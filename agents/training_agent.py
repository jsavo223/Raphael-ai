from core.ids import new_id
from core.time import utc_now
from schemas.training import TrainingSuggestion


class TrainingAgent:
    """
    Controlled improvement agent.

    This agent does not rewrite production agents directly.
    It reviews missions and creates training suggestions that can be approved later.
    """

    def __init__(self, training_store):
        self.training_store = training_store

    def create_suggestion(
        self,
        title: str,
        description: str,
        target_agent: str = "general_agent",
        category: str = "capability_improvement",
        priority: str = "medium",
        source_mission_id: str = None,
        evidence=None,
    ):
        suggestion = TrainingSuggestion(
            suggestion_id=new_id("train"),
            source_mission_id=source_mission_id,
            target_agent=target_agent,
            category=category,
            priority=priority,
            title=title,
            description=description,
            evidence=evidence or [],
            status="proposed",
            created_at=utc_now().isoformat(),
        )
        return self.training_store.add(suggestion)

    def analyze_mission(self, mission, events):
        suggestions = []
        event_types = [event.event_type for event in events]
        failed_events = [event for event in events if event.event_type == "TASK_FAILED"]
        completed_events = [event for event in events if event.event_type == "TASK_COMPLETED"]
        planned_events = [event for event in events if event.event_type == "MISSION_PLANNED"]

        if failed_events:
            for event in failed_events:
                suggestions.append(
                    self.create_suggestion(
                        source_mission_id=mission.mission_id,
                        target_agent="executor_agent",
                        category="failure_repair",
                        priority="high",
                        title="Improve failed task handling",
                        description=(
                            "A task failed during mission execution. Review the error and add a repair rule, "
                            "fallback behavior, or better worker instruction before allowing similar autonomous work."
                        ),
                        evidence=[
                            f"failed_task_id={event.task_id}",
                            f"payload={event.payload}",
                        ],
                    )
                )

        if completed_events and not failed_events:
            suggestions.append(
                self.create_suggestion(
                    source_mission_id=mission.mission_id,
                    target_agent="planner_agent",
                    category="workflow_pattern",
                    priority="medium",
                    title="Capture successful mission pattern",
                    description=(
                        "This mission completed successfully. Review the task sequence and save useful planning "
                        "patterns for future app, website, or automation-building missions."
                    ),
                    evidence=[
                        f"completed_task_count={len(completed_events)}",
                        f"event_types={event_types}",
                    ],
                )
            )

        if planned_events:
            latest_plan = planned_events[-1].payload.get("plan", [])
            if latest_plan:
                suggestions.append(
                    self.create_suggestion(
                        source_mission_id=mission.mission_id,
                        target_agent="app_builder_agent",
                        category="app_building_training",
                        priority="medium",
                        title="Review plan for reusable app-building steps",
                        description=(
                            "Check whether this mission plan contains reusable steps for building apps or websites. "
                            "If useful, convert them into templates for future specialized build agents."
                        ),
                        evidence=[f"task_titles={[task.get('title') for task in latest_plan]}"],
                    )
                )

        if not suggestions:
            suggestions.append(
                self.create_suggestion(
                    source_mission_id=mission.mission_id,
                    target_agent="training_agent",
                    category="insufficient_signal",
                    priority="low",
                    title="No training signal found",
                    description=(
                        "The mission did not produce enough signal to improve an agent. Keep the record, "
                        "but do not change behavior from this mission alone."
                    ),
                    evidence=[f"event_types={event_types}"],
                )
            )

        return suggestions
