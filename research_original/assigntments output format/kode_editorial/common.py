from pathlib import Path
import json, csv, re, copy, hashlib
from docx import Document
from docx.shared import Cm, Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path('/workspace/scratch/d9d7a0d322b5')
P = ROOT/'deliverables/revisi/Paket_UTS_Klasifikasi_F1E325063'
W = ROOT/'work/gemastik_2026'
O = ROOT/'deliverables/gemastik_2026'
O.mkdir(exist_ok=True)
NAME = 'Muhammad Aziz Syah Dani'
NIM = 'F1E325063'
TITLE = 'Analisis Klaster Spasio Temporal Hotspot MODIS dan Audit Kesiapan Klasifikasi di Daratan Utama Sumatera Tahun 2015 sampai 2026'
GUIDE_URL = 'https://dikti.kemdiktisaintek.go.id/images/announcement/00a52b9f-18a3-45fb-825d-e7040d91fc5b.pdf'
GUIDE_REF = 'Direktorat Pembelajaran dan Kemahasiswaan. (2026). Panduan GEMASTIK 2026. Direktorat Jenderal Pendidikan Tinggi, Kementerian Pendidikan Tinggi, Sains, dan Teknologi. '+GUIDE_URL
WHO_REF = 'World Health Organization. (n.d.). Wildfires. https://www.who.int/health-topics/wildfires'
HUMANIZER = 'skill://flora-user-skills/root/.codex/skills/remote-skills/skill-6ae5925446b8819194655d768c2c65af/SKILL.md'

def read_csv(path):
    with (P/path).open(newline='') as f: return list(csv.DictReader(f))
def js(path): return json.loads((P/path).read_text())
def num(n): return f'{int(n):,}'.replace(',','.')
def para(doc,text='',style=None):
    return doc.add_paragraph(text,style)
def head(doc,text,level=1,break_before=False):
    p=doc.add_heading(text,level);p.paragraph_format.page_break_before=break_before;return p
def note(doc,text):
    p=para(doc,text,'Review Note');return p
def page(doc): doc.add_page_break()
def source(doc,text): return para(doc,'Sumber: '+text,'Source')
def table(doc,headers,rows,widths=None,font=10):
    t=doc.add_table(rows=1, cols=len(headers));t.alignment=WD_TABLE_ALIGNMENT.CENTER
    t.autofit=False
    for c,v in zip(t.rows[0].cells,headers): c.text=str(v)
    for row in rows:
        for c,v in zip(t.add_row().cells,row): c.text=str(v)
    style_table(t,widths,font)
    if len(t.rows)<=8 and sum(len(c.text) for r in t.rows for c in r.cells)<1800:
        for row in t.rows[:-1]:
            for c in row.cells:
                for p in c.paragraphs:p.paragraph_format.keep_with_next=True
    para(doc,'').paragraph_format.space_after=Pt(0)
    return t
def style_table(t,widths=None,font=10):
    total=14.59 # Letter width less original 4/3 cm margins
    if widths is None: widths=[total/len(t.columns)]*len(t.columns)
    if abs(sum(widths)-total)>.05: widths=[x*total/sum(widths) for x in widths]
    for col,w in zip(t.columns,widths): col.width=Cm(w)
    for i,row in enumerate(t.rows):
        trPr=row._tr.get_or_add_trPr()
        for x in trPr.findall(qn('w:trHeight')):trPr.remove(x)
        if trPr.find(qn('w:cantSplit')) is None:trPr.append(OxmlElement('w:cantSplit'))
        if i==0 and trPr.find(qn('w:tblHeader')) is None:trPr.append(OxmlElement('w:tblHeader'))
        for j,c in enumerate(row.cells):
            c.width=Cm(widths[j]); c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            pr=c._tc.get_or_add_tcPr()
            for x in pr.findall(qn('w:shd')):pr.remove(x)
            shd=OxmlElement('w:shd');shd.set(qn('w:fill'),'EDEDED' if i==0 else 'FFFFFF');pr.append(shd)
            mar=OxmlElement('w:tcMar')
            for edge,val in [('top',70),('bottom',70),('left',85),('right',85)]:
                e=OxmlElement('w:'+edge);e.set(qn('w:w'),str(val));e.set(qn('w:type'),'dxa');mar.append(e)
            pr.append(mar)
            for p in c.paragraphs:
                pf=p.paragraph_format;pf.line_spacing=1.07;pf.space_after=Pt(2);pf.space_before=Pt(0)
                pf.keep_with_next=False;pf.keep_together=True
                p.alignment=WD_ALIGN_PARAGRAPH.LEFT
                for r in p.runs:r.font.name='Times New Roman';r.font.size=Pt(font);r.font.color.rgb=RGBColor(0,0,0);r.bold=(i==0)
    pr=t._tbl.tblPr
    for old in pr.findall(qn('w:tblBorders')):pr.remove(old)
    borders=OxmlElement('w:tblBorders')
    for edge in ['top','left','bottom','right','insideH','insideV']:
        e=OxmlElement('w:'+edge);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');borders.append(e)
    pr.append(borders)
    return t
def setup(doc,header='F1E325063 | UTS Penambangan Data'):
    sec=doc.sections[0];sec.page_width=Inches(8.5);sec.page_height=Inches(11)
    sec.left_margin=Cm(4);sec.right_margin=Cm(3);sec.top_margin=Cm(2.7);sec.bottom_margin=Cm(2.7)
    sec.header_distance=Cm(1.2);sec.footer_distance=Cm(1.2)
    for st in doc.styles:
        if st.type==1:
            st.font.name='Times New Roman';st.font.color.rgb=RGBColor(0,0,0)
            if st.element.rPr is not None:
                rf=st.element.rPr.find(qn('w:rFonts'))
                if rf is not None:
                    for key in ['asciiTheme','hAnsiTheme','eastAsiaTheme','cstheme']:rf.attrib.pop(qn('w:'+key),None)
            for key in ['color','highlight']:
                if st.element.rPr is not None:
                    for x in st.element.rPr.findall(qn('w:'+key)):
                        if key=='color':x.attrib.clear();x.set(qn('w:val'),'000000')
            pp=st.paragraph_format;pp.page_break_before=False
            for x in st.element.xpath('./w:pPr/w:pBdr'):x.getparent().remove(x)
    normal=doc.styles['Normal'];normal.font.size=Pt(12)
    normal.paragraph_format.line_spacing=1.15
    normal.paragraph_format.space_after=Pt(6)
    normal.paragraph_format.widow_control=True
    normal.paragraph_format.keep_with_next=False
    for name,size in [('Title',18),('Subtitle',12),('Heading 1',14),('Heading 2',12),('Heading 3',12)]:
        st=doc.styles[name];st.font.size=Pt(size);st.font.bold=name!='Subtitle';st.font.color.rgb=RGBColor(0,0,0)
        st.paragraph_format.line_spacing=1.1;st.paragraph_format.space_before=Pt(12);st.paragraph_format.space_after=Pt(6)
        st.paragraph_format.keep_with_next=True
    for name,size,italic in [('Review Note',10.5,True),('Source',9.5,False),('Code',9,False),('Caption',10.5,False)]:
        if name not in doc.styles:doc.styles.add_style(name,1)
        st=doc.styles[name];st.font.name='Courier New' if name=='Code' else 'Times New Roman';st.font.size=Pt(9.5 if name=='Code' else size);st.font.italic=italic;st.font.color.rgb=RGBColor(0,0,0)
        st.paragraph_format.line_spacing=1.08;st.paragraph_format.space_after=Pt(5);st.paragraph_format.space_before=Pt(3)
        st.paragraph_format.keep_with_next=(name=='Caption');st.paragraph_format.keep_together=True
    for s in doc.sections:
        for part in [s.header,s.footer]:
            for el in list(part._element):part._element.remove(el)
        hp=s.header.add_paragraph(header);hp.style=doc.styles['Source']
        hp.paragraph_format.space_after=Pt(0)
        fp=s.footer.add_paragraph();fp.alignment=WD_ALIGN_PARAGRAPH.RIGHT
        fp.add_run('F1E325063 • ')
        fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');fp._p.append(fld)
        for r in fp.runs:r.font.size=Pt(9)
    doc.core_properties.author=NAME
    doc.core_properties.subject='UTS Penambangan Data; salinan revisi editorial 5 November 2026'
    doc.core_properties.keywords='MODIS, FIRMS, ST-DBSCAN, audit kesiapan klasifikasi, UTS'
    return doc
def newdoc(title,subtitle=None,logo=False,review=False):
    d=setup(Document())
    p=para(d,title,'Title')
    if logo:
        p=para(d);p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(str(P/'assets/UNIVERSITAS_JAMBI.png'),width=Cm(3.1))
    if subtitle:para(d,subtitle,'Subtitle')
    para(d,NAME+' | NIM '+NIM)
    para(d,'Informatika • Kelas R-002\nFakultas Sains dan Teknologi, Universitas Jambi\nMata kuliah Penambangan Data • UTS 2026/2027')
    para(d,'Dosen pengampu: Ulfa Khaira S.Komp, M.Kom dan Akhiyar Waladi S.Komp')
    para(d,'Revisi editorial 5 November 2026 (WIB)')
    if review:note(d,'SALINAN UNTUK PENINJAUAN PENULIS. Susunan dan tata letak diperbaiki; isi substantif lama dipertahankan. Penanda [TINJAU PENULIS] memerlukan keputusan dan penulisan mahasiswa. Dokumen ini belum merupakan naskah final yang telah disetujui penulis.')
    return d
def pic(d,path,caption,width=14.4):
    para(d,caption,'Caption')
    p=para(d);p.paragraph_format.keep_with_next=True;p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(path),width=Cm(width));return p
def reference(d,text):
    p=para(d,text);p.paragraph_format.left_indent=Cm(.7);p.paragraph_format.first_line_indent=Cm(-.7)
    p.paragraph_format.line_spacing=1.0;p.paragraph_format.space_after=Pt(8)
    for r in p.runs:r.font.size=Pt(10.5)
    return p
def clean_direct(d):
    # Keep authored math and images, remove decorative paragraph borders only.
    for el in d.element.body.xpath('.//w:pBdr'):el.getparent().remove(el)
    for p in d.paragraphs:
        p.paragraph_format.widow_control=True
        for r in p.runs:
            if r.font.color.type is not None:r.font.color.rgb=RGBColor(0,0,0)
    return d
def save(d,name):
    clean_direct(d);d.save(O/name);return O/name
