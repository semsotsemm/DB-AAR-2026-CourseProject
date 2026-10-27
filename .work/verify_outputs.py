from pathlib import Path
import sys,json,hashlib,re
from zipfile import ZipFile
from lxml import etree as E
from docx import Document
from pypdf import PdfReader
from PIL import Image,ImageChops
from model import TABLES,RELATIONS

ROOT=Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding='utf-8')
expected=json.loads((ROOT/'.work/package-inventory.json').read_text(encoding='utf-8'))
report={}
for name,entry in expected.items():
    actual=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    assert actual==entry['sha256'], f'Changed source {name}'
report['unchanged_sources']=list(expected)
source=Document(ROOT/'Пояснительная записка Антипов.docx')
final_path=ROOT/'Пояснительная записка Антипов — подготовленные разделы.docx'
final=Document(final_path)
assert [p.text for p in final.paragraphs[:len(source.paragraphs)]]==[p.text for p in source.paragraphs]
assert [[c.text for r in final.tables[0].rows for c in r.cells]]==[[c.text for r in source.tables[0].rows for c in r.cells]]
report['source_front_matter_text_preserved']=True
assert len(final.inline_shapes)==2
assert len(final.tables)==7
text='\n'.join(p.text for p in final.paragraphs)+'\n'+'\n'.join(c.text for t in final.tables for r in t.rows for c in r.cells)
for name,_,_ in TABLES:assert name in text
for name in ['ВВЕДЕНИЕ','Постановка задачи','Проектирование базы данных','Разработка объектов базы данных']:assert name in text
assert 'Элементы оглавления не найдены' not in text
assert 'Rewind' not in text and 'PostgreSQL' not in text
report['table_count_in_model']=len(TABLES)
report['relationships_in_model']=len(RELATIONS)
report['word_figures']=len(final.inline_shapes)
report['word_tables']=len(final.tables)
for path in (ROOT/'Диаграммы').glob('*.xml'):
    tree=E.parse(str(path));assert tree.getroot().tag=='mxGraphModel'
    cells=tree.findall('.//mxCell');ids=[c.get('id') for c in cells]
    assert len(ids)==len(set(ids)),str(path)
    for cell in cells:
        for attr in ['source','target','parent']:
            if cell.get(attr):assert cell.get(attr) in ids,(path,attr,cell.get(attr))
native=E.parse(str(ROOT/'Диаграммы/Интернет-банк.drawio'))
assert len(native.findall('diagram'))==2
logical=E.parse(str(ROOT/'Диаграммы/02_Логическая_схема.xml'))
for name,_,fields in TABLES:
    assert len(logical.xpath('//mxCell[@id=$id]',id=name))==1
    for key,field,typ in fields:assert logical.xpath('//mxCell[@id=$id]',id=name+'_'+field)
assert len(logical.xpath('//mxCell[@edge="1"]'))==len(RELATIONS)
report['drawio_xml_integrity']='passed'
pdf=PdfReader(ROOT/'.work/final.pdf')
assert len(pdf.pages)==22
pages=[p.extract_text() for p in pdf.pages]
assert 'Элементы оглавления не найдены' not in '\n'.join(pages)
assert 'Заведующий' not in pages[3]
toc=pages[3]
checks=[('ВВЕДЕНИЕ',5),('Постановка задачи',6),('Проектирование базы данных',10),('Разработка объектов базы данных',15),('СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ',22)]
for label,number in checks:
    line=next(x for x in toc.splitlines() if label in x)
    assert line.strip().endswith(str(number)),(label,line)
    assert label in pages[number-1]
report['toc_chapter_pages']={k:v for k,v in checks}
report['pdf_pages']=len(pdf.pages)
with ZipFile(final_path) as z:
    original=expected['Пояснительная записка Антипов.docx']['parts']
    report['parts_changed_by_authoring_or_word_refresh']=[name for name,data in original.items() if name not in z.namelist() or hashlib.sha256(z.read(name)).hexdigest()!=data['sha256']]
    report['removed_original_parts']=[name for name in original if name not in z.namelist()]
    assert not report['removed_original_parts']
    ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    xml=E.fromstring(z.read('word/document.xml'))
    report['live_toc_field']=xml.xpath('//w:instrText[contains(text(),"TOC")]/text()',namespaces=ns)
    assert report['live_toc_field']
report['reviewed_page_images']='.work/final/page-1.png through page-22.png'
(ROOT/'.work/verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
