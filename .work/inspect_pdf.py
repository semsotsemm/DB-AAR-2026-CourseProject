from pathlib import Path
import sys,json
import pypdfium2 as pdfium
from pypdf import PdfReader
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
pdf_path=Path(sys.argv[1]).resolve()
out=ROOT/'.work'/pdf_path.stem
out.mkdir(exist_ok=True)
sys.stdout.reconfigure(encoding='utf-8')
reader=PdfReader(pdf_path)
texts=[]
for i,page in enumerate(reader.pages):
    t=page.extract_text();texts.append(t)
    print(f'PAGE {i+1}: '+repr(t[:165]).replace('\\n',' ')+' | END '+repr(t[-100:]))
(out/'text.json').write_text(json.dumps(texts,ensure_ascii=False,indent=2),encoding='utf-8')
pdf=pdfium.PdfDocument(str(pdf_path));thumbs=[]
for i,page in enumerate(pdf):
    img=page.render(scale=1.8).to_pil().convert('RGB');img.save(out/f'page-{i+1}.png')
    thumb=img.copy();thumb.thumbnail((300,425));card=Image.new('RGB',(320,455),'#e5e7eb');card.paste(thumb,((320-thumb.width)//2,8));ImageDraw.Draw(card).text((10,435),str(i+1),fill='black');thumbs.append(card)
for start in range(0,len(thumbs),12):
    group=thumbs[start:start+12];sheet=Image.new('RGB',(1280,455*((len(group)+3)//4)),'white')
    for k,item in enumerate(group):sheet.paste(item,((k%4)*320,(k//4)*455))
    sheet.save(out/f'contact-{start//12+1}.png')
print('Images:',out)
