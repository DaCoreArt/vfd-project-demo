/* Shared client-side deliverable form: draft save + Word/PDF export. Nothing leaves this browser. */
(function () {
  "use strict";

  const cfg = window.DELIVERABLE_CONFIG;
  if (!cfg || !cfg.taskId || !cfg.title || !Array.isArray(cfg.sections)) {
    console.error("DELIVERABLE_CONFIG is missing or invalid.");
    return;
  }

  const STORAGE_KEY = `vfd-deliverable-draft:${cfg.taskId}`;
  const DEPTS_URL = new URL("../../data/departments.json", window.location.href).href;

  const $ = (id) => document.getElementById(id);

  function todayISO() {
    const d = lastEditedDate() || new Date();
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${y}-${m}-${day}`;
  }

  function lastEditedDate() {
    const raw = $("date")?.value;
    if (!raw) return null;
    const d = new Date(raw + "T12:00:00");
    return Number.isNaN(d.getTime()) ? null : d;
  }

  function lastNameFromStudent() {
    const name = ($("student-name")?.value || "").trim();
    if (!name) return "Student";
    const parts = name.split(/\s+/);
    return parts[parts.length - 1].replace(/[^\w-]/g, "") || "Student";
  }

  function filename(ext) {
    return `${lastNameFromStudent()}_${cfg.taskId}_${todayISO()}.${ext}`;
  }

  function collect() {
    const data = {
      studentName: $("student-name").value.trim(),
      courseSection: $("course-section").value.trim(),
      date: $("date").value,
      department: $("department").value.trim(),
      references: $("references").value.trim(),
      sections: {}
    };
    cfg.sections.forEach((sec, i) => {
      data.sections[sec.id] = ($(`sec-${sec.id}`) || { value: "" }).value.trim();
    });
    return data;
  }

  function apply(data) {
    if (!data) return;
    if (data.studentName != null) $("student-name").value = data.studentName;
    if (data.courseSection != null) $("course-section").value = data.courseSection;
    if (data.date != null) $("date").value = data.date;
    if (data.department != null) $("department").value = data.department;
    if (data.references != null) $("references").value = data.references;
    cfg.sections.forEach((sec) => {
      const el = $(`sec-${sec.id}`);
      if (el && data.sections && data.sections[sec.id] != null) {
        el.value = data.sections[sec.id];
      }
    });
  }

  function setStatus(msg, isError) {
    const el = $("status");
    if (!el) return;
    el.textContent = msg || "";
    el.classList.toggle("error", !!isError);
  }

  function saveDraft() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(collect()));
      setStatus("Draft saved in this browser on this device.");
    } catch (err) {
      setStatus("Could not save draft (browser storage blocked or full).", true);
    }
  }

  function loadDraft() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return;
      apply(JSON.parse(raw));
      setStatus("Loaded draft from this browser.");
    } catch (err) {
      setStatus("Could not load draft from browser storage.", true);
    }
  }

  function clearDraft() {
    try {
      localStorage.removeItem(STORAGE_KEY);
      setStatus("Draft cleared from this browser.");
    } catch (err) {
      setStatus("Could not clear draft.", true);
    }
  }

  function downloadBlob(blob, name) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = name;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1500);
  }

  async function generateWord() {
    if (!window.docx) {
      setStatus("Word library failed to load.", true);
      return;
    }
    const data = collect();
    const {
      Document, Packer, Paragraph, TextRun, HeadingLevel
    } = window.docx;

    const children = [
      new Paragraph({
        heading: HeadingLevel.TITLE,
        children: [new TextRun({ text: cfg.title, bold: true })]
      }),
      new Paragraph({
        children: [new TextRun({ text: `Task ID: ${cfg.taskId}`, italics: true })]
      }),
      new Paragraph({ children: [] }),
      new Paragraph({ children: [new TextRun({ text: `Student name: ${data.studentName || "—"}` })] }),
      new Paragraph({ children: [new TextRun({ text: `Course section: ${data.courseSection || "—"}` })] }),
      new Paragraph({ children: [new TextRun({ text: `Date: ${data.date || "—"}` })] }),
      new Paragraph({ children: [new TextRun({ text: `Department analyzed: ${data.department || "—"}` })] }),
    ];

    cfg.sections.forEach((sec) => {
      children.push(new Paragraph({ children: [] }));
      children.push(new Paragraph({
        heading: HeadingLevel.HEADING_1,
        children: [new TextRun(sec.label)]
      }));
      const body = data.sections[sec.id] || "";
      body.split(/\n/).forEach((line) => {
        children.push(new Paragraph({
          children: [new TextRun(line || " ")]
        }));
      });
    });

    children.push(new Paragraph({ children: [] }));
    children.push(new Paragraph({
      heading: HeadingLevel.HEADING_1,
      children: [new TextRun("References")]
    }));
    children.push(new Paragraph({
      children: [new TextRun({
        text: "APA 7th edition. List all sources with page numbers or deep hyperlinks.",
        italics: true
      })]
    }));
    (data.references || "").split(/\n/).forEach((line) => {
      children.push(new Paragraph({
        children: [new TextRun(line || " ")]
      }));
    });

    const doc = new Document({
      sections: [{
        properties: {},
        children
      }]
    });

    const blob = await Packer.toBlob(doc);
    downloadBlob(blob, filename("docx"));
    setStatus(`Downloaded ${filename("docx")}. Upload it to the assignment in Brightspace.`);
  }

  function generatePdf() {
    const jspdfNS = window.jspdf;
    if (!jspdfNS || !jspdfNS.jsPDF) {
      setStatus("PDF library failed to load.", true);
      return;
    }
    const data = collect();
    const doc = new jspdfNS.jsPDF({ unit: "pt", format: "letter" });
    const margin = 56;
    const maxWidth = 500;
    let y = margin;
    const pageHeight = doc.internal.pageSize.getHeight();

    function ensureSpace(h) {
      if (y + h > pageHeight - margin) {
        doc.addPage();
        y = margin;
      }
    }

    function writeWrapped(text, opts) {
      const size = opts?.size || 11;
      const bold = !!opts?.bold;
      const gap = opts?.gap ?? 8;
      doc.setFont("helvetica", bold ? "bold" : "normal");
      doc.setFontSize(size);
      const lines = doc.splitTextToSize(text || " ", maxWidth);
      lines.forEach((line) => {
        ensureSpace(size + 4);
        doc.text(line, margin, y);
        y += size + 3;
      });
      y += gap;
    }

    writeWrapped(cfg.title, { size: 16, bold: true, gap: 4 });
    writeWrapped(`Task ID: ${cfg.taskId}`, { size: 11, gap: 10 });
    writeWrapped(`Student name: ${data.studentName || "—"}`);
    writeWrapped(`Course section: ${data.courseSection || "—"}`);
    writeWrapped(`Date: ${data.date || "—"}`);
    writeWrapped(`Department analyzed: ${data.department || "—"}`, { gap: 14 });

    cfg.sections.forEach((sec) => {
      writeWrapped(sec.label, { size: 13, bold: true, gap: 6 });
      writeWrapped(data.sections[sec.id] || " ", { gap: 12 });
    });

    writeWrapped("References", { size: 13, bold: true, gap: 6 });
    writeWrapped("APA 7th edition. List all sources with page numbers or deep hyperlinks.", { size: 10, gap: 6 });
    writeWrapped(data.references || " ", { gap: 8 });

    doc.save(filename("pdf"));
    setStatus(`Downloaded ${filename("pdf")}. Upload it to the assignment in Brightspace.`);
  }

  async function loadDepartments() {
    const select = $("department");
    if (!select || select.tagName !== "SELECT") return;
    try {
      const resp = await fetch(DEPTS_URL);
      const depts = await resp.json();
      const custom = document.createElement("option");
      custom.value = "";
      custom.textContent = "Select a department…";
      select.appendChild(custom);
      depts.forEach((d) => {
        const opt = document.createElement("option");
        opt.value = d.name;
        opt.textContent = d.name;
        select.appendChild(opt);
      });
      const other = document.createElement("option");
      other.value = "Other / not listed";
      other.textContent = "Other / not listed";
      select.appendChild(other);
    } catch {
      select.innerHTML = '<option value="">Enter department in notes if list unavailable</option>';
    }
  }

  function buildSectionFields() {
    const host = $("sections");
    host.innerHTML = "";
    cfg.sections.forEach((sec) => {
      const wrap = document.createElement("div");
      wrap.className = "field";
      const label = document.createElement("label");
      label.htmlFor = `sec-${sec.id}`;
      label.textContent = sec.label;
      const ta = document.createElement("textarea");
      ta.id = `sec-${sec.id}`;
      ta.rows = sec.rows || 6;
      ta.setAttribute("aria-describedby", sec.hint ? `hint-${sec.id}` : "");
      if (sec.placeholder) ta.placeholder = sec.placeholder;
      wrap.appendChild(label);
      if (sec.hint) {
        const hint = document.createElement("p");
        hint.className = "hint";
        hint.id = `hint-${sec.id}`;
        hint.textContent = sec.hint;
        wrap.appendChild(hint);
      }
      wrap.appendChild(ta);
      host.appendChild(wrap);
    });
  }

  function init() {
    $("task-heading").textContent = cfg.title;
    $("task-id-label").textContent = cfg.taskId;
    if (cfg.intro) $("intro").textContent = cfg.intro;
    buildSectionFields();
    if (!$("date").value) $("date").value = todayISO();

    $("save-draft").addEventListener("click", saveDraft);
    $("clear-draft").addEventListener("click", clearDraft);
    $("gen-word").addEventListener("click", () => {
      generateWord().catch((err) => setStatus(String(err), true));
    });
    $("gen-pdf").addEventListener("click", () => {
      try { generatePdf(); }
      catch (err) { setStatus(String(err), true); }
    });

    loadDepartments().then(loadDraft);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
