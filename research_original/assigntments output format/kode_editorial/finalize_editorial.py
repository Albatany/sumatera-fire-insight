"""Package editorial copies; never execute or write research inputs."""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import csv, hashlib, json, re, shutil, zipfile, sys, unicodedata
import fitz
try:
    import nbformat
except ImportError:
    nbformat = None
from lxml import etree

ROOT = Path('/workspace/scratch/d9d7a0d322b5')
W = ROOT / 'work/gemastik_2026'
O = ROOT / 'deliverables/gemastik_2026'
P = ROOT / 'deliverables/revisi/Paket_UTS_Klasifikasi_F1E325063'
META = O / 'jejak_revisi'
META.mkdir(exist_ok=True)

def dump(p, x): p.write_text(json.dumps(x, ensure_ascii=False, indent=2), encoding='utf-8')
def read(p): return json.loads(p.read_text())
def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''): h.update(block)
    return h.hexdigest()
def rows(p):
    with p.open(newline='', encoding='utf-8-sig') as f: return list(csv.DictReader(f))
def norm(t): return re.sub(r'\s+', ' ', unicodedata.normalize('NFKC', t)).strip()
def xml(p):
    with zipfile.ZipFile(p) as z: return etree.fromstring(z.read('word/document.xml'))
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math'}

def prepare():
    shutil.copy2(W/'final_report/Technical_Report_UTS_F1E325063_Rapih.pdf', O/'Technical_Report_UTS_F1E325063_Rapih.pdf')
    shutil.copy2(W/'release_guide/Panduan_Pemahaman_Penelitian_F1E325063.pdf', O/'Panduan_Pemahaman_Penelitian_F1E325063.pdf')
    guide = fitz.open(O/'Panduan_Pemahaman_Penelitian_F1E325063.pdf')
    assert len(guide) == 50
    assert 'Bagian H Panduan presentasi dan tanya jawab' in norm(guide[34].get_text())
    presentation = fitz.open()
    presentation.insert_pdf(guide, from_page=34, to_page=len(guide)-1)
    body_identical = []
    for i, p in enumerate(presentation):
        p.add_redact_annot(fitz.Rect(0, 730, p.rect.width, p.rect.height), fill=(1,1,1))
        p.apply_redactions(images=0)
        p.insert_textbox(fitz.Rect(113,738,527,762), f'F1E325063 | {i+1}', fontname='tiro', fontsize=10, align=2)
        clip = fitz.Rect(0,0,p.rect.width,728)
        body_identical.append(p.get_pixmap(clip=clip).samples == guide[i+34].get_pixmap(clip=clip).samples)
    assert all(body_identical)
    presentation.set_metadata({'title':'Panduan Presentasi dan Tanya Jawab F1E325063',
                               'author':'Muhammad Aziz Syah Dani',
                               'subject':'Bahan latihan; bagian H panduan pemahaman. Classification belum dilatih.'})
    presentation.save(O/'Panduan_Presentasi_dan_Tanya_Jawab_F1E325063.pdf', garbage=4, deflate=True)
    q = W/'presentation_preview'; q.mkdir(exist_ok=True)
    for i in [0,4,len(presentation)-1]:
        presentation[i].get_pixmap(matrix=fitz.Matrix(4/3,4/3)).save(q/f'page-{i+1}.png')

    before = read(W/'hash_sumber_sebelum.json')
    after = {name:sha(P/name) for name in before}
    changed = [name for name in before if before[name] != after[name]]
    assert not changed, changed
    dump(META/'hash_sumber_sebelum.json', before)
    dump(META/'hash_sumber_sesudah.json', after)

    nbp = P/'UTS_PenambanganData_Klasifikasi_F1E325063.ipynb'
    nb = read(nbp)
    schema_check='NOT_REPEATED_NBFORMAT_UNAVAILABLE; PRIOR_LOG_PASS_RETAINED'
    if nbformat is not None:
        nbformat.validate(nb)
        schema_check='PASS_IN_MEMORY_NO_WRITE'
    code = [c for c in nb['cells'] if c['cell_type'] == 'code']
    assert len(nb['cells']) == 30 and len(code) == 13
    assert [c['execution_count'] for c in code] == list(range(1,14))
    errors = [o for c in code for o in c['outputs'] if o['output_type'] == 'error']
    assert not errors

    checks = []
    def check(name, actual, expected, evidence):
        assert actual == expected, (name, actual, expected)
        checks.append({'claim':name,'value':actual,'evidence':evidence,'status':'MATCH'})
    audit = read(P/'clustering/audit_ulang_ringkas.json')
    cluster = read(P/'clustering/ringkasan_eksperimen.json')
    gate = read(P/'clustering/keputusan_classification.json')
    status = read(P/'hasil/status_eksekusi.json')
    check('CSV mentah', audit['csv_count'], 13, 'clustering/audit_ulang_ringkas.json')
    check('Baris mentah', audit['raw_rows'], 630384, 'clustering/audit_ulang_ringkas.json')
    check('Deteksi terpilih', cluster['n'], 154184, 'clustering/ringkasan_eksperimen.json')
    for k,v in [('clusters',3678),('noise',74383),('core',73129),('border',6672),('configurations',27)]:
        check(k, cluster[k], v, 'clustering/ringkasan_eksperimen.json')
    for k,v in [('candidate_rows',34568),('region_days_without_records',23809),('model_fitted',False),('target_quantiles_fitted',False),('negative_labels_created',0),('test2025_evaluated',False)]:
        check(k, gate[k], v, 'clustering/keputusan_classification.json')
    check('Label sah',status['eligible_model_rows'],0,'hasil/status_eksekusi.json')
    check('Hash arsip mentah',sha(P/'data_sebelum_diolah/NASA_MODIS_2015_2026_RAW.zip'),audit['raw_zip_sha256'],'clustering/audit_ulang_ringkas.json')
    check('Hash hasil pengolahan',sha(P/'hasil/data_sesudah_diolah.csv'),audit['processed_csv_sha256'],'clustering/audit_ulang_ringkas.json')
    manifest = rows(P/'hasil/manifest_sumber.csv')
    check('Jumlah baris menurut manifest',sum(int(x['rows']) for x in manifest),630384,'hasil/manifest_sumber.csv')
    versions=Counter()
    for x in manifest: versions.update(json.loads(x['version_values']))
    check('Versi literal',dict(versions),{'6.03':397657,'61.03':141030,'6.1NRT':91697},'hasil/manifest_sumber.csv')
    comparison = {x['year']:int(x['detections']) for x in rows(P/'hasil/tabel/perbandingan_1Jan_30Okt.csv')}
    check('Jendela sebanding 1 Januari–30 Oktober',comparison,{'2024':4268,'2025':4203,'2026':20252},'hasil/tabel/perbandingan_1Jan_30Okt.csv')
    sensitivity = rows(P/'clustering/sensitivitas_27_skenario.csv')
    check('Baris tabel sensitivitas',len(sensitivity),27,'clustering/sensitivitas_27_skenario.csv')
    sensitivity_range = [min(float(x['noise_percent']) for x in sensitivity),max(float(x['noise_percent']) for x in sensitivity)]
    checks.append({'claim':'Rentang noise sensitivitas (%)','value':sensitivity_range,'evidence':'clustering/sensitivitas_27_skenario.csv','status':'READ_EXISTING_OUTPUT'})
    valid=read(P/'clustering/validasi_implementasi.json')
    check('ARI dense/sparse',valid['dense_vs_sparse_ARI'],1.0,'clustering/validasi_implementasi.json')
    check('ARI pembanding upstream',valid['upstream_reference_ARI'],1.0,'clustering/validasi_implementasi.json')
    dump(META/'pencocokan_hasil.json',checks)

    olddoc = P/'Laporan_UTS_PenambanganData_Klasifikasi_F1E325063.docx'
    newdoc = O/'Technical_Report_UTS_F1E325063_Rapih.docx'
    oldxml,newxml=xml(olddoc),xml(newdoc)
    oldbody=oldxml.find('w:body',NS);newbody=newxml.find('w:body',NS)
    def txt(el): return norm(''.join(el.xpath('.//w:t/text()',namespaces=NS)))
    newtexts = [txt(e) for e in newbody]
    mapping = read(W/'preservasi_report.json')['old_table_mapping']
    trace=rows(W/'jejak_pemindahan_report.csv')
    missing=[]
    for row in trace:
        idx=int(row['old_block'][1:]); s=txt(oldbody[idx])
        s=re.sub(r'Tabel (\d+)',lambda m:'Tabel '+str(mapping[m[1]]),s)
        s=s.replace('/services/SIG/Batas_Provinsi','/services/STIG/Batas_Provinsi')
        if idx==107:s=s.replace('NASA FIRMS (n.d.)','NASA FIRMS (n.d.-b)')
        if s and s not in newtexts: missing.append(row['old_block'])
    assert not missing, missing
    def mathtexts(root):
        return [etree.tostring(e,method='c14n') for e in root.xpath('.//m:oMath',namespaces=NS)]
    # Native equations are copied verbatim. Their canonical XML includes stable namespaces.
    oldmath=mathtexts(oldxml);newmath=mathtexts(newxml)
    assert Counter(oldmath)==Counter(newmath) and len(oldmath)==9
    with zipfile.ZipFile(olddoc) as a,zipfile.ZipFile(newdoc) as b:
        media=[n for n in a.namelist() if n.startswith('word/media/')]
        assert all(a.read(n)==b.read(n) for n in media)
    preservation = {'source_hashes_checked':len(before),'changed_source_files':changed,
                    'trace_entries':len(trace),'missing_relocated_text_blocks':missing,
                    'equations_native_xml_identical':len(oldmath),'embedded_media_byte_identical':len(media),
                    'research_notebook_sha256':sha(nbp),'research_notebook_modified':False,
                    'research_rerun_in_revision':False,'new_research_models_or_metrics':False}
    dump(META/'preservasi_final.json',preservation)

    navigation={}
    for filename, navfile in [('Technical_Report_UTS_F1E325063_Rapih.pdf','report_navigation.json'),('Panduan_Pemahaman_Penelitian_F1E325063.pdf','guide_navigation.json')]:
        doc=fitz.open(O/filename); nav=read(W/navfile); failed=[]
        for label, pg in nav.items():
            if norm(label) not in norm(doc[pg-1].get_text()): failed.append([label,pg])
        assert not failed, failed
        navigation[filename]={'entries':len(nav),'mismatches':failed}
    dump(META/'navigasi_terverifikasi.json',navigation)

    pdf_stats=[]
    for f in sorted(O.glob('*.pdf')):
        doc=fitz.open(f); blanks=[];outside=[]; fonts=set()
        for i,p in enumerate(doc):
            if not p.get_text().strip():blanks.append(i+1)
            for word in p.get_text('words'):
                x0,y0,x1,y1=word[:4]
                if x0<0 or y0<0 or x1>p.rect.width+.5 or y1>p.rect.height+.5: outside.append(i+1)
            for entry in p.get_fonts():fonts.add(entry[3])
        assert not blanks and not outside,(f.name,blanks,outside)
        pdf_stats.append({'file':f.name,'pages':len(doc),'empty_pages':blanks,'out_of_page_text':outside,'fonts':sorted(fonts)})
    report = {'revision_date_wib':'2026-11-05','checked_utc':datetime.now(timezone.utc).isoformat(),
              'scope':'Editorial, structure, layout and learning guide; no research execution',
              'preservation':preservation,'scientific_claim_checks':len(checks),'pdfs':pdf_stats,
              'notebook':{'nbformat_validate_in_memory':schema_check,'cells':len(nb['cells']),'code_cells':len(code),'stored_execution_counts':[c['execution_count'] for c in code],'stored_errors':len(errors),'rerun':False,'previous_run_evidence':read(P/'clustering/validasi_notebook.json'),'native_colab_vscode_test':'NOT_PERFORMED'},
              'audit_old_report_status_counts':dict(Counter(x['status'] for x in rows(W/'matriks_audit.csv'))),
              'guide_inventory':read(W/'panduan_inventory.json'),
              'presentation':{'source_pages':'35–50 of revised learning guide','pages':len(presentation),'content_above_footer_pixel_identical':all(body_identical)},
              'visual_qa':'PENDING_PRESENTATION_FOOTER_CHECK',
              'not_final_for_submission':['Student review R01–R13','Related-work synthesis and section 3.7','Teacher determination of UTS method conformity','Authorship and acknowledgement decision','LMS timing confirmation'],
              'classification_status':'NOT_FITTED_MISSING_VALID_TARGET','clustering_status':'PREVIOUS_EXECUTION_PRESERVED',
              'cutoff_utc':'2026-10-30T23:59:59Z','last_retained_observation_utc':status['study_2026_max_observed_utc'],
              'unresolved_version':'61.03'}
    dump(META/'audit_final_editorial.json',report)
    print(json.dumps({'pages':[{k:x[k] for k in ['file','pages']} for x in pdf_stats],'preservation':preservation,'checks':len(checks)},ensure_ascii=False,indent=2))

def package():
    a=read(META/'audit_final_editorial.json')
    a['visual_qa']={'report':'35/35 pages inspected','revision_map':'7/7 pages inspected',
                    'audit':'12/12 pages inspected','learning_guide':'50/50; 48 content matches to inspected version plus revised pages 38 and 49 inspected',
                    'presentation':'All body content pixel-identical to inspected guide; renumbered footer previews inspected'}
    dump(META/'audit_final_editorial.json',a)
    checklist='''# Checklist Final UTS F1E325063

Revisi editorial: 5 November 2026 (WIB). Status: **siap ditinjau mahasiswa; belum dinyatakan final untuk pengumpulan**.

Muhammad Aziz Syah Dani · F1E325063 · Informatika · Fakultas Sains dan Teknologi · Universitas Jambi · R-002 · Penambangan Data · UTS 2026/2027.

## Pemeriksaan akhir

| Pemeriksaan | Status | Bukti dan batas pemeriksaan |
|---|---|---|
| Delapan komponen GEMASTIK | Tercakup secara struktur | Judul, abstrak, pendahuluan, kajian terkait, solusi usulan, hasil, analisis, kesimpulan. Kajian terkait dan 3.7 masih memerlukan penulisan mahasiswa. |
| Konteks tugas | Sesuai | UTS mata kuliah dengan acuan format GEMASTIK; bukan pendaftaran lomba dan tanpa identitas tim rekaan. |
| Sumber resmi format | Terverifikasi | PDF resmi cadangan, BAB III C, halaman cetak 24–26; halaman fisik 28–30. Bukan asumsi template IEEE. |
| Identitas dan logo | Sesuai | Nama, NIM, program, fakultas, universitas, kelas, mata kuliah, dosen, UTS dan semester diperiksa; logo UNJA asli dipertahankan. |
| Data dan file lama | Tidak berubah | SHA-256 133 berkas sumber sama sebelum/sesudah. Arsip CSV, notebook, hasil, laporan dan panduan lama dipertahankan. |
| Substansi laporan lama | Dipertahankan | 185 catatan pemindahan blok; sembilan persamaan native identik; gambar/logo tertanam byte-identik. Heading lama kasus 2026 dicatat sebelum diperbaiki. |
| Konsistensi angka | Cocok dengan hasil tersimpan | 13 CSV, 630.384 baris mentah, 154.184 deteksi terpilih; jejak verifikasi dalam pencocokan_hasil.json. Tidak ada pemodelan ulang. |
| Clustering | Hasil aktual lama dipertahankan | ST-DBSCAN dua ambang: 3.678 klaster, 74.383 noise; 27 konfigurasi sensitivitas. Bukan hitungan kejadian atau luas kebakaran. |
| Classification | BELUM MEMENUHI | 34.568 kandidat wilayah-hari; 23.809 tanpa rekaman tetap missing. Nol label sah; classifier/ambang numerik/metrik prediksi belum dihitung. |
| Versi MODIS | Sebagian belum tuntas | 6.03, 61.03, 6.1NRT dipertahankan literal. 61.03 belum terverifikasi; nama file tidak mengesahkan koleksi. |
| Studi 2026 | Deskriptif, provisional | Cutoff tetap 30 Oktober 2026 23:59:59 UTC. Observasi terakhir terpilih 30 Oktober 01:58 UTC; tidak membuktikan cakupan satu hari penuh. Status archive/NRT dibedakan. |
| Kebocoran data | Rancangan dijelaskan; belum diuji model | Split rencana 2015–2023/2024/2025/2026, syarat QA dan available_at dipertahankan. Tidak ada klaim classifier bebas leakage yang telah dievaluasi. |
| Notebook | Berkas asli tidak diubah/dijalankan ulang | JSON dan output tersimpan diperiksa: 30 sel, 13 sel kode dengan In[1]–In[13], tanpa error tersimpan. Log lama mencatat nbformat.validate PASS dan Run All memakai IPython in-process. Validator nbformat tidak tersedia pada lingkungan editorial akhir sehingga validasi skema tidak diulang; uji native Colab/VS Code belum dilakukan. |
| Referensi dan hasil | Tidak ditambah secara fiktif | Perbaikan tautan BIG dan sitasi NASA dicatat; GEMASTIK dan WHO sumber tambahan. Kajian Birant–Kut dibatasi bukti abstrak/metadata yang telah dibaca. |
| Tata letak DOCX/PDF | Diperiksa | Report 35 halaman; peta revisi 7; audit 12; panduan belajar 50; presentasi 16. Seluruh halaman diperiksa atau dicocokkan piksel dengan halaman yang telah diperiksa. Tidak ada halaman kosong/teks di luar batas halaman. |
| Navigasi | Cocok dengan PDF revisi | 40 rujukan halaman report dan delapan bagian panduan diperiksa. Nomor dapat berubah setelah penyuntingan di Word. |
| Gaya halaman | Pilihan editorial | Letter, TNR 12, spasi 1,15; kiri 4 cm, kanan 3 cm, atas/bawah 2,7 cm. PDF memakai substitusi utama Liberation Serif. Bukan aturan resmi GEMASTIK. |
| Panduan pemahaman | Lengkap sebagai bahan belajar | A–H; delapan proses; 11 grafik dan 19 tabel; semua 30 sel notebook; sembilan slide/naskah 875 kata; 40 tanya jawab; 58 istilah; sembilan pertanyaan terbuka. Durasi presentasi 7–10 menit perlu latihan, bukan hasil pengukuran. |
| Peran bantuan AI | Dinyatakan | Humanizer dipakai untuk kejelasan dan catatan editorial; tidak ada sertifikat keaslian atau klaim naskah karya mandiri. |
| Pengiriman | Tidak dilakukan | Tidak diunggah ke LMS, dipublikasikan atau dikirim kepada dosen. |

## BELUM MEMENUHI dan tindakan mahasiswa

| Item | Tindakan konkret |
|---|---|
| R01–R04: judul, abstrak, tujuan dan manfaat | Tetapkan judul yang sesuai audit/clustering; pertahankan status classification tertunda; tulis konteks dan manfaat dalam pemahaman sendiri dengan sumber sah. |
| R05 dan bagian 3.7 | Baca sumber terkait yang relevan; lengkapi tabel perbandingan/sintesis dari bukti nyata; jangan menganggap dokumentasi NASA sebagai eksperimen pembanding. Jangan mengklaim studi pertama/terbaik. |
| R06–R10: label, metode, 2026 dan kesimpulan | Bedakan jumlah tinggi dari kenaikan; jelaskan varian ST-DBSCAN, sifat noise dan chaining; simpulkan hasil yang benar-benar ada. |
| Kelayakan classification | Perlukan kelengkapan ekspor, QA/FireMask wilayah-harian, pemetaan 61.03 dan timestamp ketersediaan informasi. Raster belum didapat pada audit lama; rencana perbaikan bukan hasil eksperimen. |
| Kesesuaian metode dengan UTS | Diskusikan kepada dosen bahwa ST-DBSCAN analisis pendukung dan classification belum dilatih. Algoritma tambahan tetap berlabel di luar materi. Format laporan tidak otomatis berarti memenuhi seluruh sasaran penilaian. |
| R11–R13 dan kepengarangan | Tinjau koreksi referensi, tulis bagian substantif yang belum lengkap, baca keseluruhan naskah, dan tetapkan pengungkapan bantuan sesuai arahan dosen. Selesaikan alasan catatan sebelum menghapus penandanya. |
| Jadwal LMS | Tanggal 4 November 2026 untuk pemeriksaan dataset/metode dan 11 November 2026 pukul 23.59 berasal dari instruksi pengguna. Revisi ini dibuat 5 November; hasil pertemuan tidak diasumsikan. Cocokkan kembali zona waktu dan tampilan tenggat pada LMS. |
| Uji demonstrasi | Buka salinan paket lama, ikuti Bagian F/H6; jika melakukan Run All, gunakan salinan dan catat hasil aktual. Jangan menimpa paket asli. |

## Urutan peninjauan yang disarankan

1. Baca Audit Kesesuaian dan Peta Revisi, terutama R01–R13.
2. Tinjau salinan technical report. Perubahan struktur sudah diterapkan; bagian substantif yang belum lengkap tetap ditandai.
3. Pelajari panduan A–F sambil membuka output notebook lama.
4. Latih naskah presentasi, perhitungan manual dan 40 tanya jawab; cocokkan istilah dengan materi kuliah.
5. Selesaikan bagian yang masih membutuhkan penulisan Anda dan konfirmasi ketentuan dosen sebelum mengumpulkan.

Paket ZIP revisi berisi delapan keluaran utama, jejak audit, sumber format dan kode penyusun dokumen. Dataset serta notebook tetap berada di paket penelitian lama; tidak diduplikasi atau diganti oleh ZIP revisi.
'''
    (O/'Checklist_Final_UTS_F1E325063.md').write_text(checklist,encoding='utf-8')
    for name in ['preservasi_report.json','panduan_inventory.json','report_navigation.json','guide_navigation.json','guide_render_comparison.json','jejak_pemindahan_report.csv','matriks_audit.csv','notebook_inventory.json','Panduan_GEMASTIK_2026_resmi.json']:
        shutil.copy2(W/name,META/name)
    source=O/'sumber_format';source.mkdir(exist_ok=True)
    shutil.copy2(W/'Panduan_GEMASTIK_2026_resmi.pdf',source/'Panduan_GEMASTIK_2026_resmi.pdf')
    with (META/'manifest_sumber_revisi.csv').open('w',newline='',encoding='utf-8') as f:
        cw=csv.writer(f);cw.writerow(['item','url','access_utc','sha256','catatan'])
        g=read(W/'Panduan_GEMASTIK_2026_resmi.json')
        cw.writerow(['Panduan GEMASTIK 2026',g['url'],g['access_utc'],g['sha256'],'PDF resmi cadangan; 109 halaman; bagian cetak 24–26. Waktu akses asli dipertahankan.'])
        cw.writerow(['WHO Wildfires','https://www.who.int/health-topics/wildfires','','','Halaman resmi diverifikasi pada rangkaian revisi; timestamp jaringan persis tidak dicatat. Sumber konteks, bukan hasil empiris penelitian ini.'])
        cw.writerow(['NASA dan referensi penelitian lama','REFERENSI_APA7.md serta sources/manifest_akses.json pada paket penelitian lama','','','Metadata lama dipertahankan; koreksi URL BIG dan sitasi NASA hanya pada salinan dokumen.'])
    code=O/'kode_editorial';code.mkdir(exist_ok=True)
    for name in ['common.py','audit_content.py','learning_content.py','build_report.py','build_learning.py','build_audit_pdf.py','finalize_editorial.py','report_blocks.json','guide_blocks.json','report_navigation.json','guide_navigation.json']:
        shutil.copy2(W/name,code/name)
    (O/'README_REVISI.md').write_text('''# Paket Revisi GEMASTIK 2026 — F1E325063

Ini salinan editorial dan bahan belajar, bukan hasil eksperimen baru. Simpan paket penelitian asli secara terpisah. Data, notebook dan hasil lama tidak diubah.

Mulai dari Checklist_Final_UTS_F1E325063.md, lalu Audit Kesesuaian dan Peta Revisi. Technical report adalah naskah tinjauan dengan penanda R01–R13, bukan naskah yang telah dinyatakan final untuk pengumpulan. Panduan presentasi merupakan ekstrak Bagian H panduan belajar, dengan nomor halaman tersendiri.

Paket penelitian sumber: [Paket_UTS_Klasifikasi_F1E325063.zip](https://chatgpt.com/library?file_id=libfile_625f0499d22481918b2866e7d2a2c075&account_id=personal). Anda sudah memiliki paket tersebut; salinan ZIP revisi ini tidak memuat ulang data mentah/notebook. Hash berkas sumber tercatat dalam jejak_revisi.

## Reproduksi editorial

Kode dalam kode_editorial merekam penyusunan dokumen dan verifikasi. Kode ini bukan notebook penelitian. Jalur ROOT/P/W/O pada common.py dan finalize_editorial.py mengikuti ruang kerja saat revisi; sesuaikan ke folder lokal. Tempatkan paket lama pada P dan berkas metadata JSON dalam W. Dependensi: python-docx, lxml, PyMuPDF, reportlab, nbformat; renderer DOCX memerlukan LibreOffice dan font yang sesuai. Versi paket tercatat dalam jejak_revisi/lingkungan_editorial.json.

Urutan penyusunan: build_report.py, build_learning.py, build_audit_pdf.py. Peta revisi dibentuk oleh audit_content.py. Render DOCX ke PDF, periksa seluruh halaman, lalu perbarui report_navigation.json/guide_navigation.json jika pagination berubah dan render kembali. finalize_editorial.py menyimpan salinan PDF final, ekstrak presentasi dan bukti pemeriksaan. Mode package hanya digunakan setelah pemeriksaan visual lengkap. Skrip tidak boleh diarahkan untuk menimpa folder sumber.

PDF final telah diperiksa. Font DOCX TNR dapat diganti Liberation Serif oleh renderer; pagination pada komputer lain dapat berbeda. Sumber format resmi dan pilihan editorial dibedakan dalam Audit/Peta Revisi. Tanggal revisi 5 November 2026 (WIB) tidak mengubah cutoff data.

Tidak ada training classification, perubahan hasil clustering, metrik baru, pengunggahan LMS, publikasi, atau pengesahan kepengarangan mandiri dalam revisi ini.
''',encoding='utf-8')
    import importlib.metadata, platform
    env={'python':platform.python_version(),'packages':{name:importlib.metadata.version(name) for name in ['python-docx','lxml','PyMuPDF','reportlab']},'nbformat':'unavailable in final editorial runtime; prior validation preserved','note':'Lingkungan penyuntingan, bukan perubahan lingkungan penelitian lama.'}
    dump(META/'lingkungan_editorial.json',env)
    with (O/'SHA256_BERKAS_REVISI.csv').open('w',newline='',encoding='utf-8') as f:
        cw=csv.writer(f);cw.writerow(['file','bytes','sha256'])
        for p in sorted(O.rglob('*')):
            if p.is_file() and p.name not in ['SHA256_BERKAS_REVISI.csv','Paket_Revisi_GEMASTIK_2026_F1E325063.zip']:
                cw.writerow([str(p.relative_to(O)),p.stat().st_size,sha(p)])
    zpath=O/'Paket_Revisi_GEMASTIK_2026_F1E325063.zip'
    with zipfile.ZipFile(zpath,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(O.rglob('*')):
            if p.is_file() and p!=zpath:z.write(p,'Paket_Revisi_GEMASTIK_2026_F1E325063/'+str(p.relative_to(O)))
    with zipfile.ZipFile(zpath) as z: assert z.testzip() is None
    names=['Audit_Kesesuaian_Technical_Report_GEMASTIK_2026.pdf','Peta_Revisi_Laporan_F1E325063.docx','Technical_Report_UTS_F1E325063_Rapih.docx','Technical_Report_UTS_F1E325063_Rapih.pdf','Panduan_Pemahaman_Penelitian_F1E325063.docx','Panduan_Pemahaman_Penelitian_F1E325063.pdf','Panduan_Presentasi_dan_Tanya_Jawab_F1E325063.pdf','Checklist_Final_UTS_F1E325063.md','Paket_Revisi_GEMASTIK_2026_F1E325063.zip']
    dump(W/'library_upload_request.json',{'uploads':[{'local_path':str(O/n),'purpose':'create_library_file','library_artifact_type':'report' if n.endswith(('.docx','.pdf')) else 'other'} for n in names]})
    print(json.dumps({'final_files':names,'zip_bytes':zpath.stat().st_size,'source_unchanged':a['preservation']['changed_source_files']==[]},indent=2))

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='package':package()
    else:prepare()
