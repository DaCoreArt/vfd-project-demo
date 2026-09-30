"""Generate widgets/deliverables/<task-id>.html from shell + configs."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHELL = (ROOT / "widgets" / "deliverables" / "_shell.html").read_text(encoding="utf-8")
OUT_DIR = ROOT / "widgets" / "deliverables"

CONFIGS = [
    {
        "taskId": "D1.1",
        "file": "d1-1.html",
        "title": "Task D1.1 — Construct a Six-Year Dataset and Firehouse Identification",
        "intro": "Document your dataset construction, data extraction, and initial financial story.",
        "sections": [
            {
                "id": "dataset-steps",
                "label": "Dataset construction steps",
                "hint": "Identify NYC VFDs, locate tax returns, list entity names and available years.",
                "rows": 6,
            },
            {
                "id": "financial-extract",
                "label": "Financial data extracted",
                "hint": "Summarize the selected financial fields and years you captured.",
                "rows": 6,
            },
            {
                "id": "initial-story",
                "label": "Initial financial story",
                "hint": "What is the initial financial story about the state of volunteer departments in NYC?",
                "rows": 6,
            },
            {
                "id": "financial-aspects",
                "label": "Financial aspects observed",
                "hint": "What you did — walking through the space, watching processes, interacting with people (if applicable at this stage).",
                "rows": 5,
            },
            {
                "id": "sensory",
                "label": "Sensory observations",
                "hint": "Sounds, smells, movement, pace, atmosphere.",
                "rows": 5,
            },
        ],
    },
    {
        "taskId": "D1.2",
        "file": "d1-2.html",
        "title": "Task D1.2 — Firehouse Identification",
        "intro": "Identify a primary target firehouse plus two alternates.",
        "sections": [
            {
                "id": "primary",
                "label": "Primary firehouse",
                "hint": "Name, address, and description of the picture/source for the primary firehouse.",
                "rows": 5,
            },
            {
                "id": "selection-rationale",
                "label": "Selection rationale",
                "hint": "Describe how and why the primary firehouse was selected.",
                "rows": 6,
            },
            {
                "id": "alternates",
                "label": "Two alternate firehouses",
                "hint": "Names, addresses, and brief notes for each alternate.",
                "rows": 6,
            },
        ],
    },
    {
        "taskId": "D1.3",
        "file": "d1-3.html",
        "title": "Task D1.3 — Reflection (Self-Assessment)",
        "intro": "One well-developed paragraph addressing the prompts below.",
        "sections": [
            {
                "id": "framework",
                "label": "Framework from tax returns and other resources",
                "hint": "How the data gave you a framework to understand nonprofit accounting and financial data.",
                "rows": 6,
            },
            {
                "id": "competencies",
                "label": "Employer-desired competencies",
                "hint": "How this process strengthened at least three employer-desired competencies.",
                "rows": 6,
            },
        ],
    },
    {
        "taskId": "D1.4",
        "file": "d1-4.html",
        "title": "Task D1.4 — References (APA 7th Edition)",
        "intro": "Compile your references for Deliverable One. Use the References field below; add notes on source evaluation if needed.",
        "sections": [
            {
                "id": "source-notes",
                "label": "Source evaluation notes",
                "hint": "Note any AI tools used as research aids, interviews, and why aggregator sites were avoided.",
                "rows": 5,
            },
        ],
    },
    {
        "taskId": "D2.1",
        "file": "d2-1.html",
        "title": "Task D2.1 — Review and Analyze Financial Statements",
        "intro": "Calculate and interpret key financial metrics for all available years.",
        "sections": [
            {
                "id": "metrics-table",
                "label": "Key metrics by year",
                "hint": "Operating Surplus/Deficit, Operating Margin, Reserve Ratio, Liability Burden, Donation Dependence.",
                "rows": 8,
            },
            {
                "id": "analysis",
                "label": "Analysis and interpretation",
                "hint": "What do the metrics suggest about financial health and sustainability?",
                "rows": 7,
            },
            {
                "id": "whatif-notes",
                "label": "What-if insights",
                "hint": "Optional: insights from the surplus/deficit what-if tool on this page.",
                "rows": 5,
            },
        ],
    },
    {
        "taskId": "D2.2",
        "file": "d2-2.html",
        "title": "Task D2.2 — Firehouse Visitation",
        "intro": "Document your field visit (or approved virtual option).",
        "sections": [
            {
                "id": "visit-logistics",
                "label": "Visit logistics",
                "hint": "Date, location, in-person or virtual option used, who you spoke with (if any).",
                "rows": 4,
            },
            {
                "id": "equipment",
                "label": "Equipment needing replacement",
                "hint": "Fire trucks, drones, ambulances, etc.",
                "rows": 5,
            },
            {
                "id": "infrastructure",
                "label": "Construction or infrastructure needs",
                "rows": 5,
            },
            {
                "id": "funding",
                "label": "Funding sources discussed",
                "hint": "Donations, grants, and other sources for volunteer firehouses.",
                "rows": 5,
            },
            {
                "id": "recruitment",
                "label": "Recruitment and training needs",
                "rows": 5,
            },
            {
                "id": "sensory-ops",
                "label": "Operational and sensory connections",
                "hint": "How the physical realities of work shape labor costs, productivity, and staffing decisions.",
                "rows": 6,
            },
        ],
    },
    {
        "taskId": "D2.3",
        "file": "d2-3.html",
        "title": "Task D2.3 — Reflection",
        "intro": "In two to three paragraphs, describe how skills and competencies were strengthened.",
        "sections": [
            {
                "id": "reflection",
                "label": "Reflection",
                "hint": "Financial reasoning, problem-solving, curiosity, adaptability, critical thinking, empathy, emotional intelligence, and communication.",
                "rows": 10,
            },
        ],
    },
    {
        "taskId": "D2.4",
        "file": "d2-4.html",
        "title": "Task D2.4 — References (APA 7th Edition)",
        "intro": "Compile references for Deliverable Two.",
        "sections": [
            {
                "id": "source-notes",
                "label": "Source evaluation notes",
                "rows": 5,
            },
        ],
    },
    {
        "taskId": "D3.1",
        "file": "d3-1.html",
        "title": "Task D3.1 — Funding Requests",
        "intro": "Prepare a financial concerns report under four funding scenarios for a chosen investment.",
        "sections": [
            {
                "id": "investment",
                "label": "Chosen investment",
                "hint": "Equipment, apparatus, marketing, training, or recruitment campaign — and estimated cost if known.",
                "rows": 5,
            },
            {
                "id": "community",
                "label": "Scenario 1 — Community funding",
                "hint": "Membership and small donations. Raise financial concerns only.",
                "rows": 6,
            },
            {
                "id": "grant",
                "label": "Scenario 2 — Full grant funding",
                "rows": 6,
            },
            {
                "id": "short-loan",
                "label": "Scenario 3 — Short-term bank loan",
                "hint": "Bridge financing reimbursed later by a grant maker.",
                "rows": 6,
            },
            {
                "id": "long-loan",
                "label": "Scenario 4 — Long-term bank loan",
                "rows": 6,
            },
            {
                "id": "testimony",
                "label": "Legislative testimony summary",
                "hint": "Concise statement you would make before the New York State legislature.",
                "rows": 6,
            },
        ],
    },
    {
        "taskId": "D3.2",
        "file": "d3-2.html",
        "title": "Task D3.2 — Reflection",
        "intro": "Reflect on modeling and evaluating capital investment decisions.",
        "sections": [
            {
                "id": "reflection",
                "label": "Reflection",
                "hint": "Financial reasoning, problem-solving, curiosity, adaptability, critical thinking, empathy, emotional intelligence, and communication.",
                "rows": 10,
            },
        ],
    },
    {
        "taskId": "D3.3",
        "file": "d3-3.html",
        "title": "Task D3.3 — References (APA 7th Edition)",
        "intro": "Compile references for Deliverable Three.",
        "sections": [
            {
                "id": "source-notes",
                "label": "Source evaluation notes",
                "rows": 5,
            },
        ],
    },
    {
        "taskId": "D4.1",
        "file": "d4-1.html",
        "title": "Task D4.1 — Presentation Storyboard and Talking Points",
        "intro": "Deliverable Four is submitted as a narrated PowerPoint. Use this form for your storyboard, talking points, and references before recording.",
        "sections": [
            {
                "id": "storyboard",
                "label": "Storyboard / slide outline",
                "hint": "Outline or empty slide sequence populated with ideas from Deliverables One through Three.",
                "rows": 10,
            },
            {
                "id": "narration",
                "label": "Narration talking points",
                "hint": "Keep the full presentation to five minutes or less.",
                "rows": 8,
            },
            {
                "id": "rehearsal",
                "label": "Rehearsal notes",
                "hint": "Timing, clarity, accessibility accommodations if applicable.",
                "rows": 4,
            },
        ],
    },
    {
        "taskId": "D5.1",
        "file": "d5-1.html",
        "title": "Task D5.1 — Written Reflection",
        "intro": "Combine reflections from Deliverables One through Four into a flowing business story. Brightspace requires a Word file for this deliverable.",
        "sections": [
            {
                "id": "sensory",
                "label": "Firehouse setting and sensory perceptions",
                "hint": "How the setting engaged sensory perceptions and why that mattered for learning.",
                "rows": 7,
            },
            {
                "id": "theories",
                "label": "Theories and nonprofit financial management",
                "hint": "How theories studied helped explain nonprofit accounting and financial management.",
                "rows": 7,
            },
            {
                "id": "competencies",
                "label": "Employer-desired competencies",
                "hint": "Strengthened, weakened, or unchanged — with specific examples, framed for a prospective employer.",
                "rows": 8,
            },
            {
                "id": "integrated-story",
                "label": "Integrated business story",
                "hint": "Concrete experiences, abstract theories, and the D1→D5 progression.",
                "rows": 8,
            },
        ],
    },
    {
        "taskId": "D5.2",
        "file": "d5-2.html",
        "title": "Task D5.2 — Oral Reflection (VoiceThread) Planning",
        "intro": "Plan your two-to-three-minute VoiceThread. Export can help you rehearse; the oral component is submitted in VoiceThread.",
        "sections": [
            {
                "id": "interview-answer",
                "label": "Interview-style answer script",
                "hint": "What experience best prepared you to add value to this organization?",
                "rows": 8,
            },
            {
                "id": "competency-links",
                "label": "Competency links to financial and strategic decisions",
                "rows": 6,
            },
            {
                "id": "delivery",
                "label": "Delivery checklist",
                "hint": "Concise, rehearsed, energy and conviction.",
                "rows": 4,
            },
        ],
    },
]


def render(config: dict) -> str:
    cfg_json = json.dumps(
        {
            "taskId": config["taskId"],
            "title": config["title"],
            "intro": config.get("intro", ""),
            "sections": config["sections"],
        },
        indent=2,
    )
    block = f"""<script>
window.DELIVERABLE_CONFIG = {cfg_json};
</script>
<script src="form-runtime.js"></script>
"""
    if "<!-- CONFIG_AND_RUNTIME -->" not in SHELL:
        raise SystemExit("Shell missing CONFIG_AND_RUNTIME marker")
    html = SHELL.replace("<!-- CONFIG_AND_RUNTIME -->", block)
    html = html.replace("<title>Deliverable form</title>", f"<title>{config['title']}</title>")
    return html


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for config in CONFIGS:
        path = OUT_DIR / config["file"]
        path.write_text(render(config), encoding="utf-8")
        print(f"Wrote {path.relative_to(ROOT)}")
    print(f"Generated {len(CONFIGS)} deliverable forms.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
