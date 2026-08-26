# NYC Volunteer Fire Department Project — Jupyter Book 2

## What this is

Dr. Joseph Foy's NYC Volunteer Fire Department Project — the Signature Term Experiential Learning Project for MGMT 603 (Nonprofit Accounting and Financial Management) — restructured from its original PDF step-by-step guide into a working Jupyter Book 2 project.

This is the first real (non-placeholder) content run through the platform's ingestion pipeline: source document → structured Markdown → built, browsable Jupyter Book.

## Contents

| File / Folder | Contents |
|---|---|
| `myst.yml` | Project configuration, metadata, and table of contents |
| `index.md` | Landing page and book overview |
| `chapters/01-introduction.md` | NYC volunteer fire department background and project rationale |
| `chapters/02-project-overview-and-objectives.md` | Purpose, learning objectives, deliverables summary, employer-desired competencies |
| `chapters/03-deliverable-one.md` | Financial Data Gathering and Firehouse Identification |
| `chapters/04-deliverable-two.md` | Firehouse Visitation and Financial Analysis |
| `chapters/05-deliverable-three.md` | Funding Scenarios Simulation Evaluation |
| `chapters/06-deliverable-four.md` | Communicating Results (presentation) |
| `chapters/07-deliverable-five.md` | Reflection (written + oral) |
| `chapters/08-rubrics.md` | Grading rubrics for all five deliverables |
| `chapters/09-appendix-and-references.md` | Confidentiality statement, citation guidance, references |
| `chapters/10-media-gallery.md` | Video and visual reference gallery |
| `assets/` | Figures, photos, interactive HTML, and data files (see `assets/README.md`) |
| `project-template/` | Starting point for new projects — copy this folder to begin a new Jupyter Book |

## Source and attribution

Original content: *The NYC Volunteer Fire Department Project for MGMT 603 Nonprofit Accounting and Financial Management — A Step-by-Step Guide* (rev. 3/26/26), authored by Dr. Joseph Foy, CPA (joseph.foy@cuny.edu). Restructured into MyST Markdown / Jupyter Book 2 format as a platform pipeline demonstration.

## Preview locally

```bash
pip install jupyter-book

cd vfd-project

jupyter book build --html

jupyter book start
```

## Status

Structural conversion complete and validated (builds with zero content errors). This is the primary demo repo for showing the platform pipeline using real course material, rather than placeholder or third-party test content.
