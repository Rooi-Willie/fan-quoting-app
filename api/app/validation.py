"""Quote data schema validation utilities (Stage 5).

Produces structured error lists without raising immediately so callers can
aggregate or transform into HTTP 422 responses.
"""
from __future__ import annotations

from typing import Dict, Any, List


class ValidationIssue(dict):
    """Lightweight issue structure (path, code, message)."""

    @classmethod
    def make(cls, path: str, code: str, message: str) -> "ValidationIssue":
        return cls(path=path, code=code, message=message)


def validate_quote_data(qd: Dict[str, Any]) -> List[ValidationIssue]:
    """Validation for quote_data structure."""
    issues: List[ValidationIssue] = []
    if not isinstance(qd, dict):
        issues.append(ValidationIssue.make(path="/", code="not_object", message="quote_data root must be an object"))
        return issues

    # Check main sections exist
    required_sections = ["meta", "quote", "specification", "pricing", "calculations"]
    for section in required_sections:
        if section not in qd:
            # Don't fail on missing context - it's often populated later
            if section != "context":
                issues.append(ValidationIssue.make(f"/{section}", "missing", f"Required section '{section}' is missing"))
        elif not isinstance(qd[section], dict):
            issues.append(ValidationIssue.make(f"/{section}", "type", f"Section '{section}' must be an object"))

    # Validate specification section
    spec = qd.get("specification", {})
    if isinstance(spec, dict):
        # Check components list
        components = spec.get("components", [])
        if not isinstance(components, list):
            issues.append(ValidationIssue.make("/specification/components", "type", "components must be list"))
        else:
            for idx, comp in enumerate(components):
                if not isinstance(comp, dict):
                    issues.append(ValidationIssue.make(f"/specification/components/{idx}", "type", "component must be object"))
                elif "id" not in comp:
                    issues.append(ValidationIssue.make(f"/specification/components/{idx}/id", "missing", "id is required"))

    return issues


def _is_number(v: Any) -> bool:
    try:
        float(v)
        return True
    except Exception:
        return False
