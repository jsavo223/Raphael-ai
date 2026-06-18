from dataclasses import dataclass
from typing import Dict, Optional

from core.errors import PermissionDeniedError


@dataclass(frozen=True)
class ToolPermission:
    name: str
    category: str
    enabled: bool
    approval_required: bool
    risk_level: str
    description: str


class ToolRegistry:
    """
    Central permission registry for future Raphael tools.

    Workers should never call external tools directly. They must ask the control
    layer to verify tool permission here first.
    """

    def __init__(self):
        self._tools: Dict[str, ToolPermission] = {}
        self._register_defaults()

    def _register_defaults(self):
        self.register(
            ToolPermission(
                name="web_search",
                category="internet",
                enabled=False,
                approval_required=True,
                risk_level="high",
                description="Searches the public web. Disabled until prompt-injection defenses exist.",
            )
        )
        self.register(
            ToolPermission(
                name="file_read",
                category="files",
                enabled=False,
                approval_required=True,
                risk_level="high",
                description="Reads local or uploaded files. Disabled until file sandboxing exists.",
            )
        )
        self.register(
            ToolPermission(
                name="file_write",
                category="files",
                enabled=False,
                approval_required=True,
                risk_level="critical",
                description="Writes files. Requires sandboxing and explicit approval.",
            )
        )
        self.register(
            ToolPermission(
                name="terminal_command",
                category="terminal",
                enabled=False,
                approval_required=True,
                risk_level="critical",
                description="Runs terminal commands. Disabled until command sandboxing exists.",
            )
        )
        self.register(
            ToolPermission(
                name="email_send",
                category="communication",
                enabled=False,
                approval_required=True,
                risk_level="critical",
                description="Sends email. Requires explicit user approval per send.",
            )
        )
        self.register(
            ToolPermission(
                name="calendar_write",
                category="calendar",
                enabled=False,
                approval_required=True,
                risk_level="high",
                description="Creates or updates calendar events. Requires explicit approval.",
            )
        )
        self.register(
            ToolPermission(
                name="deploy_app",
                category="deployment",
                enabled=False,
                approval_required=True,
                risk_level="critical",
                description="Deploys an application. Requires tests, approval, and rollback plan.",
            )
        )

    def register(self, permission: ToolPermission):
        self._tools[permission.name] = permission

    def get(self, tool_name: str) -> Optional[ToolPermission]:
        return self._tools.get(tool_name)

    def list_tools(self):
        return list(self._tools.values())

    def require_allowed(self, tool_name: str, approved: bool = False) -> ToolPermission:
        permission = self.get(tool_name)

        if permission is None:
            raise PermissionDeniedError(f"Unknown tool: {tool_name}")

        if not permission.enabled:
            raise PermissionDeniedError(f"Tool is disabled: {tool_name}")

        if permission.approval_required and not approved:
            raise PermissionDeniedError(f"Tool requires approval: {tool_name}")

        return permission
