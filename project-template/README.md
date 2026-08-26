# Project Template — CUNY Experiential Learning Repository

Starting point for adding a project to the repository. Copy this folder,
rename it, and work through the checklist below.

Everything here follows the house conventions, so a project built from
this template will look and behave consistently with every other project
in the repository.

## What's here

```
myst.yml          Project configuration — edit every REPLACE value
index.md          Landing page
references.bib    Bibliography (BibTeX) — required for citations
chapters/         One Markdown file per section, numbered
assets/           All images, charts, photos, data, interactive files
  ├── figures/
  ├── photos/
  ├── data/
  └── interactive/
```

`assets/README.md` documents naming and directive conventions in detail.

## Setup checklist

1. **Copy and rename** this folder to your project name.
2. **Fill in `myst.yml`** — replace every value marked `REPLACE`. Leave
   the `site:` block alone; it is what keeps the look consistent.
3. **Write `index.md`** — a short landing page and a map of the chapters.
4. **Add chapters** to `chapters/`, numbered (`01-`, `02-`), and list
   each in the `toc:` block of `myst.yml`.
5. **Add sources** to `references.bib` and cite them inline with
   `[@citekey]`.
6. **Build and check:** `jupyter book build --html`
7. **Preview live:** `jupyter book start`

## House conventions

**Cross-references** use Markdown link syntax, not the deprecated `{doc}`
role:

```markdown
See [](03-deliverable-one) for the full task list.
```

**Callouts** use MyST directives so they render consistently:

```markdown
:::{note} Optional title
Supporting context or an aside.
:::

:::{admonition} Submission Requirements
:class: important
Requirements students must not miss.
:::

:::{admonition} Before you begin
:class: warning
Safety or compliance information.
:::
```

**Figures** use the `figure` directive with a label and alt text, never
bare Markdown image syntax:

```markdown
:::{figure} ../assets/figures/example.svg
:label: fig-example
:width: 80%
:alt: Description of what the figure shows.

Caption, including data source.
:::
```

**Every factual claim needs a citation.** Add the source to
`references.bib`, then cite it as `[@citekey]`. MyST generates the
reference list automatically. This is the same standard most projects
ask of students.

## Requirements

Jupyter Book 2 needs both Python and Node.js:

```bash
pip install jupyter-book
```

Node.js 18 or later must be installed separately; the build will prompt
you if it is missing.

## Before submitting

- [ ] Build completes with no warnings
- [ ] Every `REPLACE` value in `myst.yml` is filled in
- [ ] Every figure has alt text and a caption
- [ ] Every factual claim is cited
- [ ] Permission obtained for all photographs of people or property
- [ ] All links resolve
