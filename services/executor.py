from workers.worker_loop import WorkerLoop


class Executor:
    def __init__(self):
        self.worker = WorkerLoop()

    def execute_plan(
        self,
        plan,
        mission_id=None,
        correlation_id=None,
        event_callback=None,
    ):
        results = []

        for task in plan:
            task_id = task.get("task_id")
            task["status"] = "running"

            if event_callback:
                event_callback(
                    event_type="TASK_STARTED",
                    mission_id=mission_id,
                    correlation_id=correlation_id,
                    task_id=task_id,
                    payload={
                        "title": task.get("title"),
                        "worker_type": task.get("worker_type"),
                    },
                )

            try:
                result = self.worker.run_task(task)
                task["status"] = result.get("status", "completed")
                task["output"] = result.get("output")

                if event_callback:
                    event_callback(
                        event_type="TASK_COMPLETED",
                        mission_id=mission_id,
                        correlation_id=correlation_id,
                        task_id=task_id,
                        payload={
                            "title": task.get("title"),
                            "status": task.get("status"),
                            "output": task.get("output"),
                        },
                    )

                results.append(result)

            except Exception as error:
                task["status"] = "failed"
                task["error"] = str(error)

                failure = {
                    "task": task,
                    "status": "failed",
                    "error": str(error),
                }

                if event_callback:
                    event_callback(
                        event_type="TASK_FAILED",
                        mission_id=mission_id,
                        correlation_id=correlation_id,
                        task_id=task_id,
                        payload={
                            "title": task.get("title"),
                            "error": str(error),
                        },
                    )

                results.append(failure)
                break

        return results
