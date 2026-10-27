from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from lxml import etree as E
import hashlib
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / '.work'
SOURCE = ROOT / 'Пояснительная записка Антипов.docx'
BACKUP = WORK / 'before-formatting-20261027.docx'
OUTPUT = WORK / 'spacing-candidate.docx'
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS = {'w': W, 'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}

def tag(name): return '{'+W+'}'+name
def child(parent, name):
    el = parent.find(tag(name))
    if el is None:
        el = E.SubElement(parent, tag(name))
    return el
def props(p):
    pr = p.find(tag('pPr'))
    if pr is None:
        pr = E.Element(tag('pPr')); p.insert(0, pr)
    return pr
def flag(pr, name, value=True): child(pr, name).set(tag('val'), '1' if value else '0')
def spacing(pr, before=None, after=None):
    el = child(pr, 'spacing')
    for key, value in [('before', before), ('after', after)]:
        if value is not None:
            el.set(tag(key), str(round(value*20)))
            el.set(tag(key+'Autospacing'), '0')
            el.attrib.pop(tag(key+'Lines'), None)
def style(p): return p.find('w:pPr/w:pStyle', NS).get(tag('val')) if p.find('w:pPr/w:pStyle', NS) is not None else ''
def text(p): return ''.join(p.itertext()) if False else ''.join(p.xpath('.//w:t/text()', namespaces=NS))
def body_paragraph(value):
    p = E.Element(tag('p')); pr = props(p)
    child(pr, 'pStyle').set(tag('val'), 'CourseBody')
    flag(pr, 'keepLines'); flag(pr, 'keepNext', False)
    r = E.SubElement(p, tag('r')); E.SubElement(r, tag('t')).text = value
    return p

if not BACKUP.exists(): BACKUP.write_bytes(SOURCE.read_bytes())
with ZipFile(BACKUP) as z:
    original_parts = {name: z.read(name) for name in z.namelist()}
doc = E.fromstring(original_parts['word/document.xml'])
styles = E.fromstring(original_parts['word/styles.xml'])
body = doc.find('w:body', NS)

for ident, before, after, newpage in [
    ('CourseHeading1', 0, 18, True), ('CourseHeading2', 18, 12, False),
    ('CourseIntroduction', 0, 18, True), ('CourseReferences', 0, 18, True),
    ('CourseContentsTitle', 0, 18, False), ('CourseFigure', 14, None, False),
]:
    matches = styles.xpath('./w:style[@w:styleId=$ident]', namespaces=NS, ident=ident)
    if not matches: continue
    pr = child(matches[0], 'pPr'); spacing(pr, before, after)
    flag(pr, 'pageBreakBefore', newpage); flag(pr, 'keepNext'); flag(pr, 'keepLines')

started = False
main_nodes = []
for node in list(body):
    if node.tag == tag('p') and style(node) == 'CourseIntroduction': started = True
    if started: main_nodes.append(node)

# Remove old forced page breaks from subsection headings and prose. Chapter
# starts remain controlled by their heading style rather than empty paragraphs.
for p in [n for n in main_nodes if n.tag == tag('p')]:
    ident = style(p); pr = props(p)
    if ident in ('CourseHeading1', 'CourseIntroduction', 'CourseReferences'):
        flag(pr, 'pageBreakBefore'); flag(pr, 'keepNext'); flag(pr, 'keepLines')
        spacing(pr, before=0, after=18)
    elif ident == 'CourseHeading2':
        flag(pr, 'pageBreakBefore', False); flag(pr, 'keepNext'); flag(pr, 'keepLines')
        spacing(pr, before=18, after=12)
    elif ident == 'CourseBody':
        flag(pr, 'pageBreakBefore', False)
    if ident in ('CourseHeading1', 'CourseHeading2', 'CourseIntroduction', 'CourseReferences'):
        for br in p.xpath('.//w:br[@w:type="page"]', namespaces=NS): br.getparent().remove(br)

# Consecutive chapter and subsection headings have precisely a 12 pt gap.
for p in [n for n in main_nodes if n.tag == tag('p') and style(n) == 'CourseHeading1']:
    nxt = p.getnext()
    if nxt is not None and nxt.tag == tag('p') and style(nxt) == 'CourseHeading2':
        spacing(props(p), after=12); spacing(props(nxt), before=0)

figure_notes = [
    'Распределение сценариев определяет состав процедур для каждой роли. '
    'Общие функции выполняются с учетом прав пользователя и принадлежности запрашиваемых данных.',
    'Связи схемы обеспечивают принадлежность счетов и карт клиентам '
    'и позволяют учитывать списания и зачисления в истории каждого счета.',
]
figures = [p for p in main_nodes if p.tag == tag('p') and p.xpath('.//w:drawing', namespaces=NS)]
for index, p in enumerate(figures):
    spacing(props(p), before=14)
    flag(props(p), 'keepNext'); flag(props(p), 'keepLines')
    previous = p.getprevious()
    if previous is not None and previous.tag == tag('p'):
        spacing(props(previous), after=0); flag(props(previous), 'keepNext'); flag(props(previous), 'keepLines')
    cap = p.getnext()
    assert cap is not None and style(cap) == 'CourseCaption'
    # Existing figure-to-caption and caption-to-text spacing stays intact.
    flag(props(cap), 'keepNext'); flag(props(cap), 'keepLines')
    cap.addnext(body_paragraph(figure_notes[index]))
    if index == 1:
        # Leave enough room for introduction, caption and substantive text on
        # the same page, without cropping or changing the embedded image.
        extent = p.find('.//wp:extent', NS)
        old_x, old_y = int(extent.get('cx')), int(extent.get('cy'))
        max_y = round(17.0*360000)
        if old_y > max_y:
            new_x = round(old_x*max_y/old_y)
            extent.set('cx', str(new_x)); extent.set('cy', str(max_y))
            for ext in p.xpath('.//a:xfrm/a:ext', namespaces=NS):
                ext.set('cx', str(new_x)); ext.set('cy', str(max_y))

table_notes = [
    'Раздельное хранение профилей, счетов и операций сохраняет финансовую историю '
    'при блокировке пользователя.',
    'Поля начального и текущего остатков используются совместно с историей операций '
    'для проверки согласованности состояния счета.',
    'Связи со счетами списания и зачисления позволяют включать одну операцию '
    'в историю обоих участников перевода.',
    'Декларативные ограничения проверяют допустимость значений и ссылок. '
    'Проверки остатков, лимитов и полномочий выполняются процедурами проведения операций.',
    'Порядок столбцов составных индексов соответствует отбору по счету и периоду. '
    'При испытаниях оцениваются планы запросов и стоимость сопровождения индексов.',
    'Разделение пакетов позволяет выдавать каждой роли доступ только к необходимым '
    'процедурам и исключает прямое изменение прикладных таблиц.',
]
tables = [n for n in main_nodes if n.tag == tag('tbl')]
assert len(tables) == len(table_notes)
for table_index, (table, note) in enumerate(zip(tables, table_notes)):
    # These six compact tables fit on one page. Keeping all rows together with
    # the following explanation prevents any page ending in a table row.
    for p in table.xpath('.//w:tc/w:p', namespaces=NS):
        flag(props(p), 'keepNext'); flag(props(p), 'keepLines')
    for row in table.findall(tag('tr')): flag(child(row, 'trPr'), 'cantSplit')
    if table_index == 0:
        # Small vertical padding adjustment keeps the complete entity inventory
        # and its explanation on the chapter's first page at the existing font.
        for margin in table.xpath('.//w:tcPr/w:tcMar', namespaces=NS):
            for side in ['top', 'bottom']:
                child(margin, side).set(tag('w'), '30')
    if table_index == 4:
        for row in table.findall(tag('tr')):
            cell = row.find(tag('tc'))
            if cell is not None and 'IX_AUDIT_ACTOR_TIME' in text(cell):
                for run in cell.findall('.//'+tag('r')):
                    rpr = child(run, 'rPr')
                    run.remove(rpr); run.insert(0, rpr)
                    child(rpr, 'sz').set(tag('val'), '21')
                    child(rpr, 'szCs').set(tag('val'), '21')
    caption = table.getprevious()
    intro = caption.getprevious() if caption is not None else None
    for preceding in [caption, intro]:
        if preceding is not None and preceding.tag == tag('p'):
            flag(props(preceding), 'keepLines'); flag(props(preceding), 'keepNext')
    nxt = table.getnext()
    if nxt is not None and nxt.tag == tag('p') and not text(nxt).strip() and not nxt.xpath('.//w:drawing', namespaces=NS):
        body.remove(nxt)
    table.addnext(body_paragraph(note))

# Remove manual breaks before all subsection headings, including breaks held
# in adjacent otherwise empty paragraphs. Retain section properties/bookmarks.
for p in list(body):
    if p.tag != tag('p') or text(p).strip() or p.xpath('.//w:drawing|.//w:sectPr|.//w:fldChar|.//w:bookmarkStart|.//w:bookmarkEnd', namespaces=NS): continue
    nxt = p.getnext()
    if nxt is not None and nxt.tag == tag('p') and style(nxt) == 'CourseHeading2':
        body.remove(p)

changed = {'word/document.xml': E.tostring(doc, encoding='UTF-8', xml_declaration=True, standalone=True),
           'word/styles.xml': E.tostring(styles, encoding='UTF-8', xml_declaration=True, standalone=True)}
with ZipFile(BACKUP) as source, ZipFile(OUTPUT, 'w', ZIP_DEFLATED) as out:
    for info in source.infolist(): out.writestr(info, changed.get(info.filename, source.read(info.filename)))
with ZipFile(OUTPUT) as z:
    assert all(z.read(n) == data for n, data in original_parts.items() if n not in changed)
    original_text = E.fromstring(original_parts['word/document.xml']).xpath('//w:t/text()', namespaces=NS)
    new_text = E.fromstring(z.read('word/document.xml')).xpath('//w:t/text()', namespaces=NS)
    assert all(value in new_text for value in original_text), 'A source text run was removed'
report = {'backup': str(BACKUP), 'output': str(OUTPUT), 'source_sha256': hashlib.sha256(BACKUP.read_bytes()).hexdigest(),
          'figures': len(figures), 'tables': len(tables), 'new_explanations': figure_notes+table_notes,
          'changed_package_parts': list(changed)}
(WORK/'spacing-changes.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(OUTPUT)
print('Original text and all media parts preserved; changed only document.xml and styles.xml.')
