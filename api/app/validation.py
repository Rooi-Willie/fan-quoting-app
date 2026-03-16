"""Quote data schema validation utilities (v4 multi-fan-configuration).

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
    """Validation for v4 quote_data structure."""
    issues: List[ValidationIssue] = []
    if not isinstance(qd, dict):
        issues.append(ValidationIssue.make(path="/", code="not_object", message="quote_data root must be an object"))
        return issues

    # Check top-level sections
    for section in ["meta", "quote"]:
        if section not in qd:
            issues.append(ValidationIssue.make(f"/{section}", "missing", f"Required section '{section}' is missing"))
        elif not isinstance(qd[section], dict):
            issues.append(ValidationIssue.make(f"/{section}", "type", f"Section '{section}' must be an object"))

    # Validate fan_configurations array
    fan_configs = qd.get("fan_configurations")
    if fan_configs is None:
        issues.append(ValidationIssue.make("/fan_configurations", "missing", "Required section 'fan_configurations' is missing"))
        return issues
    if not isinstance(fan_configs, list):
        issues.append(ValidationIssue.make("/fan_configurations", "type", "fan_configurations must be a list"))
        return issues
    if len(fan_configs) == 0:
        issues.append(ValidationIssue.make("/fan_configurations", "empty", "fan_configurations must contain at least one entry"))
        return issues

    # Validate each fan configuration entry
    for idx, cfg in enumerate(fan_configs):
        prefix = f"/fan_configurations/{idx}"
        if not isinstance(cfg, dict):
            issues.append(ValidationIssue.make(prefix, "type", "fan configuration entry must be an object"))
            continue

        # Validate quantity
        qty = cfg.get("quantity", 1)
        if not isinstance(qty, (int, float)) or qty < 1:
            issues.append(ValidationIssue.make(f"{prefix}/quantity", "invalid", "quantity must be >= 1"))

        # Validate specification section
        spec = cfg.get("specification")
        if spec is not None and isinstance(spec, dict):
            components = spec.get("components", [])
            if not isinstance(components, list):
                issues.append(ValidationIssue.make(f"{prefix}/specification/components", "type", "components must be list"))
            else:
                for cidx, comp in enumerate(components):
                    if not isinstance(comp, dict):
                        issues.append(ValidationIssue.make(f"{prefix}/specification/components/{cidx}", "type", "component must be object"))
                    elif "id" not in comp:
                        issues.append(ValidationIssue.make(f"{prefix}/specification/components/{cidx}/id", "missing", "id is required"))

    return issues


def _is_number(v: Any) -> bool:
    try:
        float(v)
        return True
    except Exception:
        return False
