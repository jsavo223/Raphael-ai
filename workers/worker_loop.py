class WorkerLoop:
    def run_task(self, task):
        return {
            "task": task,
            "status": "completed",
            "output": f"Completed task: {task['title']}"
        }