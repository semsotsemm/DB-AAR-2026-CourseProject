from pathlib import Path
import html
import json
import math
from lxml import etree as E
from PIL import Image, ImageDraw, ImageFont
from model import TABLES, RELATIONS

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Диаграммы'
OUT.mkdir(exist_ok=True)
FONT_DIR = Path('C:/Windows/Fonts')
def font(size, bold=False, mono=False):
    filename = 'consola.ttf' if mono else ('arialbd.ttf' if bold else 'arial.ttf')
    return ImageFont.truetype(str(FONT_DIR / filename), size)


class Diagram:
    def __init__(self, name, width, height):
        self.name, self.width, self.height = name, width, height
        self.graph = E.Element('mxGraphModel', dx='1200', dy='900', grid='1', gridSize='10',
            guides='1', tooltips='1', connect='1', arrows='1', fold='1', page='1',
            pageScale='1', pageWidth=str(width), pageHeight=str(height), math='0', shadow='0')
        self.root = E.SubElement(self.graph, 'root')
        E.SubElement(self.root, 'mxCell', id='0')
        E.SubElement(self.root, 'mxCell', id='1', parent='0')
        self.nodes, self.lines, self.labels = [], [], []

    def vertex(self, ident, value, x, y, w, h, style='', parent='1'):
        cell = E.SubElement(self.root, 'mxCell', id=ident, value=value,
            style=style, vertex='1', parent=parent)
        E.SubElement(cell, 'mxGeometry', x=str(x), y=str(y), width=str(w), height=str(h), **{'as':'geometry'})
        return cell

    def node(self, ident, label, x, y, w, h, kind='box'):
        if kind == 'actor':
            style='shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;fontFamily=Arial;fontSize=21;strokeColor=#000000;fillColor=#ffffff;'
        elif kind == 'ellipse':
            style='ellipse;whiteSpace=wrap;html=1;fontFamily=Arial;fontSize=22;strokeColor=#000000;fillColor=#ffffff;'
        else:
            style='rounded=0;whiteSpace=wrap;html=1;fontFamily=Arial;fontSize=20;strokeColor=#000000;fillColor=#ffffff;'
        self.vertex(ident, html.escape(label).replace('\n','<br>'), x,y,w,h,style)
        self.nodes.append((kind,x,y,w,h,label))

    def text(self, ident, label, x, y, w, h, size=20, bold=False):
        self.vertex(ident, html.escape(label).replace('\n','<br>'),x,y,w,h,
            f'text;html=1;whiteSpace=wrap;align=center;verticalAlign=middle;fontFamily=Arial;fontSize={size};fontStyle={1 if bold else 0};fontColor=#000000;')
        self.labels.append((label,x+w/2,y+h/2,size,bold))

    def edge(self, ident, source, target, path, source_card='', target_card='', label='', general=False):
        style='edgeStyle=none;html=1;rounded=0;endArrow=block;endFill=0;' if general else 'edgeStyle=none;html=1;rounded=0;endArrow=none;'
        style+='strokeColor=#333333;strokeWidth=1.3;fontColor=#000000;fontFamily=Arial;fontSize=17;labelBackgroundColor=#ffffff;'
        cell=E.SubElement(self.root,'mxCell',id=ident,value=label,style=style,
            edge='1',parent='1',source=source,target=target)
        geo=E.SubElement(cell,'mxGeometry',relative='1',**{'as':'geometry'})
        if len(path)>2:
            points=E.SubElement(geo,'Array',**{'as':'points'})
            for x,y in path[1:-1]:E.SubElement(points,'mxPoint',x=str(x),y=str(y))
        # Explicit ports ensure editable XML and the preview use the same endpoints.
        start=self.bounds(source);end=self.bounds(target)
        def port(point,box):
            x,y,w,h=box
            return ((point[0]-x)/w,(point[1]-y)/h)
        sx,sy=port(path[0],start);tx,ty=port(path[-1],end)
        cell.set('style',style+f'exitX={sx};exitY={sy};exitDx=0;exitDy=0;entryX={tx};entryY={ty};entryDx=0;entryDy=0;')
        self.lines.append((path,source_card,target_card,label,general))
        for suffix,value,relative,xoff,yoff in [('s',source_card,-.85,8,-12),('t',target_card,.85,8,-12)]:
            if value:
                item=E.SubElement(self.root,'mxCell',id=ident+'_'+suffix,value=value,
                    style='edgeLabel;html=1;align=center;verticalAlign=middle;resizable=0;points=[];fontFamily=Arial;fontSize=17;labelBackgroundColor=#ffffff;',
                    vertex='1',connectable='0',parent=ident)
                geom=E.SubElement(item,'mxGeometry',x=str(relative),y='0',relative='1',**{'as':'geometry'})
                E.SubElement(geom,'mxPoint',x=str(xoff),y=str(yoff),**{'as':'offset'})

    def bounds(self, ident):
        c=self.root.xpath('./mxCell[@id=$i]',i=ident)[0]
        g=c.find('mxGeometry')
        return tuple(float(g.get(k)) for k in ['x','y','width','height'])

    def render(self):
        scale=2
        image=Image.new('RGB',(self.width*scale,self.height*scale),'white')
        draw=ImageDraw.Draw(image)
        def point(p):return tuple(int(v*scale) for v in p)
        def text(label,x,y,size=20,bold=False,mono=False,anchor='mm'):
            draw.multiline_text(point((x,y)),label,font=font(size*scale,bold,mono),fill='black',anchor=anchor,align='center' if anchor=='mm' else 'left',spacing=3*scale)
        # Lines are behind all filled nodes, as in draw.io.
        for path,sc,tc,label,general in self.lines:
            draw.line([point(p) for p in path],fill='#333333',width=2*scale,joint='curve')
            if general:
                x,y=path[-1]
                px,py=path[-2];length=math.hypot(x-px,y-py)
                ux,uy=(x-px)/length,(y-py)/length
                bx,by=x-ux*15,y-uy*15
                draw.polygon([point((x,y)),point((bx-uy*7,by+ux*7)),point((bx+uy*7,by-ux*7))],fill='white',outline='black',width=scale)
            if sc:
                a,b=path[0],path[1];dx=b[0]-a[0];dy=b[1]-a[1]
                x=a[0]+(18 if dx>0 else -18 if dx<0 else 12);y=a[1]+(18 if dy>0 else -18 if dy<0 else -12)
                box=draw.textbbox(point((x,y)),sc,font=font(17*scale),anchor='mm');draw.rectangle(box,fill='white');text(sc,x,y,17)
            if tc:
                a,b=path[-1],path[-2];dx=b[0]-a[0];dy=b[1]-a[1]
                x=a[0]+(22 if dx>0 else -22 if dx<0 else 15);y=a[1]+(20 if dy>0 else -20 if dy<0 else -12)
                box=draw.textbbox(point((x,y)),tc,font=font(17*scale),anchor='mm');draw.rectangle(box,fill='white');text(tc,x,y,17)
            if label:
                a,b=max(zip(path,path[1:]),key=lambda pair:abs(pair[0][0]-pair[1][0]))
                x=(a[0]+b[0])/2;y=(a[1]+b[1])/2-12
                box=draw.textbbox(point((x,y)),label,font=font(17*scale),anchor='mm');draw.rectangle(box,fill='white');text(label,x,y,17)
        for kind,x,y,w,h,label in self.nodes:
            if kind=='actor':
                cx=x+w/2;cy=y+12
                draw.ellipse([point((cx-12,cy-12)),point((cx+12,cy+12))],fill='white',outline='black',width=2*scale)
                for a,b in [((cx,cy+12),(cx,cy+42)),((cx-21,cy+24),(cx+21,cy+24)),((cx,cy+42),(cx-20,cy+65)),((cx,cy+42),(cx+20,cy+65))]:draw.line([point(a),point(b)],fill='black',width=2*scale)
                text(label,cx,y+h+24,21)
            elif kind=='ellipse':
                draw.ellipse([point((x,y)),point((x+w,y+h))],fill='white',outline='black',width=2*scale)
                text(label,x+w/2,y+h/2,22)
            elif kind=='entity':
                title,fields=label
                draw.rectangle([point((x,y)),point((x+w,y+h))],fill='white',outline='black',width=scale)
                draw.rectangle([point((x,y)),point((x+w,y+30))],fill='#eeeeee',outline='black',width=scale)
                text(title,x+w/2,y+15,17,True,True)
                for k,field in enumerate(fields):text(field,x+8,y+31+k*22,20,False,True,'lt')
            else:
                # The system boundary must not hide the edges/nodes inside it.
                draw.rectangle([point((x,y)),point((x+w,y+h))],outline='black',width=2*scale)
        for label,x,y,size,bold in self.labels:text(label,x,y,size,bold)
        output=OUT/(self.name+'.png');image.save(output,dpi=(300,300))
        return output

    def save(self):
        E.indent(self.graph,space='  ')
        (OUT/(self.name+'.xml')).write_bytes(E.tostring(self.graph,encoding='UTF-8',xml_declaration=True))
        self.render()


def logical():
    d=Diagram('02_Логическая_схема',1030,1270)
    positions={
        'BANK_USERS':(50,40),'BANK_USER_ROLES':(385,40),'BANK_ROLES':(720,40),
        'BANK_CLIENTS':(50,300),'BANK_EMPLOYEES':(385,300),'BANK_AUDIT_LOG':(720,300),
        'BANK_ACCOUNTS':(50,630),'BANK_CURRENCIES':(385,630),'BANK_OPERATION_TYPES':(720,630),
        'BANK_CARDS':(50,970),'BANK_ACCOUNT_LIMITS':(385,970),'BANK_OPERATIONS':(720,970),
    }
    for name,title,fields in TABLES:
        x,y=positions[name];h=38+22*len(fields)
        d.vertex(name,name,x,y,250,h,
            'swimlane;html=1;startSize=30;horizontal=1;collapsible=0;rounded=0;fillColor=#eeeeee;swimlaneFillColor=#ffffff;strokeColor=#000000;fontColor=#000000;fontFamily=Consolas;fontSize=17;fontStyle=1;')
        labels=[]
        for i,(key,field,typ) in enumerate(fields):
            label=((key+' ') if key else '')+field;labels.append(label)
            row=d.vertex(name+'_'+field,html.escape(label),0,31+i*22,250,22,
                'text;html=1;align=left;verticalAlign=middle;spacingLeft=8;overflow=hidden;fontFamily=Consolas;fontSize=20;fontColor=#000000;',name)
            row.set('tooltip',typ)
        d.nodes.append(('entity',x,y,250,h,(name,labels)))
    B={name:d.bounds(name) for name,_,_ in TABLES}
    def side(name,where,f=.5):
        x,y,w,h=B[name]
        return {'left':(x,y+h*f),'right':(x+w,y+h*f),'top':(x+w*f,y),'bottom':(x+w*f,y+h)}[where]
    paths=[
      [side('BANK_USERS','right'),side('BANK_USER_ROLES','left')],
      [side('BANK_ROLES','left'),side('BANK_USER_ROLES','right')],
      [side('BANK_USERS','bottom'),side('BANK_CLIENTS','top')],
      [side('BANK_USERS','right',.8),(340,158),(340,260),(460,260),side('BANK_EMPLOYEES','top',.3)],
      [side('BANK_USERS','top',.9),(275,15),(1003,15),(1003,370),side('BANK_AUDIT_LOG','right',.3)],
      [side('BANK_CLIENTS','bottom'),side('BANK_ACCOUNTS','top')],
      [side('BANK_CURRENCIES','left',.4),side('BANK_ACCOUNTS','right',.13)],
      [side('BANK_EMPLOYEES','bottom',.3),(460,570),(260,570),side('BANK_ACCOUNTS','top',.84)],
      [side('BANK_ACCOUNTS','bottom',.3),side('BANK_CARDS','top',.3)],
      [side('BANK_EMPLOYEES','left',.7),(345,404),(345,1060),side('BANK_CARDS','right',.4)],
      [side('BANK_ACCOUNTS','bottom',.85),(262.5,920),(500,920),side('BANK_ACCOUNT_LIMITS','top',.46)],
      [side('BANK_ACCOUNTS','right',.65),(325,798),(325,850),(785,850),side('BANK_OPERATIONS','top',.26)],
      [side('BANK_ACCOUNTS','right',.8),(320,836),(320,888),(855,888),side('BANK_OPERATIONS','top',.54)],
      [side('BANK_OPERATION_TYPES','bottom',.85),(932.5,850),(957,850),side('BANK_OPERATIONS','top',.95)],
      [side('BANK_USERS','left',.4),(15,99),(15,1230),(1000,1230),(1000,1085),side('BANK_OPERATIONS','right',.5)],
    ]
    for i,((source,target,field,sc,tc),path) in enumerate(zip(RELATIONS,paths)):
        d.edge('relation_'+str(i),source,target,path,sc,tc,
            'списание' if field=='debit_account_id' else 'зачисление' if field=='credit_account_id' else '')
    d.text('legend','PK — первичный ключ; FK — внешний ключ; UK — уникальность;\nUK* — пара (initiator_user_id, request_id). ENC — шифротекст.',70,1235,880,35,17)
    return d


def usecases():
    d=Diagram('01_Варианты_использования',1100,1320)
    # The boundary is the first vertex, hence behind all other native shapes.
    d.node('system','',245,30,825,1215)
    d.text('system_title','Интернет-банк — база данных Oracle',320,38,670,45,25,True)
    actors=[('user','Пользователь',110,70),('admin','Администратор',110,345),
            ('employee','Сотрудник банка',110,645),('client','Клиент',110,985)]
    for ident,title,x,y in actors:d.node(ident,title,x,y,55,75,'actor')
    cases=[
      ('login','Пройти\nаутентификацию',325,100),
      ('read','Просмотреть\nразрешенные данные',735,100),
      ('admin_clients','Управлять учетными\nзаписями клиентов',325,280),
      ('admin_employees','Управлять учетными\nзаписями сотрудников',735,280),
      ('roles','Назначить или\nотозвать роли',325,420),
      ('reports','Сформировать\nсводные отчеты',735,420),
      ('accounts','Открыть или закрыть\nсчет и изменить\nего состояние',325,590),
      ('cards','Выпустить карту\nили изменить\nее состояние',735,590),
      ('limits','Проверить остатки\nи лимиты операций',325,730),
      ('register','Зарегистрироваться',325,910),
      ('transfer','Выполнить перевод\nмежду счетами',735,910),
      ('payment','Выполнить платеж',325,1050),
      ('statement','Просмотреть историю\nи получить выписку',735,1050),
    ]
    for ident,title,x,y in cases:d.node(ident,title,x,y,285,88,'ellipse')
    # Association waypoints avoid crossing use-case ellipses.
    specs=[
      ('user','login',[(130,110),(325,144)]),
      ('user','read',[(130,90),(210,90),(210,82),(880,82),(880,100)]),
      ('admin','admin_clients',[(130,375),(325,324)]),
      ('admin','admin_employees',[(130,355),(210,355),(210,252),(880,252),(880,280)]),
      ('admin','roles',[(130,395),(325,464)]),
      ('admin','reports',[(130,410),(210,410),(210,535),(880,535),(880,508)]),
      ('employee','accounts',[(130,670),(325,634)]),
      ('employee','cards',[(130,655),(210,655),(210,562),(880,562),(880,590)]),
      ('employee','limits',[(130,700),(325,774)]),
      ('client','register',[(130,1010),(325,954)]),
      ('client','transfer',[(130,995),(210,995),(210,882),(880,882),(880,910)]),
      ('client','payment',[(130,1035),(325,1094)]),
      ('client','statement',[(130,1050),(210,1050),(210,1165),(880,1165),(880,1138)]),
    ]
    for i,(source,target,path) in enumerate(specs):
        path[0]=(165,path[0][1])
        d.edge('association_'+str(i),source,target,path)
    for i,role in enumerate(['admin','employee','client']):
        _,_,_,y=[row for row in actors if row[0]==role][0]
        xroute=25+i*13
        xroute=10+i*8
        d.edge('general_'+role,role,'user',[(110,y+35),(xroute,y+35),(xroute,105),(110,105)],general=True)
    d.text('security_note','Все обращения, кроме регистрации, требуют аутентификации.\nПрава и принадлежность данных проверяются процедурами.\nШифрование и маскирование — внутренние механизмы, не отдельные акторы.',260,1255,800,60,20)
    return d


def main():
    diagrams=[usecases(),logical()]
    file=E.Element('mxfile',host='app.diagrams.net',agent='CourseProject',version='26.0.0')
    for i,d in enumerate(diagrams):
        d.save()
        page=E.SubElement(file,'diagram',id='page-'+str(i+1),name='Варианты использования' if i==0 else 'Логическая схема')
        page.append(E.fromstring(E.tostring(d.graph)))
    E.indent(file,space='  ')
    (OUT/'Интернет-банк.drawio').write_bytes(E.tostring(file,encoding='UTF-8',xml_declaration=True))
    print('Created two editable diagram pages, XML sources and PNG previews.')

if __name__=='__main__':main()
