from pathlib import Path
from typing import Iterable

from core.errors import PermissionDeniedError


class SandboxPolicy:
    """
    Safety policy for future terminal and file tools.

    This does not execute commands or access files. It defines the rules that
    future tool adapters must pass before doing risky work.
    """

    def __init__(self, workspace_root: str = "workspace"):
        self.workspace_root = Path(workspace_root).resolve()
        self.blocked_command_keywords = {
            "rm -rf",
            "format",
            "shutdown",
            "reboot",
            "mkfs",
            "del /s",
            "rmdir /s",
            "powershell -enc",
            "curl | sh",
            "wget | sh",
        }
        self.blocked_file_names = {
            ".env",
            "id_rsa",
            "id_ed25519",
            "known_hosts",
            "credentials",
        }

    def validate_command(self, command: str, approved: bool = False):
        normalized = command.strip().lower()

        if not approved:
            raise PermissionDeniedError("Terminal commands require explicit approval.")

        if not normalized:
            raise PermissionDeniedError("Empty terminal command is not allowed.")

        for keyword in self.blocked_command_keywords:
            if keyword in normalized:
                raise PermissionDeniedError(f"Blocked dangerous command pattern: {keyword}")

        return True

    def validate_file_path(self, file_path: str, approved: bool = False):
        if not approved:
            raise PermissionDeniedError("File access requires explicit approval.")

        resolved_path = Path(file_path).resolve()

        if not self._is_within_workspace(resolved_path):
            raise PermissionDeniedError("File access outside the sandbox workspace is not allowed.")

        if resolved_path.name in self.blocked_file_names:
            raise PermissionDeniedError("Access to sensitive file names is not allowed.")

        return True

    def validate_file_batch(self, file_paths: Iterable[str], approved: bool = False):
        for file_path in file_paths:
            self.validate_file_path(file_path, approved=approved)
        return True

    def _is_within_workspace(self, resolved_path: Path) -> bool:
        try:
            resolved_path.relative_to(self.workspace_root)
            return True
        except ValueError:
            return False
