class ChatService:
    """
    Simple user-facing wrapper around Raphael missions.

    This lets the app talk to Raphael with one plain message instead of exposing
    mission internals to the user interface.
    """

    def __init__(self, control_core):
        self.control_core = control_core

    def handle_message(self, message: str):
        mission_result = self.control_core.create_mission(message)
        mission_id = mission_result["mission_id"]
        progress = self.control_core.get_mission_progress(mission_id)

        return {
            "reply": self._build_reply(mission_result, progress),
            "mission_id": mission_id,
            "status": mission_result["status"],
            "progress": progress,
            "next_action": self._next_action(mission_result["status"]),
        }

    def _build_reply(self, mission_result, progress):
        status = mission_result["status"]
        goal = mission_result["goal"]
        percentage = progress.get("progress_percentage", 0) if progress else 0

        if status == "completed":
            return (
                "I handled that as a Raphael mission and completed the first pass. "
                f"Progress is {percentage}%. Goal: {goal}"
            )

        if status == "failed":
            return (
                "I tried to handle that, but the mission failed. "
                "Check the mission events so Raphael can repair the issue safely."
            )

        return (
            "I started that as a Raphael mission. "
            f"Current progress is {percentage}%."
        )

    def _next_action(self, status: str):
        if status == "completed":
            return "review_result"
        if status == "failed":
            return "review_events_and_repair"
        return "wait_for_progress"
