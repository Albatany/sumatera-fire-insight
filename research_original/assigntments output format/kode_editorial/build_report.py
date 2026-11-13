from common import *
from audit_content import TABLE_SOURCE, FIG_SOURCE, LITERATURE
from docx.text.paragraph import Paragraph
from docx.table import Table
from docx.enum.text import WD_TAB_ALIGNMENT, WD_TAB_LEADER

OLD = Document(P/'Laporan_UTS_PenambanganData_Klasifikasi_F1E325063.docx')
BLOCKS=list(OLD.element.body)
META=json.loads((W/'report_blocks.json').read_text())
MAP={1:14,2:2,3:6,4:7,5:3,6:4,7:10,8:9,9:16,10:15,11:8,12:5,13:11,14:12,15:13,16:17,17:18,18:19}
d=Document(P/'Laporan_UTS_PenambanganData_Klasifikasi_F1E325063.docx')
for el in list(d.element.body):
 if el.tag!=qn('w:sectPr'):d.element.body.remove(el)
setup(d, 'UTS Penambangan Data | Salinan tinjauan penulis')
used=set();trace=[];where='';eqno=0

def h(s,lev=1,new=False):
 global where
 where=s
 if s.startswith(('2. ','3. ','4. ','5. ','6. ')):new=False
 return head(d,s,lev,new)
def add(i):
 global eqno
 b=META[i];el=copy.deepcopy(BLOCKS[i])
 if i in used:raise ValueError(('duplicate',i))
 used.add(i)
 # Mechanical changes only: cross-references and corrected source URL.
 for t in el.xpath('.//w:t'):
  if t.text:
   t.text=re.sub(r'Tabel (\d+)',lambda m:'Tabel '+str(MAP[int(m[1])]),t.text)
   t.text=t.text.replace('/services/SIG/Batas_Provinsi','/services/STIG/Batas_Provinsi')
   if i==107:t.text=t.text.replace('NASA FIRMS (n.d.)','NASA FIRMS (n.d.-b)')
 for x in el.xpath('.//w:pageBreakBefore|.//w:lastRenderedPageBreak|.//w:br[@w:type="page"]'):
  x.getparent().remove(x)
 if b['tag']=='p':
  p=Paragraph(el,d._body);pf=p.paragraph_format
  pf.space_after=Pt(6);pf.space_before=Pt(0);pf.line_spacing=1.15;pf.keep_with_next=False;pf.keep_together=False
  if b['images']:
   pf.keep_with_next=True;p.alignment=WD_ALIGN_PARAGRAPH.CENTER
  elif b['math']:
   pf.keep_together=True;p.alignment=WD_ALIGN_PARAGRAPH.CENTER
  elif 'Caption' in b['style']:
   p.style=d.styles['Caption'];pf.keep_with_next=True
  else:
   p.style=d.styles['Normal'];p.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
  if where=='Daftar pustaka' and 288<=i<=308:
   p.alignment=WD_ALIGN_PARAGRAPH.LEFT;pf.left_indent=Cm(.7);pf.first_line_indent=Cm(-.7);pf.keep_together=True
  for r in p.runs:
   if not b['math']:
    r.font.name='Times New Roman';r.font.size=Pt(10.5 if 'Caption' in b['style'] else 12)
    r.font.color.rgb=RGBColor(0,0,0)
 if b['tag']=='tbl':
  t=Table(el,d._body)
  # Retain original proportions when possible, within one text column.
  widths=[c.width.cm if c.width else 1 for c in t.columns]
  style_table(t,widths,10)
  if i==97:style_table(t,[2.3,1.9,5.1,5.29],10)
  if i==123:
   for c in t._tbl.xpath('.//w:tc'):
    for mar in c.xpath('./w:tcPr/w:tcMar'):
     for edge in ['top','bottom']:
      for e in mar.findall(qn('w:'+edge)):e.set(qn('w:w'),'40')
    for pe in c.xpath('./w:p'):Paragraph(pe,d._body).paragraph_format.space_after=Pt(0)
 d.element.body.insert(len(d.element.body)-1,el)
 trace.append({'old_block':b['id'],'old_text':b['text'],'new_section':where,'change':'crossrefs/URL/citation only' if any(x in b['text'] for x in ['Tabel ','/services/SIG/','NASA FIRMS (n.d.)']) else 'text preserved'})
 if b['math']:
  eqno+=1
  pp=para(d,f'Persamaan ({eqno}) • Bentuk asli dari laporan sumber.','Source')
  pp.alignment=WD_ALIGN_PARAGRAPH.RIGHT
 return el
def adds(*ids):
 for i in ids:add(i)
def rng(a,b):
 for i in range(a,b+1):
  bmeta=META[i]
  if not bmeta['style'] or 'Caption' in bmeta['style']:
   if bmeta['text'] or bmeta['images'] or bmeta['math']:add(i)
def tab(cap,idx):
 n=int(re.search(r'Tabel (\d+)',META[cap]['text'])[1]);new=MAP[n]
 para(d,f'Tabel {new} memuat '+META[cap]['text'].split(' ',2)[2].lower()+'.')
 add(cap);add(idx);source(d,TABLE_SOURCE[new])
def fig(cap,idx):
 n=int(re.search(r'Gambar (\d+)',META[cap]['text'])[1])
 add(cap);add(idx);source(d,FIG_SOURCE[n]+' Grafik asli, tidak dihitung atau digambar ulang pada revisi editorial.')
def review(rid,s):note(d,f'[TINJAU PENULIS {rid}] '+s)

para(d,'TECHNICAL REPORT UTS PENAMBANGAN DATA','Title')
para(d,TITLE,'Title')
p=para(d);p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.add_run().add_picture(str(P/'assets/UNIVERSITAS_JAMBI.png'),width=Cm(3.3))
para(d,NAME+'\nNIM '+NIM+'\nProgram Studi Informatika | Kelas R-002')
para(d,'Fakultas Sains dan Teknologi\nUniversitas Jambi\nUTS | Semester dan Tahun Akademik 2026/2027')
para(d,'Dosen pengampu\nUlfa Khaira S.Komp, M.Kom\nAkhiyar Waladi S.Komp')
para(d,'Salinan revisi editorial 5 November 2026 (WIB)')
review('R01','Judul ini merupakan usulan berdasarkan hasil aktual. Judul lama dipertahankan dalam peta revisi; penulis menetapkan judul akhir.')
review('R13','Naskah untuk peninjauan mahasiswa. Isi lama dipertahankan; catatan editorial, tabel bukti kajian, dan susunan baru belum merupakan persetujuan kepengarangan. Tidak dibuat identitas tim atau deklarasi peserta GEMASTIK.')
page(d);h('Abstrak');adds(15,16,18)
review('R02','Teks abstrak lama dipertahankan. Lengkapi konteks karhutla dan manfaat yang realistis dengan tulisan sendiri; pertimbangkan kata kunci clustering. Semua angka dan status classifier tetap.')
para(d,'Catatan penggunaan format: tugas ini merupakan UTS mata kuliah dengan acuan struktur GEMASTIK 2026, BAB III C, halaman cetak 24–26. Susunan delapan komponen digunakan; ketentuan pendaftaran dan identitas tim kompetisi tidak diterapkan. Format huruf/margin/spasi merupakan pilihan editorial yang dicatat dalam Peta Revisi.')
para(d,'Keterangan status: “terverifikasi” menunjuk hasil yang dapat dilacak ke berkas; “eksperimen” menunjuk clustering yang telah dijalankan; “rancangan” menunjuk klasifikasi yang belum dapat dilatih. Tidak ada eksperimen baru pada revisi ini.')
page(d);h('Daftar isi')
para(d,'Heading Word dapat digunakan melalui Navigation Pane. Nomor halaman berikut mengikuti PDF salinan revisi; perbarui setelah penulis mengubah isi.')
para(d,'Penomoran tabel/gambar berlaku untuk salinan ini. Sumber setiap ilustrasi mencantumkan jalur berkas pada paket penelitian lama. Peta nomor lama dan baru tersedia dalam Peta Revisi dan berkas jejak pemindahan.')
navigation=json.loads((W/'report_navigation.json').read_text()) if (W/'report_navigation.json').exists() else {}
def nav_line(label):
 p=para(d,label+'\t'+str(navigation.get(label,'—')),'Source')
 p.paragraph_format.tab_stops.add_tab_stop(Cm(14.45),WD_TAB_ALIGNMENT.RIGHT,WD_TAB_LEADER.DOTS)
 p.paragraph_format.line_spacing=1.0;p.paragraph_format.space_after=Pt(4)
 for r in p.runs:r.font.size=Pt(10.5)
for label in ['Abstrak','1. Pendahuluan','2. Kajian terkait','3. Solusi usulan','4. Hasil eksperimen dan pengujian','5. Analisis hasil eksperimen dan pengujian','6. Kesimpulan','Daftar pustaka','Lampiran A Kesesuaian materi kuliah','Lampiran B Perhitungan manual nyata','Lampiran C Bukti notebook dan paket','Lampiran D Audit terdahulu dan pembaruan status']:nav_line(label)
head(d,'Daftar tabel dan gambar')
for new,oldno in sorted((v,k) for k,v in MAP.items()):
 if new==2:nav_line('Tabel 1 Bukti untuk kajian terkait yang perlu ditinjau penulis')
 caps=[b for b in META if b['text'].startswith('Tabel '+str(oldno)+' ') and 'Caption' in b['style']]
 if caps:nav_line(re.sub(r'^Tabel \d+',f'Tabel {new}',caps[0]['text']))
for b in META:
 if b['text'].startswith('Gambar ') and 'Caption' in b['style']:nav_line(b['text'])

h('1. Pendahuluan',new=True)
h('1.1 Latar belakang',2);adds(85,86)
review('R04','Tambahkan konteks masyarakat/lingkungan berdasarkan sumber. WHO (n.d.) menjelaskan polusi asap dan gangguan layanan akibat wildfire. Ini rujukan konteks umum, bukan pengukuran dampak Sumatera dari dataset penelitian.')
h('1.2 Rumusan masalah',2);adds(88,89,90)
review('R03','Rumusan lama berfokus pada klasifikasi yang belum dapat dijalankan. Tambahkan pertanyaan clustering pendukung dengan kata-kata sendiri, sesuai eksperimen yang telah tersedia.')
h('1.3 Tujuan penelitian',2);add(91)
review('R03','Lengkapi tujuan deskriptif/pengelompokan yang sudah dilakukan. Jangan menyatakan tujuan prediksi tercapai.')
h('1.4 Manfaat penelitian',2);add(286)
review('R04','Tulis manfaat akademik dan kemungkinan dukungan pemantauan secara proporsional. Belum ada uji manfaat operasional atau dampak lapangan.')
h('1.5 Batasan penelitian',2);add(93)

h('2. Kajian terkait',new=True)
review('R05','Bagian ini merupakan kerangka bukti editorial. Laporan lama belum memiliki sintesis penelitian terdahulu. Mahasiswa perlu membaca sumber dan menulis perbandingan sendiri; baris dokumentasi/perangkat lunak tidak dianggap studi empiris setara.')
para(d,'Tabel 1 membedakan jenis sumber, informasi yang sudah tersedia, dan informasi yang belum diperiksa. Kolom hasil hanya memuat keterangan yang ditemukan pada sumber, tanpa menambahkan skor atau klaim unggul.')
para(d,'Tabel 1 Bukti untuk kajian terkait yang perlu ditinjau penulis','Caption')
fields=['Sumber dan jenis','Dataset/cakupan','Metode','Tujuan','Hasil yang dilaporkan sumber','Perbedaan dengan penelitian ini']
table(d,['Unsur','Birant dan Kut','Cakmak dan Plank','Giglio dkk.'],[[fields[i],*[r[i] for r in LITERATURE]] for i in range(6)],[2,4.2,4.2,4.2],10)
source(d,TABLE_SOURCE[1])
review('R05','Belum ada studi empiris prediksi lonjakan MODIS Sumatera yang ditelaah lengkap dalam referensi lama. Jangan mengisi bagian ini dengan penelitian atau angka rekaan. Pembandingan literatur yang terbatas tidak membuktikan kebaruan.')
add(314)

h('3. Solusi usulan',new=True)
h('3.1 Deskripsi solusi',2);add(190)
review('R07','Ketentuan format sekarang tersedia. Kesesuaian classification yang tertunda dan metode tambahan perlu dijelaskan kepada dosen; format GEMASTIK saja tidak membuktikan kewajiban mata kuliah telah terpenuhi.')
h('3.2 Sumber dan karakteristik dataset',2);tab(104,105);adds(107,108,140);tab(141,142);adds(144,145)
h('3.3 Audit dan kualitas data',2);adds(199,200,153);tab(148,149);add(152)
h('3.4 Tahapan preprocessing dan observabilitas',2);adds(147,151,112);tab(207,208);adds(210,211,212)
h('3.5 Metode penambangan data',2)
h('3.5.1 ST-DBSCAN dua ambang yang telah dijalankan',3);rng(214,222)
review('R07','Pertahankan nama varian dua ambang dan label metode tambahan. Penjelasan ini tidak boleh diubah menjadi klaim replikasi lengkap Birant–Kut.')
h('3.5.2 Target klasifikasi yang belum dapat difit',3);adds(111);rng(114,118);add(120)
review('R06','Istilah lonjakan masih perlu keputusan definisi oleh penulis: jumlah tinggi berbasis kuantil atau kenaikan terhadap histori. Belum ada ambang numerik/label sah yang boleh dilaporkan.')
h('3.6 Rancangan eksperimen dan evaluasi',2);tab(122,123);adds(125,126,128,129);tab(131,132);rng(134,138)
h('3.7 Perbedaan dari sumber terdahulu',2)
review('R05','Gunakan Tabel 1 untuk menulis perbedaan lingkup data, varian implementasi, audit label dan pemisahan periode. Perbedaan rancangan tidak otomatis merupakan kebaruan ilmiah. Bagian substantif ini belum diselesaikan otomatis.')

h('4. Hasil eksperimen dan pengujian',new=True)
h('4.1 Hasil audit kesiapan klasifikasi',2);tab(201,202);add(204);tab(175,176);add(178)
h('4.2 Eksplorasi deteksi historis',2);add(155);fig(156,157);fig(158,159);add(160)
h('4.3 Studi deskriptif tahun 2026 provisional',2)
review('R08','Heading lama “Studi Kasus Penerapan Model pada Data Hotspot Tahun 2026 (Provisional)” diganti untuk menghindari kesan classifier telah diterapkan. Kalimat hasil lama berikut tetap dipertahankan.')
add(163);tab(164,165);fig(167,168);adds(169,170);fig(172,173)
h('4.4 Hasil utama clustering',2);add(224);tab(225,226)
h('4.5 Sensitivitas parameter',2);para(d,'Gambar 5 dan Tabel 12 menyajikan keluaran sensitivitas eksperimen terdahulu.');fig(230,231);add(232);tab(233,234)
h('4.6 Validasi implementasi dan sensitivitas input',2);adds(238,239,240);tab(241,242)
h('4.7 Visualisasi geografi dan klaster',2);para(d,'Gambar 6 sampai Gambar 9 memperlihatkan keluaran pengelompokan. Interpretasinya dibahas pada bagian 5.');fig(246,247);fig(251,252);fig(253,254);fig(257,258)

h('5. Analisis hasil eksperimen dan pengujian',new=True)
h('5.1 Makna deteksi dan ketiadaan label',2);adds(205,174)
h('5.2 Makna klaster, noise dan sensitivitas',2);adds(228,236,244)
review('R09','Istilah ARI dan silhouette dapat dijelaskan lebih singkat dengan tulisan sendiri. Keduanya tidak boleh diberi arti precision, recall, F1 atau akurasi kebakaran.')
h('5.3 Interpretasi geografis dan efek rantai',2);adds(248,249,255,259)
h('5.4 Interpretasi tahun 2026',2);adds(260,261)
h('5.5 Keterbatasan dan kemungkinan penggunaan',2);adds(283,311,312,313)
h('5.6 Rencana perbaikan klasifikasi',2)
h('Jalur A Mempertahankan hitungan FIRMS',3);add(264)
h('Jalur B Mengubah target menjadi sel fire harian',3);adds(266,267,268,269)

h('6. Kesimpulan',new=True);adds(280,281,285)
review('R10','Kesimpulan asli dipertahankan. Setelah tujuan diperbaiki, pastikan kesimpulan menjawab tujuan audit dan clustering serta menyatakan tujuan prediksi belum tercapai. Tidak ada klaim classifier mengungguli baseline.')

h('Daftar pustaka',new=True)
for i in [288,289,290,291,292,293]:add(i)
p=reference(d,GUIDE_REF);p.alignment=WD_ALIGN_PARAGRAPH.LEFT;p.paragraph_format.line_spacing=1.15
for r in p.runs:r.font.size=Pt(12)
for i in [295,296,297,298,299,300,301,303,304,305,306,307,308]:add(i)
p=reference(d,WHO_REF);p.alignment=WD_ALIGN_PARAGRAPH.LEFT;p.paragraph_format.line_spacing=1.15
for r in p.runs:r.font.size=Pt(12)
note(d,'GEMASTIK 2026 dan WHO merupakan sumber tambahan revisi editorial. WHO dipakai sebagai petunjuk konteks pada catatan R04 dan panduan belajar. Sitasi n.d. mempertahankan tahun yang belum terverifikasi; tidak diubah menjadi tahun akses.')
add(310)

h('Lampiran A Kesesuaian materi kuliah',new=True);adds(95);tab(96,97);adds(99,101,102);tab(191,192);adds(194,195,196,197)
review('R12','Kalimat lama tentang belum adanya rubrik dibaca sesuai tanggal audit. Panduan format resmi sekarang tersedia; persetujuan algoritma tambahan dan penilaian LMS belum diverifikasi langsung.')
h('Lampiran B Perhitungan manual nyata',new=True);add(180);tab(181,182);rng(184,188);add(271);tab(272,273);adds(275,276)
h('Lampiran C Bukti notebook dan paket',new=True);adds(277,324,325,326)
note(d,'Revisi editorial 5 November 2026 membaca 30 sel notebook, termasuk 13 sel kode dengan output eksekusi tersimpan. Notebook tidak diubah atau dijalankan ulang. Sel 0 dan log lama masih menyebut rubrik belum tersedia; ini status historis, bukan informasi format terbaru.')
note(d,'Tata huruf DOCX memakai Times New Roman 12. Konversi PDF revisi memakai substitusi utama Liberation Serif dan font pendukung untuk simbol rumus. Informasi Nimbus Roman pada audit lama di Lampiran D merujuk PDF lama.')
h('Lampiran D Audit terdahulu dan pembaruan status',new=True)
note(d,'Tabel 18 dan Tabel 19 mempertahankan audit lama untuk jejak pemeriksaan. Status “Rubrik resmi BELUM MEMENUHI” berasal dari sebelum panduan terbaru tersedia. Pembaruan saat ini: format teknis terverifikasi, sedangkan kecukupan classification dan persetujuan metode tambahan tetap belum ditetapkan dosen.')
tab(316,317);add(319);tab(321,322);add(100)
review('R13','Penulis meninjau naskah, melengkapi kajian dan konteks, lalu memberi persetujuan akhir. Audit ini tidak mengesahkan keaslian tulisan atau kesesuaian seluruh syarat kepengarangan GEMASTIK.')

# Assert every substantive old paragraph/table/image/math survives, except the
# explicitly superseded legacy subtitle R162 (quoted in its review note).
expected={b['idx'] for b in META if b['idx']>=83 and b['tag']!='sectPr' and not any(s.startswith('Heading') for s in b['style']) and (b['text'] or b['images'] or b['math'])}
missing=expected-used-{162}
if missing:raise AssertionError(('unmapped substantive blocks',missing))
with (W/'jejak_pemindahan_report.csv').open('w',newline='') as f:
 wr=csv.DictWriter(f,fieldnames=['old_block','old_text','new_section','change']);wr.writeheader();wr.writerows(trace)
save(d,'Technical_Report_UTS_F1E325063_Rapih.docx')
(W/'preservasi_report.json').write_text(json.dumps({'substantive_source_blocks':len(expected),'retained_blocks':len(expected & used),'legacy_heading_replaced_and_quoted':['R162'],'missing':sorted(missing),'equations_numbered':eqno,'original_images_preserved':9,'old_table_mapping':MAP},indent=2))
print('report built',len(trace),'blocks',eqno,'equations')
