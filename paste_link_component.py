from pathlib import Path

import streamlit.components.v1 as components


_paste_component = components.declare_component(
    "webdownloaddede_paste_link",
    path=str(Path(__file__).resolve().parent / "paste_link_component"),
)


def paste_link_button(label: str = "Tempel", key: str | None = None):
    """Render a browser-side clipboard button and return its latest event."""
    return _paste_component(label=label, key=key, default=None)
