def create_simple_plan(goal: str):
    return [
        {
            "title": "Understand goal",
            "description": f"Review the user goal: {goal}",
            "worker_type": "text_worker",
            "dependencies": []
        },
        {
            "title": "Create output",
            "description": "Generate the requested result.",
            "worker_type": "text_worker",
            "dependencies": ["Understand goal"]
        },
        {
            "title": "Report completion",
            "description": "Summarize the completed work for the user.",
            "worker_type": "text_worker",
            "dependencies": ["Create output"]
        }
    ]