"""Shared helper for safely passing raw HTML through st.markdown(unsafe_allow_html=True).

`unsafe_allow_html=True` only stops Streamlit's Markdown renderer from
escaping HTML tags — it does NOT disable the rest of CommonMark parsing.
Any line indented 4+ spaces is still treated as a literal indented code
block per the CommonMark spec, and Python multi-line f-strings written with
normal source-code indentation (nested divs indented 8-10 spaces to match
the surrounding code) trip this rule constantly: the first line or two
render fine, then the parser flips into "code block" mode and the rest of
the markup is dumped to the page as literal text instead of being rendered.

Flattening to a single line sidesteps this entirely and is always safe for
HTML, since HTML rendering itself is whitespace-insensitive in normal flow
content (browsers collapse whitespace runs regardless).
"""

from __future__ import annotations

import re


def flatten(html: str) -> str:
    """Collapse a (possibly indented, multi-line) HTML string to one line."""
    return re.sub(r"\s+", " ", html).strip()
