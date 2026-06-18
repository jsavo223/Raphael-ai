from services.plan_engine import create_simple_plan
from services.executor import Executor


class ControlCore:
    def __init__(self):
        self.executor = Executor()

    def create_mission(self, goal: str):
        plan = create_simple_plan(goal)

        results = self.executor.execute_plan(plan)

        return {
            "goal": goal,
            "status": "completed",
            "plan": plan,
            "results": results
        }