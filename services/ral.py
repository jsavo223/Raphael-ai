class RuntimeAccessLayer:
    def validate_request(self, goal: str) -> bool:
        return bool(goal and goal.strip())