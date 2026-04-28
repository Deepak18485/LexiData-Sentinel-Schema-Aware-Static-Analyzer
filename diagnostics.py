""" LexiData-Sentinel: Diagnostics Module Handles compile-time error, warning, and info messages."""

from enum import Enum
from typing import Optional


class DiagnosticLevel(Enum):
    """Severity levels for diagnostics."""
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


class Diagnostic:
    """Represents a single diagnostic message with location information."""
    
    def __init__(
        self,
        level: DiagnosticLevel,
        message: str,
        line: Optional[int] = None,
        column: Optional[int] = None
    ):
        self.level = level
        self.message = message
        self.line = line
        self.column = column
    
    def __str__(self) -> str:
        """Format diagnostic for human-readable output."""
        location = f"(line {self.line})" if self.line else ""
        return f"{self.level.value} {location}: {self.message}"
    
    def __repr__(self) -> str:
        return f"Diagnostic({self.level}, {self.message!r}, line={self.line})"


class DiagnosticCollector:
    """Collects and manages diagnostics during analysis."""
    
    def __init__(self):
        self.diagnostics: list[Diagnostic] = []
        self._error_count = 0
        self._warning_count = 0
        self._info_count = 0
    
    def error(self, message: str, line: Optional[int] = None):
        """Add an error diagnostic."""
        diag = Diagnostic(DiagnosticLevel.ERROR, message, line)
        self.diagnostics.append(diag)
        self._error_count += 1
    
    def warning(self, message: str, line: Optional[int] = None):
        """Add a warning diagnostic."""
        diag = Diagnostic(DiagnosticLevel.WARNING, message, line)
        self.diagnostics.append(diag)
        self._warning_count += 1
    
    def info(self, message: str, line: Optional[int] = None):
        """Add an info diagnostic."""
        diag = Diagnostic(DiagnosticLevel.INFO, message, line)
        self.diagnostics.append(diag)
        self._info_count += 1
    
    def has_errors(self) -> bool:
        """Check if any errors were reported."""
        return self._error_count > 0
    
    def get_summary(self) -> str:
        """Get a summary of diagnostic counts."""
        return (
            f"Analysis complete: "
            f"{self._error_count} error(s), "
            f"{self._warning_count} warning(s), "
            f"{self._info_count} info(s)"
        )
    
    def print_all(self):
        """Print all diagnostics in order."""
        for diag in self.diagnostics:
            print(diag)
        print()
        print(self.get_summary())
