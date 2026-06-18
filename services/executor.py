from workers.worker_loop import WorkerLoop


class Executor:
    def __init__(self):
        self.worker = WorkerLoop()

    def execute_plan(self, plan):
        results = []

        for task in plan:
            result = self.worker.run_task(task)
            results.append(result)

        return results