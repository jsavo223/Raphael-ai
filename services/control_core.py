from services.plan_engine import create_simple_plan


class ControlCore:
    def create_mission(self, goal: str):
        plan = create_simple_plan(goal)

        return {
            "goal": goal,
            "status": "planned",
            "plan": plan
        }