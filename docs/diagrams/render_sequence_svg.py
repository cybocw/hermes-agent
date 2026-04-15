from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path
from xml.sax.saxutils import escape

TONE_STYLES = {
    "entry": {"stroke": "#2563eb", "fill": "#dbeafe"},
    "control": {"stroke": "#7c3aed", "fill": "#ede9fe"},
    "write": {"stroke": "#10b981", "fill": "#d1fae5"},
    "model": {"stroke": "#4f46e5", "fill": "#e0e7ff"},
    "tool": {"stroke": "#f97316", "fill": "#ffedd5"},
    "muted": {"stroke": "#64748b", "fill": "#f8fafc"},
}

MARGIN_X = 90
TOP_Y = 86
HEADER_H = 56
LIFELINE_TOP = 150
STEP_X = 200
ACTIVATION_W = 20
NOTE_W = 250
NOTE_PADDING = 12
FRAME_LABEL_PADDING_X = 12
FRAME_LABEL_H = 24


def tone_style(name: str) -> dict[str, str]:
    return TONE_STYLES.get(name, TONE_STYLES["muted"])


def wrap_lines(text: str, width: int) -> list[str]:
    return textwrap.wrap(text, width=width) or [text]


def svg_text(x: float, y: float, text: str, klass: str, anchor: str = "start") -> str:
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" class="{klass}">{escape(text)}</text>'


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: render_sequence_svg.py <input.json> <output.svg>")
        return 1

    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    participants = data["participants"]
    messages = data["messages"]
    frames = data.get("frames", [])
    activations = data.get("activations", [])
    notes = data.get("notes", [])

    count = len(participants)
    width = data.get("width", MARGIN_X * 2 + STEP_X * (count - 1) + 120)
    height = data.get("height", max((m["y"] for m in messages), default=700) + 120)
    subtitle = data.get("subtitle", "")

    x_map: dict[str, float] = {}
    for idx, participant in enumerate(participants):
        x_map[participant["id"]] = MARGIN_X + idx * STEP_X

    parts: list[str] = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">')
    parts.append("<defs>")
    for name, style in TONE_STYLES.items():
        parts.append(
            f'<marker id="arrow-{name}" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">'
            f'<polygon points="0 0, 10 3.5, 0 7" fill="{style["stroke"]}"/></marker>'
        )
    parts.append("</defs>")
    parts.append("<style>")
    parts.append("text { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }")
    parts.append(".title { font-size: 24px; font-weight: 700; fill: #0f172a; }")
    parts.append(".subtitle { font-size: 13px; font-weight: 500; fill: #64748b; }")
    parts.append(".participant-label { font-size: 14px; font-weight: 700; fill: #0f172a; }")
    parts.append(".participant-type { font-size: 11px; font-weight: 700; fill: #94a3b8; letter-spacing: 0.08em; }")
    parts.append(".message { font-size: 12px; font-weight: 500; fill: #334155; }")
    parts.append(".note { font-size: 12px; font-weight: 500; fill: #475569; }")
    parts.append(".frame { font-size: 12px; font-weight: 700; fill: #475569; }")
    parts.append(".lifeline { stroke: #cbd5e1; stroke-width: 1.5; stroke-dasharray: 5,4; }")
    parts.append("</style>")
    parts.append(f'<rect width="{width}" height="{height}" fill="#ffffff"/>')
    parts.append(svg_text(width / 2, 42, data["title"], "title", anchor="middle"))
    if subtitle:
        parts.append(svg_text(width / 2, 68, subtitle, "subtitle", anchor="middle"))

    for frame in frames:
        x1 = x_map[frame["from"]] - 58
        x2 = x_map[frame["to"]] + 58
        parts.append(
            f'<rect x="{x1}" y="{frame["y"]}" width="{x2 - x1}" height="{frame["height"]}" '
            'rx="12" fill="#f8fafc" stroke="#cbd5e1" stroke-dasharray="7 5"/>'
        )
        label = frame["label"]
        label_w = max(180, len(label) * 6.2 + FRAME_LABEL_PADDING_X * 2)
        label_x = x1 + 14
        label_y = frame["y"] - FRAME_LABEL_H / 2
        parts.append(
            f'<rect x="{label_x}" y="{label_y}" width="{label_w}" height="{FRAME_LABEL_H}" '
            'rx="10" fill="#ffffff" stroke="#cbd5e1"/>'
        )
        parts.append(svg_text(label_x + FRAME_LABEL_PADDING_X, label_y + 16, label, "frame"))

    for activation in activations:
        x = x_map[activation["participant"]] - ACTIVATION_W / 2
        style = tone_style(activation.get("tone", "muted"))
        parts.append(
            f'<rect x="{x}" y="{activation["y"]}" width="{ACTIVATION_W}" height="{activation["height"]}" '
            f'rx="8" fill="{style["fill"]}" stroke="{style["stroke"]}" opacity="0.95"/>'
        )

    for participant in participants:
        x = x_map[participant["id"]]
        label = participant["label"]
        box_w = max(128, len(label) * 8.2)
        box_x = x - box_w / 2
        parts.append(
            f'<rect x="{box_x}" y="{TOP_Y}" width="{box_w}" height="{HEADER_H}" rx="12" '
            'fill="#f8fafc" stroke="#cbd5e1"/>'
        )
        type_label = participant.get("type_label", "PARTICIPANT")
        parts.append(svg_text(x, TOP_Y + 18, type_label, "participant-type", anchor="middle"))
        parts.append(svg_text(x, TOP_Y + 39, label, "participant-label", anchor="middle"))
        parts.append(f'<line x1="{x}" y1="{LIFELINE_TOP}" x2="{x}" y2="{height - 48}" class="lifeline"/>')

    for message in messages:
        x1 = x_map[message["from"]]
        x2 = x_map[message["to"]]
        y = message["y"]
        style = tone_style(message.get("tone", "muted"))
        dash = ' stroke-dasharray="7 5"' if message.get("dashed") else ""
        parts.append(
            f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{style["stroke"]}" stroke-width="2.2"{dash} '
            f'marker-end="url(#arrow-{message.get("tone", "muted")})"/>'
        )
        label_x = (x1 + x2) / 2
        anchor = "middle"
        if x2 < x1:
            label_x -= 6
        parts.append(svg_text(label_x, y - 8, message["label"], "message", anchor=anchor))

    for note in notes:
        x = x_map[note["participant"]]
        lines = wrap_lines(note["text"], 34)
        note_h = 20 + len(lines) * 16 + NOTE_PADDING
        preferred_x = x + 24
        if preferred_x + NOTE_W > width - 20:
            preferred_x = x - NOTE_W - 24
        note_x = max(20, preferred_x)
        note_y = note["y"]
        parts.append(
            f'<rect x="{note_x}" y="{note_y}" width="{NOTE_W}" height="{note_h}" rx="10" '
            'fill="#fff7ed" stroke="#fdba74"/>'
        )
        ty = note_y + 24
        for line in lines:
            parts.append(svg_text(note_x + NOTE_PADDING, ty, line, "note"))
            ty += 16

    parts.append("</svg>")
    Path(sys.argv[2]).write_text("\n".join(parts) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
