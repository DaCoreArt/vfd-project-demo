/**
 * Headless check that Word/PDF export libraries produce valid files
 * with the expected structure (same approach as the browser forms).
 */
import { createRequire } from "module";
import { writeFileSync, mkdirSync, readFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { execSync } from "child_process";

const __dirname = dirname(fileURLToPath(import.meta.url));
const outDir = join(__dirname, "..", "tmp-export-test");
mkdirSync(outDir, { recursive: true });

execSync("npm pack docx@9.5.0 jspdf@2.5.2 --pack-destination .", {
  cwd: outDir,
  stdio: "inherit",
});

// Extract tarballs lightly via npm install in a temp folder
execSync("npm init -y", { cwd: outDir, stdio: "inherit" });
execSync("npm install docx@9.5.0 jspdf@2.5.2 --no-save --no-package-lock", {
  cwd: outDir,
  stdio: "inherit",
});

const require = createRequire(join(outDir, "package.json"));
const { Document, Packer, Paragraph, TextRun, HeadingLevel } = require("docx");
const { jsPDF } = require("jspdf");

const taskId = "D2.1";
const lastName = "Demo";
const date = "2026-09-30";
const base = `${lastName}_${taskId}_${date}`;

const doc = new Document({
  sections: [
    {
      children: [
        new Paragraph({
          heading: HeadingLevel.TITLE,
          children: [new TextRun({ text: "Task D2.1 — Review and Analyze Financial Statements", bold: true })],
        }),
        new Paragraph({ children: [new TextRun("Student name: Demo Student")] }),
        new Paragraph({ children: [new TextRun("Course section: MGMT 603")] }),
        new Paragraph({ children: [new TextRun("Date: 2026-09-30")] }),
        new Paragraph({ children: [new TextRun("Department analyzed: Broad Channel VFD & Ambulance Corp.")] }),
        new Paragraph({
          heading: HeadingLevel.HEADING_1,
          children: [new TextRun("Key metrics by year")],
        }),
        new Paragraph({ children: [new TextRun("Operating surplus test content.")] }),
        new Paragraph({
          heading: HeadingLevel.HEADING_1,
          children: [new TextRun("References")],
        }),
        new Paragraph({
          children: [new TextRun("Author, A. A. (2024). Title. Publisher. https://example.org")],
        }),
      ],
    },
  ],
});

const docxBuf = await Packer.toBuffer(doc);
const docxPath = join(outDir, `${base}.docx`);
writeFileSync(docxPath, docxBuf);

const pdf = new jsPDF({ unit: "pt", format: "letter" });
pdf.setFont("helvetica", "bold");
pdf.setFontSize(16);
pdf.text("Task D2.1 — Review and Analyze Financial Statements", 56, 72);
pdf.setFont("helvetica", "normal");
pdf.setFontSize(11);
pdf.text("Student name: Demo Student", 56, 100);
pdf.text("References", 56, 130);
pdf.text("Author, A. A. (2024). Title. Publisher.", 56, 148);
const pdfPath = join(outDir, `${base}.pdf`);
writeFileSync(pdfPath, Buffer.from(pdf.output("arraybuffer")));

const docxBytes = readFileSync(docxPath);
const pdfBytes = readFileSync(pdfPath);

const isZip = docxBytes[0] === 0x50 && docxBytes[1] === 0x4b; // PK
const isPdf = pdfBytes.slice(0, 4).toString("ascii") === "%PDF";

console.log("DOCX path:", docxPath, "size:", docxBytes.length, "zip-signature:", isZip);
console.log("PDF path:", pdfPath, "size:", pdfBytes.length, "pdf-signature:", isPdf);

if (!isZip || !isPdf) {
  process.exit(1);
}
console.log("Export smoke test passed.");
