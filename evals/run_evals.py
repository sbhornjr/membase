from tools import TOOLS, execute_tool, grade
import yaml
import json
import anthropic
import asyncio
from pathlib import Path
from datetime import datetime, timezone

client = anthropic.AsyncAnthropic()
evals_path = Path("evals/cases")

async def run_agent(prompt: str, max_turns: int = 10) -> list:
    messages = [{"role": "user", "content": prompt}]
    tool_call_log = []

    for turn in range(max_turns):
        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            tools=TOOLS,
            messages=messages
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            break

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"  → Tool call: {block.name}({block.input})")
                result = await execute_tool(block.name, block.input)
                print(f"  ← Result: {result}")
                tool_call_log.append({
                    "tool": block.name,
                    "input": block.input,
                    "result": result
                })
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result)
                })
        
        if not tool_results:
            break

        messages.append({"role": "user", "content": tool_results})

    return tool_call_log


async def run_eval(eval_file: str):
    with open(eval_file) as f:
        eval = yaml.safe_load(f)

    clear = await execute_tool("clear_namespace", {"namespace": eval["name"]})
    if (not clear.get("ok")):
        print("ERROR CLEARING DATABASE BEFORE EVAL. ABORTING EVALS.")
        raise RuntimeError("ERROR CLEARING DATABASE BEFORE EVAL. ABORTING EVALS.")
    
    if eval.get("setup", None):
        for cmd in eval["setup"]:
            await execute_tool("set_key", cmd)

    print(f"\n{'='*50}")
    print(f"Eval: {eval['name']}")
    print(f"Prompt: {eval['prompt']}")
    print(f"{'='*50}")

    tool_call_log = await run_agent(eval["prompt"])
    grade_results = await grade(eval["expected_state"])

    passed = all(r["passed"] for r in grade_results.values())
    print(f"\nResult: {'PASS ✓' if passed else 'FAIL ✗'}")
    for key, result in grade_results.items():
        status = "✓" if result["passed"] else "✗"
        print(f"  {status} {key}: expected={result['expected']}, actual={result['actual']}")

    return {"eval": eval["name"], "passed": passed, "grades": grade_results, "tool_calls": tool_call_log}

async def run_all_evals(eval_dir: str, report_dir: str = "reports"):
    eval_files = sorted(Path(eval_dir).glob("*.yaml"))

    results = await asyncio.gather(*(run_eval(str(f)) for f in eval_files))

    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": passed / total if total else 0,
        "results": results
    }

    # Write JSON report
    Path(report_dir).mkdir(exist_ok=True)
    timestamp_slug = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    report_path = Path(report_dir) / f"eval_report_{timestamp_slug}.json"
    report_path.write_text(json.dumps(report, indent=2))

    # Print human-readable summary
    print(f"\n{'='*50}")
    print(f"EVAL SUMMARY: {passed}/{total} passed ({report['pass_rate']:.0%})")
    print(f"{'='*50}")
    for r in results:
        status = "PASS ✓" if r["passed"] else "FAIL ✗"
        print(f"  {status}  {r['eval']}")
        if not r["passed"]:
            for key, grade in r["grades"].items():
                if not grade["passed"]:
                    print(f"           ↳ {key}: expected={grade['expected']!r}, actual={grade['actual']!r}")
                    print(f"            Tool Call Log: {r["tool_calls"]}")

    print(f"\nFull report: {report_path}")

    return report

if __name__ == "__main__":
    asyncio.run(run_all_evals(evals_path))
