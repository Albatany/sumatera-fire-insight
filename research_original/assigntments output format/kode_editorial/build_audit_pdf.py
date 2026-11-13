from common import *
from audit_content import AUDIT, LAYOUT
from collections import Counter
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

for name,fn in [('Serif','LiberationSerif-Regular.ttf'),('SerifB','LiberationSerif-Bold.ttf'),('SerifI','LiberationSerif-Italic.ttf')]:
 pdfmetrics.registerFont(TTFont(name,'/usr/share/fonts/truetype/liberation/'+fn))
pdfmetrics.registerFontFamily('Serif',normal='Serif',bold='SerifB',italic='SerifI',boldItalic='SerifB')
styles={
 'body':ParagraphStyle('body',fontName='Serif',fontSize=11,leading=14.5,spaceAfter=7),
 'h1':ParagraphStyle('h1',fontName='SerifB',fontSize=14,leading=17,spaceBefore=10,spaceAfter=8,keepWithNext=True),
 'h2':ParagraphStyle('h2',fontName='SerifB',fontSize=11,leading=14,spaceBefore=7,spaceAfter=6,keepWithNext=True),
 'small':ParagraphStyle('small',fontName='Serif',fontSize=9.5,leading=12,spaceAfter=6),
 'title':ParagraphStyle('title',fontName='SerifB',fontSize=20,leading=24,spaceAfter=16),
}
story=[]
def p(s,style='body'):return Paragraph(escape(s),styles[style])
def add(s,style='body'):story.append(p(s,style))
def tb(headers,rows,widths):
 data=[[p(str(c),'small') for c in headers]]+[[p(str(c),'small') for c in row] for row in rows]
 t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#ededed')),('GRID',(0,0),(-1,-1),.35,colors.HexColor('#d9d9d9')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]));return t
add('Audit Kesesuaian Technical Report GEMASTIK 2026','title')
add(NAME+' | NIM '+NIM+'\nInformatika, R-002\nFakultas Sains dan Teknologi, Universitas Jambi')
add('Pemeriksaan editorial 5 November 2026 (WIB) terhadap laporan lama 35 halaman, panduan lama 17 halaman, notebook dan keluaran penelitian tersimpan. Tidak ada pemodelan atau analisis penelitian yang dijalankan ulang.')
add('Hasil pemeriksaan','h1')
add('Laporan memiliki bukti audit, analisis deskriptif dan ST-DBSCAN. Classification belum memenuhi syarat pengamatan dan belum dilatih. Struktur perlu memisahkan kajian terkait, solusi, hasil dan analisis. Sintesis literatur empiris serta manfaat dan kepengarangan masih memerlukan pekerjaan mahasiswa. Salinan rapi disiapkan untuk peninjauan, belum disahkan sebagai naskah final mandiri.')
counts=Counter(x[-1] for x in AUDIT)
story.append(tb(['Status temuan','Jumlah catatan'],[[x,counts[x]] for x in ['Sesuai','Perlu Revisi','Belum Didukung Data']],[330,138]))
add('Jumlah ini menghitung catatan editorial, bukan skor dosen atau metrik penelitian. Belum Didukung Data juga mencakup bukti literatur/kepengarangan yang belum cukup, bukan hanya data satelit.')
add('Ruang lingkup keputusan','h1')
add('Format GEMASTIK digunakan sebagai acuan UTS. Tidak dibuat pendaftaran kompetisi, nama/ID tim, deklarasi orisinalitas atau unggahan LMS. Jadwal 4 November dan tenggat 11 November pukul 23.59 berasal dari keterangan pengguna tentang LMS; zona waktu LMS belum diverifikasi langsung.')
story.append(PageBreak());add('1 Acuan resmi dan penerapannya','h1')
add('Panduan resmi BAB III C, halaman cetak 24–26, dibaca dari PDF cadangan pada domain kementerian. Pada PDF 109 halaman, bagian tersebut berada pada halaman berkas 28–30. Tautan utama tidak dapat dibaca melalui alat akses yang digunakan; isinya tidak diasumsikan berbeda atau sama tanpa bukti tambahan.')
add('Delapan komponen wajib dipetakan pada judul, abstrak, pendahuluan, kajian terkait, solusi usulan, hasil eksperimen/pengujian, analisis hasil, dan kesimpulan. Pustaka serta lampiran melengkapi keterlacakan. Bagian C tidak menetapkan font, margin, panjang halaman atau template IEEE; ketentuan cabang lain tidak diterapkan otomatis.')
add('Panduan membolehkan alat bantu penelitian termasuk GenAI, tetapi menyatakan “Technical report bukan hasil dari Generative AI” (Direktorat Pembelajaran dan Kemahasiswaan, 2026, hlm. 25). Karena itu revisi mempertahankan substansi sumber dan memberi catatan penulis. Perubahan tata letak tidak mengesahkan kepengarangan; mahasiswa tetap perlu menyelesaikan, memverifikasi dan menyetujui naskah.')
story.append(tb(['Unsur penilaian penyisihan pada panduan','Bobot panduan'],[[s,'20%'] for s in ['Keaslian','Kebaruan dataset atau metode','Manfaat','Kejelasan tulisan','Kelengkapan laporan']],[350,118]))
add('Bobot di atas adalah rubrik kompetisi pada halaman cetak 26. Belum ada bukti dosen menyalin bobot yang sama untuk UTS. Audit tidak memberi skor keaslian, kebaruan, manfaat atau nilai mata kuliah.')
story.append(PageBreak());add('2 Pemetaan delapan komponen','h1')
story.append(tb(['Komponen','Lokasi salinan','Status substansi'],[
 ['Judul','Sampul; R01','Usulan untuk ditetapkan penulis'],['Abstrak','Sesudah sampul; R02','Teks/angka lama dipertahankan; konteks perlu tinjauan'],['Pendahuluan','1.1–1.5; R03/R04','Struktur lengkap; manfaat/tujuan perlu tulisan penulis'],['Kajian terkait','Bagian 2; R05','Kerangka bukti ada; sintesis empiris belum lengkap'],['Solusi usulan','3.1–3.7','Metode aktual/rencana dipisahkan; perbedaan perlu penulis'],['Hasil eksperimen','Bagian 4','Audit/EDA/clustering aktual; classifier belum dieksekusi'],['Analisis hasil','Bagian 5','Paragraf asli dan keterbatasan dipertahankan'],['Kesimpulan','Bagian 6; R10','Hasil aktual; classification tetap tertunda']],[100,140,228]))
add('Tercakup secara struktur tidak berarti seluruh komponen sudah memenuhi kedalaman substansi. Khusus kajian terkait dan 3.7, ruang penyelesaian penulis sengaja terlihat agar tidak disamarkan oleh format rapi.')
add('3 Matriks pemeriksaan laporan lama','h1')
add('Setiap entri berikut merupakan satu rekaman matriks dengan kolom tetap: bagian lama, kesesuaian, kualitas penjelasan, kelengkapan bukti, tata letak, referensi, rekomendasi dan status. Tata letak vertikal menjaga keterbacaan pada halaman potret. Nomor halaman merujuk PDF lama.')
fields=['Bagian laporan lama','Kesesuaian GEMASTIK','Kualitas penjelasan','Kelengkapan bukti','Masalah tata letak','Masalah referensi','Rekomendasi']
for rec in AUDIT:
 code,*vals,status=rec
 data=[[p(k,'small'),p(v,'small')] for k,v in zip(fields,vals)]
 t=Table(data,colWidths=[118,350],hAlign='LEFT')
 t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.35,colors.HexColor('#d9d9d9')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
 story.append(KeepTogether([p(code+' | '+status,'h2'),t,Spacer(1,12)]))
story.append(PageBreak());add('4 Pencocokan angka dan bukti','h1')
story.append(tb(['Klaim yang dicocokkan','Sumber hasil lama'],[
 ['13 CSV; 630.384 baris mentah','clustering/audit_ulang_ringkas.json dan audit_ulang_13_csv.csv'],['154.184 deteksi terpilih','hasil/audit_paket_final.json; data_sesudah_diolah.csv'],['34.568 kandidat; 23.809 tanpa rekaman','hasil/status_eksekusi.json; keputusan_classification.json'],['3.678 klaster; 74.383 noise; sekitar 48,24%','clustering/ringkasan_eksperimen.json'],['73.129 core; 6.672 border','ringkasan_eksperimen.json; hasil_utama_per_strata.csv'],['27 konfigurasi; noise 28,72%–94,99%','sensitivitas_27_skenario.csv; pembulatan laporan lama'],['4.268 / 4.203 / 20.252 pada jendela setara','hasil/tabel/perbandingan_1Jan_30Okt.csv'],['ARI sampel 1; permutasi 0,999810','clustering/validasi_implementasi.json'],['Tidak ada classifier atau kuantil label yang difit','clustering/keputusan_classification.json'],['30 sel, 13 kode, In[1]–In[13] tersimpan','Notebook sumber; validasi_notebook.json']],[234,234]))
add('Pencocokan memakai file hasil dan output tersimpan. Keberhasilan log notebook terdahulu dibedakan dari uji antarmuka Colab/VS Code yang belum dilakukan. Tanggal/cutoff data tidak diperpanjang mengikuti tanggal revisi dokumen.')
add('5 Tata letak bahasa dan jejak perubahan','h1')
add('DOCX menggunakan Times New Roman 12, Letter, margin kiri 4 cm/kanan 3 cm/atas-bawah 2,7 cm dan spasi 1,15 sebagai pilihan editorial. PDF revisi memakai substitusi utama Liberation Serif serta font pendukung simbol. Logo UNJA dan grafik asli dipertahankan. Header tabel berulang, baris tidak dipotong, sumber/nomor konsisten dan rumus OMML tetap dapat diedit.')
add('Humanizer dipakai untuk menilai kejelasan, pengulangan dan kepadatan istilah. Saran ditulis sebagai R01–R13 disertai alasan serta tindakan mahasiswa. Tidak dilakukan penilaian deteksi AI atau penulisan ulang seluruh isi. Jejak pemindahan blok sumber dan perbandingan hash disimpan sebagai lampiran digital.')
add('6 Hal yang perlu diselesaikan penulis','h1')
add('Tentukan judul akhir; lengkapi konteks/manfaat dengan sumber; rumuskan tujuan clustering pendukung; baca dan sintesis kajian terkait; jelaskan perbedaan solusi tanpa klaim kebaruan berlebihan; diskusikan kecukupan classification dan metode tambahan dengan dosen; tinjau seluruh naskah serta akui bantuan sesuai ketentuan. Jangan mengisi bagian kosong dengan metrik prediksi yang belum tersedia.')
story.append(PageBreak());add('Sumber pemeriksaan','h1')
for s in [GUIDE_REF,WHO_REF,'Badan Informasi Geospasial. (n.d.). Batas administrasi provinsi. https://geoservices.big.go.id/gis/rest/services/STIG/Batas_Provinsi/MapServer/0','Berkas penelitian sumber: laporan/panduan versi 1, notebook dengan output tersimpan, manifest, tabel CSV/JSON, sembilan gambar report dan dua grafik tambahan. Bibliografi sumber lengkap dipertahankan pada report.']:add(s,'small')
def page_frame(c,doc):
 c.setFont('Serif',9);c.drawString(72,757,'F1E325063 | Audit editorial UTS Penambangan Data');c.drawRightString(540,36,str(doc.page))
doc=SimpleDocTemplate(str(O/'Audit_Kesesuaian_Technical_Report_GEMASTIK_2026.pdf'),pagesize=(612,792),leftMargin=78,rightMargin=66,topMargin=70,bottomMargin=62,title='Audit Kesesuaian Technical Report GEMASTIK 2026',author=NAME)
doc.build(story,onFirstPage=page_frame,onLaterPages=page_frame)
with (W/'matriks_audit.csv').open('w',newline='') as f:
 wr=csv.writer(f);wr.writerow(['id',*fields,'status']);wr.writerows(AUDIT)
print('audit PDF built',dict(counts))
