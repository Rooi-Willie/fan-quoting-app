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
    issues: List[ValidationIssue] = []
    if not isinstance(qd, dict):
        issues.append(ValidationIssue.make(path="/", code="not_object", message="quote_data root must be an object"))
        return issues

    # Fan node basic checks (fan.uid optional for drafts but if present must be str)
    fan = qd.get("fan", {}) or {}
    if fan and not isinstance(fan, dict):
        issues.append(ValidationIssue.make("/fan", "type", "fan must be object"))
    else:
        uid = fan.get("uid")
        if uid is not None and not isinstance(uid, str):
            issues.append(ValidationIssue.make("/fan/uid", "type", "uid must be string"))

    # Components selection integrity
    comps = qd.get("components", {}) or {}
    if comps and not isinstance(comps, dict):
        issues.append(ValidationIssue.make("/components", "type", "components must be object"))
    else:
        selected = comps.get("selected") or []
        if not isinstance(selected, list):
            issues.append(ValidationIssue.make("/components/selected", "type", "selected must be list"))
            selected = []
        by_name = comps.get("by_name") or {}
        if by_name and not isinstance(by_name, dict):
            issues.append(ValidationIssue.make("/components/by_name", "type", "by_name must be object"))
            by_name = {}
        # Each selected exists
        for idx, name in enumerate(selected):
            if name not in by_name:
                issues.append(ValidationIssue.make(f"/components/selected/{idx}", "missing_component_def", f"component '{name}' not present under by_name"))
        # Each selected has calculated total if calculated exists
        for cname, node in by_name.items():
            if not isinstance(node, dict):
                issues.append(ValidationIssue.make(f"/components/by_name/{cname}", "type", "component entry must be object"))
                continue
            calc = node.get("calculated") or {}
            if calc and not isinstance(calc, dict):
                issues.append(ValidationIssue.make(f"/components/by_name/{cname}/calculated", "type", "calculated must be object"))
                continue
            if cname in selected:
                val = calc.get("total_cost_after_markup") if isinstance(calc, dict) else None
                if val is not None and not _is_number(val):
                    issues.append(ValidationIssue.make(f"/components/by_name/{cname}/calculated/total_cost_after_markup", "type", "must be numeric"))

    # Motor pricing consistency
    motor = qd.get("motor", {}) or {}
    if motor and not isinstance(motor, dict):
        issues.append(ValidationIssue.make("/motor", "type", "motor must be object"))
    else:
        selection = motor.get("selection") or {}
        if selection and not isinstance(selection, dict):
            issues.append(ValidationIssue.make("/motor/selection", "type", "selection must be object"))
        final_price = motor.get("final_price")
        if final_price is not None and not _is_number(final_price):
            issues.append(ValidationIssue.make("/motor/final_price", "type", "final_price must be numeric"))

    # Buy-out items
    buyouts = qd.get("buy_out_items") or []
    if buyouts and not isinstance(buyouts, list):
        issues.append(ValidationIssue.make("/buy_out_items", "type", "buy_out_items must be list"))
        buyouts = []
    for i, item in enumerate(buyouts):
        if not isinstance(item, dict):
            issues.append(ValidationIssue.make(f"/buy_out_items/{i}", "type", "item must be object"))
            continue
        sub = item.get("subtotal")
        if sub is not None and not _is_number(sub):
            issues.append(ValidationIssue.make(f"/buy_out_items/{i}/subtotal", "type", "subtotal must be numeric"))

    # Derived totals integrity (if present)
    calc = qd.get("calculation", {}) or {}
    if calc and not isinstance(calc, dict):
        issues.append(ValidationIssue.make("/calculation", "type", "calculation must be object"))
    else:
        dt = calc.get("derived_totals") or {}
        if dt and not isinstance(dt, dict):
            issues.append(ValidationIssue.make("/calculation/derived_totals", "type", "derived_totals must be object"))
        else:
            if isinstance(dt, dict):
                parts = [dt.get("components_final_price"), dt.get("motor_final_price"), dt.get("buyout_total")]
                if any(v is not None and not _is_number(v) for v in parts):
                    issues.append(ValidationIssue.make("/calculation/derived_totals", "type", "component, motor, buyout totals must be numeric"))
                grand = dt.get("grand_total")
                if grand is not None and all(_is_number(v) for v in parts if v is not None):
                    comp_val = float(parts[0] or 0)
                    motor_val = float(parts[1] or 0)
                    buy_val = float(parts[2] or 0)
                    expected = comp_val + motor_val + buy_val
                    if _is_number(grand) and abs(float(grand) - expected) > 0.01:
                        issues.append(ValidationIssue.make("/calculation/derived_totals/grand_total", "sum_mismatch", f"grand_total {grand} != sum({expected})"))

    return issues


def _is_number(v: Any) -> bool:
    try:
        float(v)
        return True
    except Exception:
        return False
