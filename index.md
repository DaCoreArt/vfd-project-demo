# The NYC Volunteer Fire Department Project

**MGMT 603 — Nonprofit Accounting and Financial Management**
**A Signature Term Experiential Learning Project**

:::{note} About this project
This course places students directly into the context of New York City's
volunteer fire departments — nonprofit organizations balancing public
safety responsibilities with financial sustainability. Students build a
six-year financial dataset covering all NYC volunteer firehouse
nonprofits, visit a local firehouse, simulate funding scenarios, and
communicate findings — connecting classroom theory to real nonprofit
financial decision-making.
:::

## The eight NYC volunteer fire departments

<div class="vfd-logo-grid" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(9.5rem,1fr));gap:1.25rem;align-items:stretch;margin:1.5rem 0 2rem;">

<a href="https://broadchannelvfd.org/" target="_blank" rel="noopener noreferrer" style="display:flex;flex-direction:column;align-items:center;justify-content:center;gap:0.5rem;min-height:8.5rem;padding:0.75rem;border:1px solid #dcd7cf;text-decoration:none;color:inherit;text-align:center;">
<span style="display:flex;align-items:center;justify-content:center;width:100%;min-height:4.5rem;background:#f3f1ed;font-size:0.75rem;line-height:1.3;padding:0.5rem;">Logo pending<br><code>broad-channel-vfd.png</code></span>
<span style="font-size:0.85rem;font-weight:600;">Broad Channel</span>
</a>

<a href="https://vfanyc.org/edgewater-park-volunteer-hose-company-no-1/" target="_blank" rel="noopener noreferrer" style="display:flex;flex-direction:column;align-items:center;justify-content:center;gap:0.5rem;min-height:8.5rem;padding:0.75rem;border:1px solid #dcd7cf;text-decoration:none;color:inherit;text-align:center;">
<span style="display:flex;align-items:center;justify-content:center;width:100%;min-height:4.5rem;background:#f3f1ed;font-size:0.75rem;line-height:1.3;padding:0.5rem;">Logo pending<br><code>edgewater-park-hose-co.png</code></span>
<span style="font-size:0.85rem;font-weight:600;">Edgewater Park</span>
</a>

<a href="https://gbfd.net" target="_blank" rel="noopener noreferrer" style="display:flex;flex-direction:column;align-items:center;justify-content:center;gap:0.5rem;min-height:8.5rem;padding:0.75rem;border:1px solid #dcd7cf;text-decoration:none;color:inherit;text-align:center;">
<span style="display:flex;align-items:center;justify-content:center;width:100%;min-height:4.5rem;background:#f3f1ed;font-size:0.75rem;line-height:1.3;padding:0.5rem;">Logo pending<br><code>gerritsen-beach-vfd.png</code></span>
<span style="font-size:0.85rem;font-weight:600;">Gerritsen Beach</span>
</a>

<a href="https://www.facebook.com/PointBreezeVFD/" target="_blank" rel="noopener noreferrer" style="display:flex;flex-direction:column;align-items:center;justify-content:center;gap:0.5rem;min-height:8.5rem;padding:0.75rem;border:1px solid #dcd7cf;text-decoration:none;color:inherit;text-align:center;">
<span style="display:flex;align-items:center;justify-content:center;width:100%;min-height:4.5rem;background:#f3f1ed;font-size:0.75rem;line-height:1.3;padding:0.5rem;">Logo pending<br><code>point-breeze-vfd.png</code></span>
<span style="font-size:0.85rem;font-weight:600;">Point Breeze</span>
</a>

<a href="https://richmondengine.org" target="_blank" rel="noopener noreferrer" style="display:flex;flex-direction:column;align-items:center;justify-content:center;gap:0.5rem;min-height:8.5rem;padding:0.75rem;border:1px solid #dcd7cf;text-decoration:none;color:inherit;text-align:center;">
<span style="display:flex;align-items:center;justify-content:center;width:100%;min-height:4.5rem;background:#f3f1ed;font-size:0.75rem;line-height:1.3;padding:0.5rem;">Logo pending<br><code>richmond-engine-co.png</code></span>
<span style="font-size:0.85rem;font-weight:600;">Richmond Engine</span>
</a>

<a href="https://rpfdny.org" target="_blank" rel="noopener noreferrer" style="display:flex;flex-direction:column;align-items:center;justify-content:center;gap:0.5rem;min-height:8.5rem;padding:0.75rem;border:1px solid #dcd7cf;text-decoration:none;color:inherit;text-align:center;">
<span style="display:flex;align-items:center;justify-content:center;width:100%;min-height:4.5rem;background:#f3f1ed;font-size:0.75rem;line-height:1.3;padding:0.5rem;">Logo pending<br><code>rockaway-point-vfd.png</code></span>
<span style="font-size:0.85rem;font-weight:600;">Rockaway Point</span>
</a>

<a href="https://www.facebook.com/RoxburyVolunteerFD/" target="_blank" rel="noopener noreferrer" style="display:flex;flex-direction:column;align-items:center;justify-content:center;gap:0.5rem;min-height:8.5rem;padding:0.75rem;border:1px solid #dcd7cf;text-decoration:none;color:inherit;text-align:center;">
<span style="display:flex;align-items:center;justify-content:center;width:100%;min-height:4.5rem;background:#f3f1ed;font-size:0.75rem;line-height:1.3;padding:0.5rem;">Logo pending<br><code>roxbury-vfd.png</code></span>
<span style="font-size:0.85rem;font-weight:600;">Roxbury</span>
</a>

<a href="https://www.whbvfd.org" target="_blank" rel="noopener noreferrer" style="display:flex;flex-direction:column;align-items:center;justify-content:center;gap:0.5rem;min-height:8.5rem;padding:0.75rem;border:1px solid #dcd7cf;text-decoration:none;color:inherit;text-align:center;">
<span style="display:flex;align-items:center;justify-content:center;width:100%;min-height:4.5rem;background:#f3f1ed;font-size:0.75rem;line-height:1.3;padding:0.5rem;">Logo pending<br><code>west-hamilton-beach-vfd.png</code></span>
<span style="font-size:0.85rem;font-weight:600;">West Hamilton Beach</span>
</a>

</div>

:::{note}
Department logos are pending drop-in under `images/logos/`. Each tile
above is a labeled placeholder until the PNG file is added; alt text for
finished logos should read "[Department name] logo".
:::

## How this book is organized

- **Introduction** — background on NYC volunteer fire departments and the
  purpose of the project
- **Project Overview and Objectives** — learning objectives and the
  five-deliverable structure
- **Deliverables One through Five** — detailed task instructions for
  each phase of the project
- **Rubrics** — grading criteria for every deliverable
- **Citation Guidance** — APA 7th edition citation and reference examples
- **Student Confidentiality Statement** — research project confidentiality
  pledge
- **Media Gallery** — video reference material on firehouse operations,
  apparatus, and nonprofit funding

**Instructor:** Dr. Joseph Foy, CPA ([joseph.foy@cuny.edu](mailto:joseph.foy@cuny.edu))
