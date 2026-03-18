# UI CLAUDE.md — Streamlit-Specific Patterns & Gotchas

## Sidebar Render Order & Deferred Placeholders

Streamlit renders the page top-to-bottom in a single pass. The sidebar (`render_sidebar_widgets()`) renders **before** the tab content (motor selection, fan config, etc.). This means any sidebar element that reads from `quote_data` will show **stale data** from the previous render — not changes made by the current render's tabs.

**Solution — deferred placeholders:** Use `st.empty()` to reserve visual position in the sidebar during `render_sidebar_widgets()`, then fill them **after** all tabs render via `update_sidebar_deferred()`. This is called at the end of `2_Create_New_Quote.py`.

```python
# In render_sidebar_widgets():
_sidebar_summary_placeholder = st.empty()     # reserves position
_sidebar_grand_total_placeholder = st.empty()  # reserves position

# In 2_Create_New_Quote.py, AFTER all tab content renders:
update_sidebar_deferred()  # fills placeholders with current data
```

**Rule:** Any sidebar content that depends on data modified by tab rendering (motor details, component calculations, totals) **must** use a deferred placeholder — never render it inline during `render_sidebar_widgets()`.

## Widget Key Reset Pattern (`widget_reset_counter`)

All sidebar widgets use a dynamic key suffix: `key=f"widget_name_{widget_reset_counter}"`. When `widget_reset_counter` increments, Streamlit treats them as new widgets and recreates them from scratch with fresh values from `quote_data`.

**When to increment:** Adding/removing fan configs, switching active config, changing fan ID — any action that invalidates all widget values for the active config.

**Critical:** Every interactive sidebar widget must include `widget_key_suffix` in its key. A widget with a static key (e.g., `key="widget_config_selector"`) will hold stale values across resets and cause "one step behind" bugs.

```python
# Correct — resets with counter
st.selectbox("...", key=f"widget_config_selector{widget_key_suffix}", ...)

# Wrong — persists stale state across resets
st.selectbox("...", key="widget_config_selector", ...)
```

## Callback Guards — Only Act on Actual Changes

Streamlit `on_change` callbacks can fire spuriously when widget display text changes (e.g., `format_func` output updates) even though the underlying value hasn't changed. Without a guard, the callback clears widget state unnecessarily, causing the "one step behind" lag.

**Pattern:** Always check if the value actually changed before taking destructive action (clearing state, incrementing counters):

```python
def _handle_config_selector_change():
    selected_idx = ...  # parse from widget
    # Guard: no-op if index hasn't changed
    if selected_idx == st.session_state.get("active_config_index", 0):
        return
    # Only now clear state and switch config
    _clear_widget_state()
    st.session_state.widget_reset_counter += 1
```

## Selectbox `format_func` Limitations

Streamlit caches selectbox display text by widget key + underlying value. If the `format_func` includes data that changes independently (e.g., quantity), the displayed text goes stale when that data changes but the selected option doesn't.

**Rule:** Only include **stable** data in `format_func` output — data that only changes when the selection itself changes. Show volatile data (quantity, prices) in a separate deferred element instead.

```python
# Correct — fan UID only changes when config changes
format_func=lambda idx: f"Config {idx + 1}: {fan_uid}"

# Wrong — quantity changes independently, display goes stale
format_func=lambda idx: f"Config {idx + 1}: {fan_uid} (×{qty})"
```

## Selectbox Value Type Safety

When using `format_func` with integer option values, Streamlit may return the formatted string instead of the integer on stale reruns or session deserialization. Always parse defensively:

```python
raw_value = st.session_state[widget_key]
if isinstance(raw_value, int):
    selected_idx = raw_value
elif isinstance(raw_value, str):
    m = re.match(r"Config\s+(\d+)", raw_value)
    selected_idx = int(m.group(1)) - 1 if m else fallback_idx
```
