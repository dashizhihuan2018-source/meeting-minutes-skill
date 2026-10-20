#!/usr/bin/env node
'use strict';
// Editable meeting minutes. Dependency: docx. No network, personal data, or bundled fonts.
const fs = require('node:fs');
const path = require('node:path');
const d = require('docx');
const [input, output, requestedStem = '会议纪要'] = process.argv.slice(2);
if (!input || !output || requestedStem !== path.basename(requestedStem) || /[\\/]/.test(requestedStem)) {
  console.error('Usage: node render_minutes.js input.json new-output-directory [filename-stem]');
  process.exit(2);
}
const m = JSON.parse(fs.readFileSync(path.resolve(input), 'utf8'));
for (const field of ['title', 'date', 'summary']) {
  if (typeof m[field] !== 'string' || !m[field].trim()) throw new Error(`Missing string: ${field}`);
}
for (const field of ['conclusions', 'actions', 'discussions']) {
  if (!Array.isArray(m[field])) throw new Error(`Missing array: ${field}`);
}
const font = m.style?.font || '思源黑体 CN';
const ink = '17364A', teal = '137C86', gray = '61717A', light = 'EDF5F6';
const width = 9300;
const R = (text, opts = {}) => new d.TextRun({ text: String(text ?? ''), font, size: 21, color: ink, ...opts });
const P = (text, opts = {}) => new d.Paragraph({ children: [R(text)], spacing: { line: 302, after: 100 }, ...opts });
const H = (n, title) => new d.Paragraph({
  heading: d.HeadingLevel.HEADING_1, keepNext: true,
  children: [R(String(n).padStart(2, '0') + '  ', { color: teal, size: 25, bold: true }), R(title, { bold: true, size: 25 })],
  spacing: { before: 230, after: 140 }
});
const none = { style: d.BorderStyle.NONE, size: 0, color: 'FFFFFF' };
const line = { style: d.BorderStyle.SINGLE, size: 4, color: 'D5E3E7' };
const B = (b) => ({ top: b, bottom: b, left: b, right: b });
const cell = (children, w, fill, border = none, margins = {}) => new d.TableCell({
  width: { size: w, type: d.WidthType.DXA }, shading: { type: d.ShadingType.CLEAR, fill },
  verticalAlign: d.VerticalAlign.CENTER, borders: B(border),
  margins: { top: 120, bottom: 120, left: 150, right: 150, ...margins }, children
});
const table = (rows, widths) => new d.Table({ width: { size: width, type: d.WidthType.DXA }, columnWidths: widths, borders: B(none), rows });
const body = [];
body.push(new d.Paragraph({ children: [R('MEETING MINUTES', { size: 17, color: teal, bold: true, characterSpacing: 25 })], spacing: { before: 60, after: 150 } }));
body.push(new d.Paragraph({ children: [R(m.title, { size: 42, bold: true })], keepNext: true, spacing: { after: 100 } }));
if (m.subtitle) body.push(new d.Paragraph({ children: [R(m.subtitle, { size: 25, color: gray })], spacing: { after: 200 }, keepNext: true }));
const metadata = [['会议日期', m.date], ['交流形式', m.format || '未提供'], ['交流单位', (m.organizations || []).join(' · ') || '未提供']];
body.push(table([new d.TableRow({ cantSplit: true, children: metadata.map(([k, v]) => cell([
  P(k, { children: [R(k, { size: 16, color: gray })], spacing: { after: 60 } }),
  P(v, { children: [R(v, { size: 19, bold: true })], spacing: { after: 0, line: 270 } })
], width / 3, 'F3F6F7')) })], [3100, 3100, 3100]));
body.push(H(1, '会议摘要'));
body.push(table([new d.TableRow({ cantSplit: true, children: [cell([
  P(m.summary, { spacing: { line: 305, after: 0 } })
], width, light, none, { top: 160, bottom: 160, left: 200, right: 200 })] })], [width]));
body.push(H(2, m.conclusion_heading || '关键决策'));
m.conclusions.forEach((s, i) => body.push(new d.Paragraph({
  children: [R(String(i + 1).padStart(2, '0') + '  ', { color: teal, bold: true }), R(s)],
  keepLines: true, spacing: { line: 295, after: 90 }
})));
body.push(H(3, '行动事项'));
const widths = [650, 4350, 2300, 2000];
const actionRows = [new d.TableRow({ tableHeader: true, cantSplit: true, children: ['ID', '事项与交付', '跟进方', '期限'].map((s, i) => cell([
  P(s, { children: [R(s, { size: 19, bold: true, color: 'FFFFFF' })], spacing: { after: 0 } })
], widths[i], ink)) })];
m.actions.forEach((a, i) => {
  if (!a.task) throw new Error('Action is missing task');
  const values = [a.id || `A${String(i + 1).padStart(2, '0')}`, a.task, a.owner || '待确认', a.due || '未约定'];
  actionRows.push(new d.TableRow({ cantSplit: true, children: values.map((s, j) => cell([
    P(s, { children: [R(s, { size: 19, bold: j === 0, color: j === 0 ? teal : ink })], spacing: { line: 280, after: 0 } })
  ], widths[j], i % 2 ? 'FFFFFF' : 'F4F7F8', line)) }));
});
body.push(table(actionRows, widths));
if (m.action_note) body.push(P(m.action_note, { children: [R(m.action_note, { size: 18, color: gray })], spacing: { before: 100, after: 0, line: 260 } }));
if (m.layout?.discussion_new_page) body.push(new d.Paragraph({ children: [new d.PageBreak()] }));
body.push(H(4, '讨论要点'));
m.discussions.forEach((section, i) => {
  body.push(new d.Paragraph({
    heading: d.HeadingLevel.HEADING_2, keepNext: true,
    children: [R(String(i + 1).padStart(2, '0') + '  ', { color: teal, size: 24, bold: true }), R(section.title, { size: 24, bold: true })],
    spacing: { before: 180, after: 100 }
  }));
  const paragraphs = Array.isArray(section.text) ? section.text : [section.text];
  paragraphs.filter(Boolean).forEach(s => body.push(P(s, { keepLines: true, spacing: { line: 320, after: 130 } })));
});
if (m.next_steps) {
  body.push(new d.Paragraph({ children: [R('下一步', { size: 23, bold: true, color: teal })], keepNext: true, spacing: { before: 220, after: 100 } }));
  body.push(P(m.next_steps, { keepLines: true }));
}
const doc = new d.Document({ creator: 'Meeting Minutes', lastModifiedBy: 'Meeting Minutes', title: m.title,
  styles: { default: { document: { run: { font, size: 21, color: ink }, paragraph: { spacing: { line: 302 } } } } },
  sections: [{ properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1000, bottom: 1000, left: 1303, right: 1303 } } },
    headers: { default: new d.Header({ children: [new d.Paragraph({ children: [R(m.header || '技术交流  /  会议纪要', { size: 16, color: gray })], border: { bottom: line }, spacing: { after: 100 } })] }) },
    footers: { default: new d.Footer({ children: [new d.Paragraph({ alignment: d.AlignmentType.RIGHT, children: [R(m.date + '   /   ', { size: 16, color: gray }), new d.TextRun({ children: [d.PageNumber.CURRENT], font, size: 16, color: gray })] })] }) }, children: body }]
});
const safe = v => String(v ?? '').replace(/\|/g, '\\|').replace(/\r?\n/g, ' ');
const md = [`# ${m.title}`, m.subtitle || '', m.date, '', '## 一、会议摘要', m.summary, '', `## 二、${m.conclusion_heading || '关键决策'}`,
  ...m.conclusions.map((s, i) => `${i + 1}. ${s}`), '', '## 三、行动事项', '| ID | 事项与交付 | 跟进方 | 期限 |', '| --- | --- | --- | --- |',
  ...m.actions.map((a, i) => `| ${[a.id || `A${String(i + 1).padStart(2, '0')}`, a.task, a.owner || '待确认', a.due || '未约定'].map(safe).join(' | ')} |`),
  m.action_note || '', '', '## 四、讨论要点', ...m.discussions.flatMap(s => [`### ${s.title}`, ...(Array.isArray(s.text) ? s.text : [s.text])]),
  ...(m.next_steps ? ['', '## 下一步', m.next_steps] : [])].filter(s => s !== undefined).join('\n\n');
async function main() {
  const buffer = await d.Packer.toBuffer(doc);
  const out = path.resolve(output);
  fs.mkdirSync(out); // No recursive/overwrite: output must be a new child of an existing directory.
  fs.writeFileSync(path.join(out, requestedStem + '.docx'), buffer, { flag: 'wx' });
  fs.writeFileSync(path.join(out, requestedStem + '.md'), md, { flag: 'wx' });
  console.log(JSON.stringify({ files: 2, actions: m.actions.length, discussions: m.discussions.length }));
}
main().catch(err => { console.error(err.message); process.exitCode = 1; });
