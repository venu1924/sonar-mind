"""Mind map generation and overlap-safe HTML layout."""

import html
import math

from sonar_mind.json_tools import parse_model_json
from sonar_mind.llm import generate_json
from sonar_mind import state

MINDMAP_TEMPLATE = """You are an educational assistant. Create one mind map from the transcript only.
Return valid JSON only, with this shape:
{{
  "central_topic": "Main topic in at most 4 words",
  "branches": [
    {{"title": "Short title", "description": "One sentence under 20 words"}}
  ]
}}
Use 4 to 8 branches. No nested branches. No markdown.
Transcript:
{transcript}
JSON Output:
"""

BRANCH_COLORS = ["#e8c5a0", "#d4a574", "#f5deb3", "#caa44d", "#e6c85d", "#dac78e", "#b8860b", "#daa520"]


def calculate_safe_positioning(num_branches: int):
    branch_width = 180
    min_distance = branch_width + 40
    circumference = max(num_branches, 1) * min_distance
    min_radius = circumference / (2 * math.pi)
    safe_radius = max(min_radius + 50, 200)
    container_height = max(700, int((safe_radius + 180) * 2))
    return safe_radius, container_height


def generate_mindmap_html(mindmap_data: dict) -> str:
    central_topic = html.escape(str(mindmap_data.get("central_topic") or "Mind Map"))
    branches = mindmap_data.get("branches") or []
    if not isinstance(branches, list) or not branches:
        return "<div class='mindmap-display'><p>No branches to display.</p></div>"
    radius, container_height = calculate_safe_positioning(len(branches))
    center = container_height // 2
    central_radius = 90
    parts = []
    for index, branch in enumerate(branches):
        if not isinstance(branch, dict):
            continue
        color = BRANCH_COLORS[index % len(BRANCH_COLORS)]
        angle = (2 * math.pi * index) / len(branches)
        branch_x = center + (radius * math.cos(angle))
        branch_y = center + (radius * math.sin(angle))
        connector_length = max(radius - central_radius, 40)
        rotation = math.degrees(angle)
        title = html.escape(str(branch.get("title") or "Branch"))
        description = html.escape(str(branch.get("description") or ""))
        parts.append(
            f"""
<div class="branch-container" style="position:absolute; left:{branch_x - 90:.1f}px; top:{branch_y - 40:.1f}px;">
  <div style="position:absolute; width:{connector_length:.1f}px; height:4px; background:linear-gradient(to left,#caa44d,transparent); transform-origin:right center; transform:rotate({rotation:.1f}deg); right:90px; top:40px;"></div>
  <div class="branch-box" style="background:{color}; padding:12px 16px; border-radius:12px; border:2px solid #8b7355; width:180px; min-height:70px;">
    <div style="font-weight:700; color:#2c2c2c; text-align:center;">{title}</div>
    <div style="font-size:12px; color:#444; text-align:center;">{description}</div>
  </div>
</div>
"""
        )
    return f"""
<div style="position:relative; width:100%; height:{container_height}px; background:#1a1a1a; border:2px solid #caa44d; border-radius:12px; overflow:auto;">
  <div style="position:absolute; top:{center}px; left:{center}px; transform:translate(-50%,-50%); background:linear-gradient(135deg,#ffd700,#ffed4e); color:#1a1a1a; font-weight:700; padding:20px 28px; border-radius:20px; text-align:center; max-width:180px; z-index:2;">{central_topic}</div>
  {''.join(parts)}
</div>
"""


def generate_mindmap(transcript: str):
    if not transcript or not transcript.strip():
        return "<div class='mindmap-display'><p>Provide a transcript first.</p></div>", "Add lecture text before generating a mind map."
    try:
        data = generate_json(MINDMAP_TEMPLATE, transcript)
        data = parse_model_json(data)
        if isinstance(data, list):
            raise ValueError("Mind map JSON was a list, not an object with branches.")
        branches = data.get("branches") if isinstance(data, dict) else None
        if not isinstance(branches, list) or not branches:
            raise ValueError("Mind map did not include branches.")
    except Exception as exc:
        return f"<div class='mindmap-display'><p>Mind map generation failed: {html.escape(str(exc))}</p></div>", "Error occurred during generation."
    state.mindmap_state = {"data": data, "generated": True}
    try:
        return generate_mindmap_html(data), f"Mind map generated with {len(data.get('branches', []))} branches."
    except Exception as exc:
        return f"<div class='mindmap-display'><p>{html.escape(str(exc))}</p></div>", "Error occurred during visualization."
