# Media Assets — Conventions

Everything visual in this project lives here. This is the single place
authors put images, charts, graphs, diagrams, and interactive files, so
that references never break and structure stays predictable across
projects.

## Folder structure

```
assets/
├── figures/      Charts, graphs, plots, diagrams
├── photos/       Photographs (firehouse visits, equipment, sites)
├── interactive/  Self-contained HTML (maps, widgets)
└── data/         CSV or Excel files a figure was built from
```

## Naming

Lowercase, hyphens, no spaces. Lead with the chapter or deliverable the
asset belongs to:

```
d1-revenue-by-department.png
d2-reserve-ratio-trend.svg
photo-gerritsen-beach-apparatus.jpg
```

Avoid `chart1.png` or `Screenshot 2026-08-26.png` — neither survives
contact with a second author.

## Inserting a figure

Use the MyST `figure` directive rather than plain Markdown image syntax.
It gives you a caption, a numbered label, and a cross-reference target:

```markdown
:::{figure} ../assets/figures/d2-reserve-ratio-trend.svg
:label: fig-reserve-ratio
:width: 80%
:alt: Line chart of reserve ratio across six fiscal years for all eight departments.

Reserve ratio (cash ÷ total expenses) across six fiscal years.
Data source: IRS Form 990 filings.
:::
```

Then reference it anywhere in the text with `[](#fig-reserve-ratio)`,
which renders as a live link reading "Figure 1."

**Alt text is required.** It is what a screen-reader user hears in place
of the image, and CUNY is subject to accessibility requirements. Describe
what the figure *shows*, not that it is a chart.

## Inserting a photograph

Same directive, with attribution in the caption:

```markdown
:::{figure} ../assets/photos/photo-gerritsen-beach-apparatus.jpg
:label: fig-gb-apparatus
:width: 70%
:alt: A pumper engine parked inside an open firehouse bay.

Apparatus bay at Gerritsen Beach VFD. Photograph by the author,
March 2026, used with permission of the department.
:::
```

## Inserting an interactive file

Self-contained HTML goes in `interactive/` and is embedded with an
iframe:

```markdown
:::{iframe} ../assets/interactive/vfd-map.html
:width: 100%
:height: 700px

Response areas of the eight NYC volunteer fire departments.
:::
```

## Format guidance

| Content | Format | Why |
|---|---|---|
| Charts, plots, diagrams | SVG | Scales without blurring; small file |
| Screenshots | PNG | Lossless; keeps text sharp |
| Photographs | JPG | Much smaller than PNG at similar quality |
| Anything interactive | Self-contained HTML | Renders in an iframe without a build step |

Keep images under roughly 1 MB. Large binaries make the repository slow
to clone, and Git cannot meaningfully diff them.

## Permissions

Every photograph of people or private property needs permission before
publication — the site is public. Where the source is not the author,
record it in the caption. Assets whose rights are unclear should not be
committed.
