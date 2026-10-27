# Document contract

## References and editable scope

- Style reference: D:/WorkSpace/DB-AAR-2026-CourseProject/Пояснительная записка Антипов(старая).docx
- Reference SHA-256: 5ff8509cab5f8006a78fae427fe7451cc6193d0a9b03a3a08c3dc705e424ffb3
- Reference render: .work/reference.pdf, 77 pages, .work/reference-render/page-N.png; reviewed full contact sheets and full-size main-body pages 6 and 15.
- Content authority: updated Пояснительная записка Антипов.docx, 32066 bytes, first title/assignment/calendar pages only. Preserve this file unchanged; create a separate completed document.
- Subject: Oracle internet banking with encryption and masking. Required roles: administrator, employee, client; access through procedures; JSON exchange; future performance test >=100000 rows. No implementation or performance result exists in the provided folder.
- Fill Introduction, Task statement, Database design, Development of database objects; add an actual TOC. Bibliographic references support the technical design. Future sections remain in the original assignment's contents list, without fabricated completion text.

## Page and typography evidence

- Reference A4 portrait: 11906 x 16838 twips. Left 1701 twips, right 850/851, top 1134; bottom 1304 in opening section, 1134 in main section. No running header text or page footer text in reference.
- Preserve new document title/assignment section geometry and all original paragraphs/tables. Main text uses reference's main-section margins (30 / 15 / 20 / 20 mm).
- Body: Times New Roman 14 pt, black, justified, first line 709 twips (12.5 mm), single line spacing, no interparagraph space. Evidence: old document paragraphs 104,196,205; reference Normal base is 10pt so actual 14pt is deliberate run formatting/custom body style.
- Introduction: centered bold TNR14, upper case, no numbering, new page. Source paragraph 103.
- Numbered chapters: bold TNR14, new page, first-line placement from old chapter headings; actual multilevel numbering (not typed fake heading numbers). Subsections TNR14 bold, 12pt before/after, keep with following paragraph.
- TOC: source-derived formal plain list, TNR14, dot leaders, right-aligned page numbers; regenerate in Microsoft Word.
- Captions: TNR14 regular black, centered, below images; reference p119. Figures must have preceding body introduction; caption stays with figure. Tables receive preceding explanation and caption above, repeated header, no split rows, TNR11-12.
- No decorative colors or rules. Technical figures use black/gray editable UML/ER shapes.
- Title and assignment source paragraphs are preserved. Their existing differing course/department labels will be identified separately to the user, not silently rewritten outside scope.

## Slots and package handling

- Keep all existing body elements through assignment/calendar/signature paragraphs. Do not reuse previous musical-content body, figures or appendices.
- Append a TOC, introduction, chapters 1-3, and concise real references. Add two generated diagrams in context plus captions; the same diagram model drives DOCX images and editable draw.io XML.
- Preserve all original package parts byte-for-byte except word/document.xml, word/styles.xml, word/numbering.xml, word/settings.xml, word/_rels/document.xml.rels and [Content_Types].xml; image parts are additive. Word may rewrite parts during authorized field refresh; record any such changes in QA evidence and retain pre-refresh version.
- Preserve-only inventory generated in .work/package-inventory.json, including sizes and SHA-256. Verify source files are unchanged before delivery.
- Keep old comments/source bibliography untouched in retained reference; do not copy their contents into the new subject.

## Rendering and fidelity

- Canonical render_docx.py was run against the style reference and failed: no bundled/native soffice.exe on PATH. Installed desktop LibreOffice is not used.
- Use independent hidden Microsoft Word COM instance to export read-only reference and generated final to PDF; use bundled pypdfium2 to render all pages to PNG. Inspect every final page; check TOC against real pagination.
- Final must remain A4 portrait; confirm table sizes, diagram labels, no orphan headings, no leading figures without explanatory text, no empty pages, no false implementation/testing claims.
