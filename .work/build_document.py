from pathlib import Path
from copy import deepcopy
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib
import json
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.section import WD_SECTION_START
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from lxml import etree as E
from content import BLOCKS

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / '.work'
SOURCE = ROOT / 'Пояснительная записка Антипов.docx'
REFERENCE = ROOT / 'Пояснительная записка Антипов(старая).docx'
OUTPUT = ROOT / 'Пояснительная записка Антипов — подготовленные разделы.docx'
WORK.mkdir(exist_ok=True)

def hash_bytes(value): return hashlib.sha256(value).hexdigest()

def style(doc, name, size=14, bold=False, alignment=WD_ALIGN_PARAGRAPH.JUSTIFY,
          first=1.25, before=0, after=0, keep=False, page_break=False):
    s=doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH) if name not in doc.styles else doc.styles[name]
    s.base_style=doc.styles['Normal']
    s.font.name='Times New Roman';s.font.size=Pt(size);s.font.bold=bold;s.font.color.rgb=RGBColor(0,0,0)
    f=s.paragraph_format;f.alignment=alignment;f.first_line_indent=Cm(first)
    f.left_indent=Cm(0);f.right_indent=Cm(0);f.line_spacing=1
    f.space_before=Pt(before);f.space_after=Pt(after);f.keep_with_next=keep
    f.keep_together=False;f.widow_control=True;f.page_break_before=page_break
    rpr=s.element.get_or_add_rPr()
    fonts=rpr.find(qn('w:rFonts'))
    if fonts is None:fonts=OxmlElement('w:rFonts');rpr.append(fonts)
    for key in ['ascii','hAnsi','cs','eastAsia']:fonts.set(qn('w:'+key),'Times New Roman')
    lang=OxmlElement('w:lang');lang.set(qn('w:val'),'ru-RU');rpr.append(lang)
    return s

def numbering(doc, h1, h2):
    root=doc.part.numbering_part.element
    abstract=max([int(x.get(qn('w:abstractNumId'))) for x in root.findall(qn('w:abstractNum'))]+[0])+1
    numid=max([int(x.get(qn('w:numId'))) for x in root.findall(qn('w:num'))]+[0])+1
    a=OxmlElement('w:abstractNum');a.set(qn('w:abstractNumId'),str(abstract))
    multi=OxmlElement('w:multiLevelType');multi.set(qn('w:val'),'multilevel');a.append(multi)
    for level,s in enumerate([h1,h2]):
        lvl=OxmlElement('w:lvl');lvl.set(qn('w:ilvl'),str(level))
        for tag,value in [('start','1'),('numFmt','decimal'),('pStyle',s.style_id),('lvlText','%1' if level==0 else '%1.%2'),('lvlJc','left'),('suff','space')]:
            el=OxmlElement('w:'+tag);el.set(qn('w:val'),value);lvl.append(el)
        prop=OxmlElement('w:pPr');ind=OxmlElement('w:ind')
        ind.set(qn('w:left'),'709');ind.set(qn('w:firstLine'),'0');prop.append(ind);lvl.append(prop)
        a.append(lvl)
        spr=s.element.get_or_add_pPr();npr=OxmlElement('w:numPr')
        for tag,value in [('ilvl',str(level)),('numId',str(numid))]:
            el=OxmlElement('w:'+tag);el.set(qn('w:val'),value);npr.append(el)
        spr.append(npr)
        outline=OxmlElement('w:outlineLvl');outline.set(qn('w:val'),str(level));spr.append(outline)
    root.append(a)
    n=OxmlElement('w:num');n.set(qn('w:numId'),str(numid))
    ref=OxmlElement('w:abstractNumId');ref.set(qn('w:val'),str(abstract));n.append(ref);root.append(n)

def make_table(doc, block):
    intro=doc.paragraphs[-1]
    intro.paragraph_format.keep_with_next=True
    cap=doc.add_paragraph(block['text'],'Course Table Caption')
    table=doc.add_table(rows=1, cols=len(block['headers']))
    table.alignment=WD_TABLE_ALIGNMENT.CENTER;table.autofit=False
    total=sum(block['widths']);table._tbl.tblPr.append(OxmlElement('w:tblLayout'))
    table._tbl.tblPr[-1].set(qn('w:type'),'fixed')
    grid=table._tbl.tblGrid
    for col,width in zip(grid.gridCol_lst,block['widths']):col.set(qn('w:w'),str(round(width*567)))
    borders=OxmlElement('w:tblBorders')
    for side in ['top','left','bottom','right','insideH','insideV']:
        el=OxmlElement('w:'+side);el.set(qn('w:val'),'single');el.set(qn('w:sz'),'4');el.set(qn('w:color'),'808080');borders.append(el)
    table._tbl.tblPr.append(borders)
    for row_number,data in enumerate([block['headers']]+block['rows']):
        row=table.rows[0] if row_number==0 else table.add_row()
        pr=row._tr.get_or_add_trPr();pr.append(OxmlElement('w:cantSplit'))
        if row_number==0:pr.append(OxmlElement('w:tblHeader'))
        for colnum,(cell,text,width) in enumerate(zip(row.cells,data,block['widths'])):
            cell.width=Cm(width);cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            cpr=cell._tc.get_or_add_tcPr();margin=OxmlElement('w:tcMar')
            for side in ['top','left','bottom','right']:
                el=OxmlElement('w:'+side);el.set(qn('w:w'),'65' if side in ['top','bottom'] else '85');el.set(qn('w:type'),'dxa');margin.append(el)
            cpr.append(margin)
            if row_number==0:
                shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'EEEEEE');cpr.append(shade)
            p=cell.paragraphs[0];p.style=doc.styles['Course Table Text']
            p.paragraph_format.keep_with_next=row_number<2
            p.alignment=WD_ALIGN_PARAGRAPH.CENTER if row_number==0 else WD_ALIGN_PARAGRAPH.LEFT
            r=p.add_run(text);r.bold=row_number==0
            if row_number>0 and colnum==0 and text.startswith('BANK_') and len(text.split()[0])>18:
                r.font.size=Pt(10.5)
    after=doc.add_paragraph('','Course Body');after.paragraph_format.space_after=Pt(0)
    after.paragraph_format.line_spacing=Pt(2);after.paragraph_format.space_before=Pt(0)
    after.add_run().font.size=Pt(2)

def add_toc(doc):
    doc.add_paragraph('СОДЕРЖАНИЕ','Course Contents Title')
    p=doc.add_paragraph('','Course Body');p.paragraph_format.first_line_indent=Cm(0)
    run=p.add_run();begin=OxmlElement('w:fldChar');begin.set(qn('w:fldCharType'),'begin');run._r.append(begin)
    run=p.add_run();instr=OxmlElement('w:instrText');instr.set(qn('xml:space'),'preserve')
    slash=chr(92)
    instr.text=' TOC '+slash+'o "1-2" '+slash+'h '+slash+'z '+slash+'u '+slash+'b CourseMainText '
    run._r.append(instr)
    run=p.add_run();sep=OxmlElement('w:fldChar');sep.set(qn('w:fldCharType'),'separate');run._r.append(sep)
    run=p.add_run();end=OxmlElement('w:fldChar');end.set(qn('w:fldCharType'),'end');run._r.append(end)

def main():
    assert hash_bytes(REFERENCE.read_bytes())=='5ff8509cab5f8006a78fae427fe7451cc6193d0a9b03a3a08c3dc705e424ffb3'
    inventory={}
    for path in [SOURCE,REFERENCE]:
        with ZipFile(path) as z:
            inventory[path.name]={'sha256':hash_bytes(path.read_bytes()),'parts':{n:{'bytes':len(z.read(n)),'sha256':hash_bytes(z.read(n))} for n in z.namelist()}}
    (WORK/'package-inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2),encoding='utf-8')
    backup=WORK/'original-new.docx'
    if not backup.exists():backup.write_bytes(SOURCE.read_bytes())
    doc=Document(SOURCE)
    # Opening source pages stay untouched; main-body layout comes from the old sample.
    sec=doc.add_section(WD_SECTION_START.NEW_PAGE)
    sec.left_margin=Cm(3);sec.right_margin=Cm(1.5);sec.top_margin=Cm(2);sec.bottom_margin=Cm(2)
    sec.page_width=Cm(21);sec.page_height=Cm(29.7)
    style(doc,'Course Body')
    item=style(doc,'Course List');item.paragraph_format.left_indent=Cm(1.25);item.paragraph_format.first_line_indent=Cm(0)
    ch=style(doc,'Course Heading 1',bold=True,alignment=WD_ALIGN_PARAGRAPH.LEFT,first=0,before=0,after=12,keep=True,page_break=True)
    sh=style(doc,'Course Heading 2',bold=True,alignment=WD_ALIGN_PARAGRAPH.LEFT,first=0,before=12,after=12,keep=True)
    numbering(doc,ch,sh)
    for name in ['Course Introduction','Course References']:
        s=style(doc,name,bold=True,alignment=WD_ALIGN_PARAGRAPH.CENTER,first=0,after=12,keep=True,page_break=True)
        outline=OxmlElement('w:outlineLvl');outline.set(qn('w:val'),'0');s.element.get_or_add_pPr().append(outline)
    style(doc,'Course Contents Title',bold=True,alignment=WD_ALIGN_PARAGRAPH.CENTER,first=0,after=12,keep=True)
    style(doc,'Course Caption',alignment=WD_ALIGN_PARAGRAPH.CENTER,first=0,before=4,after=10)
    style(doc,'Course Table Caption',alignment=WD_ALIGN_PARAGRAPH.LEFT,first=0,before=6,after=6,keep=True)
    style(doc,'Course Table Text',size=11.5,alignment=WD_ALIGN_PARAGRAPH.LEFT,first=0)
    style(doc,'Course Figure',alignment=WD_ALIGN_PARAGRAPH.CENTER,first=0,keep=True)
    style(doc,'Course Source',size=12,first=0)
    # Define built-in TOC styles before Word populates the field.
    for level in [1,2]:
        toc=style(doc,'TOC '+str(level),size=14,alignment=WD_ALIGN_PARAGRAPH.LEFT,first=0)
        toc.paragraph_format.left_indent=Cm(0 if level==1 else .6)
        toc.paragraph_format.keep_with_next=False
    add_toc(doc)
    figure_names={'use_cases':'01_Варианты_использования.png','logical_schema':'02_Логическая_схема.png'}
    previous_was_figure=False
    for block in BLOCKS:
        kind=block['kind'];text=block['text']
        if kind=='intro':
            paragraph=doc.add_paragraph(text,'Course Introduction')
            bookmark=OxmlElement('w:bookmarkStart');bookmark.set(qn('w:id'),'10000');bookmark.set(qn('w:name'),'CourseMainText')
            paragraph._p.insert(1,bookmark)
        elif kind=='h1':doc.add_paragraph(text,'Course Heading 1')
        elif kind=='h2':doc.add_paragraph(text,'Course Heading 2')
        elif kind=='p':
            paragraph=doc.add_paragraph(text,'Course Body')
            if previous_was_figure:paragraph.paragraph_format.page_break_before=True
        elif kind=='item':doc.add_paragraph('— '+text,'Course List')
        elif kind=='table':make_table(doc,block)
        elif kind=='figure':
            # A short heading and explanatory text start every figure page.
            doc.paragraphs[-1].paragraph_format.page_break_before=True
            intro=doc.add_paragraph(block['intro'],'Course Body');intro.paragraph_format.keep_with_next=True
            picture=doc.add_paragraph('','Course Figure')
            r=picture.add_run();r.add_picture(str(ROOT/'Диаграммы'/figure_names[block['name']]),width=Cm(15.5))
            inline=r._r.xpath('.//wp:docPr')[0]
            inline.set('descr',text)
            doc.add_paragraph(text,'Course Caption')
        elif kind=='refs':doc.add_paragraph(text,'Course References')
        elif kind=='source':doc.add_paragraph(text,'Course Source')
        previous_was_figure=kind=='figure'
    bookmark_end=OxmlElement('w:bookmarkEnd');bookmark_end.set(qn('w:id'),'10000');doc.paragraphs[-1]._p.append(bookmark_end)
    settings=doc.settings.element
    update=settings.find(qn('w:updateFields'))
    if update is None:update=OxmlElement('w:updateFields');settings.append(update)
    update.set(qn('w:val'),'true')
    doc.core_properties.title='База данных интернет-банка в Oracle с шифрованием и маскированием данных'
    doc.core_properties.subject='Пояснительная записка к курсовому проекту по дисциплине Базы данных'
    generated=WORK/'generated-package.docx';doc.save(generated)
    changed={'word/document.xml','word/styles.xml','word/numbering.xml','word/settings.xml',
        'word/_rels/document.xml.rels','[Content_Types].xml','docProps/core.xml'}
    # Preserve every opaque source part not involved in the planned edit.
    with ZipFile(SOURCE) as original,ZipFile(generated) as authored,ZipFile(OUTPUT,'w',ZIP_DEFLATED) as final:
        for info in original.infolist():
            data=authored.read(info.filename) if info.filename in changed and info.filename in authored.namelist() else original.read(info.filename)
            final.writestr(info,data)
        for name in authored.namelist():
            if name not in original.namelist():final.writestr(name,authored.read(name))
    (WORK/'pre-word-refresh.docx').write_bytes(OUTPUT.read_bytes())
    print(OUTPUT)
    print('Original input files unchanged. Figures, tables and live TOC added.')

if __name__=='__main__':main()
