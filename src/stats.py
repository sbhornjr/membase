class StatsTracker():
    def __init__(self):
        self.set_ops = 0
        self.get_ops = 0
        self.delete_ops = 0
        self.commits = 0
        self.rollbacks = 0
        self.snapshots = 0
        self.wal_size = 0

    def get_stats(self):
        return {
            "set_ops": self.set_ops,
            "get_ops": self.get_ops,
            "delete_ops": self.delete_ops,
            "commits": self.commits,
            "rollbacks": self.rollbacks,
            "snapshots": self.snapshots,
            "wal_size": self.wal_size
        }