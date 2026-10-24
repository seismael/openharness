"""Exit codes and the one error type every command shares."""

from __future__ import annotations

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_USAGE = 2
EXIT_ASK = 3


class OpenHarnessError(Exception):
    """An input problem that prevents an operation from producing a verdict."""

    def __init__(self, message: str, exit_code: int = EXIT_USAGE) -> None:
        super().__init__(message)
        self.message = message
        self.exit_code = exit_code


class DeclarationError(OpenHarnessError):
    """A declaration document does not satisfy its contract."""
