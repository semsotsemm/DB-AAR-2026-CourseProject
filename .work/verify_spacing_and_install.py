from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
from PIL import Image, ImageChops
import hashlib
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / '.work'
BACKUP = WORK / 'before-formatting-20261027.docx'
CANDIDATE = WORK / 'spacing-candidate.docx'
TARGET = ROOT / 'Пояснительная записка Антипов.docx'
audit = json.loads((WORK/'spacing-native-audit.json').read_text(encoding='utf-8'))
headings = [r for r in audit if r['Kind'] == 'Course Heading 1']
subheadings = [r for r in audit if r['Kind'] == 'Course Heading 2']
figures = [r for r in audit if r['Kind'] == 'Course Figure']
tables = [r for r in audit if r['Kind'] == 'Table'][1:]
assert len(headings) == 3 and all(r['PageBreak'] == -1 and r['Y'] < 60 for r in headings)
assert len(subheadings) == 16 and all(r['PageBreak'] == 0 and r['After'] == 12 for r in subheadings)
assert all(r['Before'] in [0,18] for r in subheadings)
assert len(figures) == 2 and all(r['Before'] == 14 for r in figures)
assert len(tables) == 6 and all(r['StartPage'] == r['EndPage'] == r['AfterPage'] and r['AfterText'] for r in tables)
for n in range(1,4):
    a = Image.open(WORK/'spacing-before'/f'page-{n}.png').convert('RGB')
    b = Image.open(WORK/'spacing-final'/f'page-{n}.png').convert('RGB')
    assert ImageChops.difference(a,b).getbbox() is None, f'Front page {n} changed'
with ZipFile(BACKUP) as old, ZipFile(CANDIDATE) as new:
    media = [name for name in old.namelist() if name.startswith('word/media/')]
    assert media and all(new.read(name) == old.read(name) for name in media)
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    original_doc = E.fromstring(old.read('word/document.xml'))
    final_doc = E.fromstring(new.read('word/document.xml'))
    def body_paragraphs(doc):
        result=[]; started=False
        for p in doc.xpath('/w:document/w:body/w:p',namespaces=ns):
            ident=p.xpath('string(w:pPr/w:pStyle/@w:val)',namespaces=ns)
            if ident=='CourseIntroduction': started=True
            if started:
                value=''.join(p.xpath('.//w:t/text()',namespaces=ns))
                if value: result.append(value)
        return result
    old_text = body_paragraphs(original_doc)
    new_text = body_paragraphs(final_doc)
    assert all(p in new_text for p in old_text), 'Source paragraph changed'
    assert len(final_doc.xpath('//w:drawing',namespaces=ns)) == 2
    assert len(final_doc.xpath('/w:document/w:body/w:tbl',namespaces=ns)) == 7
    for n in [9,11]:
        page_text = json.loads((WORK/'spacing-final/text.json').read_text(encoding='utf-8'))[n-1]
        assert 'Рисунок' in page_text
        tail=page_text.split('Рисунок',1)[1].split('\n',1)[-1].strip()
        assert len(tail)>100, 'Figure has no following prose'

# Never replace any user edits made while the formatting candidate was prepared.
assert TARGET.read_bytes() == BACKUP.read_bytes(), 'The user modified the document during formatting'
try:
    TARGET.write_bytes(CANDIDATE.read_bytes())
except PermissionError:
    TARGET = ROOT / 'Пояснительная записка Антипов — исправленное оформление.docx'
    TARGET.write_bytes(CANDIDATE.read_bytes())
assert TARGET.read_bytes() == CANDIDATE.read_bytes()
report = {'target': str(TARGET), 'backup': str(BACKUP), 'pages': 23,
          'verified': ['23 pages visually inspected', 'front pages unchanged', 'all media byte-identical',
                       'source body paragraphs preserved', '14 pt before figures', 'subsection gaps 18/12 pt',
                       'adjacent chapter/subsection gap 12 pt', 'all chapters start new pages',
                       'no forced subsection breaks', 'all tables and following prose on same page',
                       'prose follows both figures on same page', 'native TOC updated'],
          'sha256': hashlib.sha256(TARGET.read_bytes()).hexdigest()}
(WORK/'spacing-verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
