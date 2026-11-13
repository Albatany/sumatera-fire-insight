from common import *
from learning_content import *
from docx.text.paragraph import Paragraph
import textwrap

old=Document(P/'Laporan_UTS_PenambanganData_Klasifikasi_F1E325063.docx')
oldg=Document(P/'Panduan_Presentasi_Klasifikasi_F1E325063.docx')
nb=json.loads((P/'UTS_PenambanganData_Klasifikasi_F1E325063.ipynb').read_text())
d=newdoc('Panduan Pemahaman Penelitian',TITLE,logo=True)
para(d,'Panduan belajar ini menjelaskan hasil audit, analisis deskriptif, ST-DBSCAN dan rancangan klasifikasi yang masih tertunda. Gunakan bersama paket penelitian lama dan technical report versi tinjauan. Penjelasan pendidikan dikembangkan pada revisi ini; data, algoritma, hasil eksperimen dan notebook sumber tidak diubah.')
para(d,'Status singkat: audit/EDA/clustering sudah dieksekusi; classification belum layak dan belum dilatih. Tidak ada metrik prediksi t+1. Angka penelitian berasal dari keluaran lama yang dapat ditelusuri.')
note(d,'Baca untuk memahami alur dan bukti. Naskah presentasi adalah bahan latihan, bukan pernyataan bahwa technical report telah ditulis mandiri atau disetujui dosen.')
page(d);head(d,'Cara memakai panduan')
para(d,'Mulai dari Bagian A dan B untuk memahami masalah serta satuan data. Bagian C menjelaskan delapan proses, Bagian D menjelaskan algoritma, dan Bagian E mendampingi setiap gambar serta tabel report. Bagian F mengikuti notebook yang sebenarnya. Bagian G memuat bahan peninjauan dataset/metode untuk jadwal 4 November. Bagian H memuat latihan presentasi, glosarium dan tanya jawab.')
table(d,['Keperluan','Bagian','Bukti yang dibawa'],[
 ['Menjelaskan penelitian singkat','A, G, H1','Manifest dan ringkasan eksperimen'],
 ['Memeriksa angka','C, E, F','CSV/JSON dan output tersimpan'],
 ['Membaca peta atau klaster','D dan E','Grafik asli serta ringkasan klaster'],
 ['Menjawab label dan leakage','C4, D, H4','Definisi label, gate temporal dan status QA'],
 ['Membahas format dan kepengarangan','Peta Revisi dan Checklist','Panduan GEMASTIK dan catatan R01–R13']], [4,3.5,7.1])
para(d,'Penomoran sel memakai indeks 0 sesuai urutan fisik file .ipynb; In[n] adalah execution_count tersimpan. Misalnya indeks 18 memiliki In[8]. Nomor tabel/gambar report menjadi rujukan utama karena nomor halaman dapat berubah setelah penyuntingan.')
nav=json.loads((W/'guide_navigation.json').read_text()) if (W/'guide_navigation.json').exists() else {}
for label in ['Bagian A Memahami penelitian','Bagian B Memahami dataset','Bagian C Memahami pengolahan data','Bagian D Memahami algoritma','Bagian E Membaca seluruh gambar dan tabel','Bagian F Penjelasan notebook','Bagian G Persiapan pertemuan 4 November 2026','Bagian H Panduan presentasi dan tanya jawab']:
 para(d,label+' • halaman '+str(nav.get(label,'—')),'Source')

head(d,'Bagian A Memahami penelitian',break_before=True)
head(d,'A1 Dari masalah karhutla ke pertanyaan yang dapat diuji',2)
para(d,'Karhutla berkaitan dengan lingkungan dan kehidupan masyarakat. WHO (n.d.) menjelaskan bahwa asap wildfire mencemari udara dan kejadian tersebut dapat mengganggu layanan penting. Rujukan itu memberi konteks umum; penelitian ini tidak mengukur korban, kerugian, kualitas udara atau dampak kesehatan penduduk Sumatera.')
para(d,'Pertanyaan komputasinya lebih terbatas: jika informasi sampai akhir hari t tersedia, dapatkah kita memperkirakan apakah jumlah deteksi suatu wilayah pada t+1 melampaui ambang historis? Keluarannya berupa kelas, sehingga classification sesuai bentuk pertanyaan. Namun, pertanyaan yang sah belum menjamin bahwa data menyediakan label yang sah.')
head(d,'A2 Mengapa NASA FIRMS dan MODIS',2)
para(d,'FIRMS menyediakan koordinat, waktu akuisisi dan atribut deteksi MODIS sehingga setiap baris dapat diaudit. Snapshot yang diterima mencakup 13 CSV dari 2015 sampai 2026. Data lokal memungkinkan pemeriksaan seluruh isi dan pelacakan row_id. Penggunaan MODIS membatasi instrumen penelitian, tetapi Terra/Aqua dan perbedaan koleksi/produk tetap harus dicatat.')
para(d,'CSV deteksi tidak memuat daftar lengkap piksel yang diamati tanpa api. Tanpa bukti pengamatan, kosongnya catatan tidak otomatis menjadi contoh negatif. Alasan classification tertunda berasal dari identifikasi target, bukan dari ketidakmampuan XGBoost menghitung model.')
head(d,'A3 Mengapa daratan utama Sumatera dan 2015 sampai 2026',2)
para(d,'Sumatera merupakan lingkup geografis yang ditetapkan dalam rancangan. Pelaksanaan memakai daratan utama delapan provinsi karena batas resmi yang diperoleh berada pada tingkat provinsi. Mask tidak mencakup seluruh kepulauan sekitar Sumatera. Jangan menambahkan alasan bahwa wilayah ini paling rawan tanpa kajian pembanding yang tersedia.')
para(d,'Tahun 2015–2025 menjadi periode historis yang direncanakan untuk pembelajaran dan pengujian, sedangkan 2026 merupakan studi kontemporer parsial. Rentang panjang memberi kesempatan melihat perubahan rekaman, tetapi tidak otomatis menghasilkan seri yang sebanding. Kode produk, tanggal kosong, lintasan dan status NRT perlu diperiksa.')
head(d,'A4 Manfaat realistis',2)
para(d,'Audit memastikan konsistensi snapshot dan mengidentifikasi keterbatasannya. ST-DBSCAN menghasilkan kelompok ruang-waktu yang dapat diperiksa kembali. Manfaat saat ini berupa kajian akademik yang transparan: pembaca mengetahui hasil, asumsi dan data yang masih kurang. Belum ada uji penerapan lapangan, prediksi kejadian kebakaran aktual, atau sistem peringatan dini operasional.')
note(d,'Latihan: jelaskan perbedaan memprediksi lonjakan deteksi dan memprediksi kebakaran. Jawaban harus menyebut proses pengamatan satelit serta batas makna label.')

head(d,'Bagian B Memahami dataset')
head(d,'B1 Asal data dan batas provenance',2)
para(d,'CSV lokal dilaporkan berasal dari NASA FIRMS. Manifest menyimpan nama, hash, ukuran, skema, jumlah baris, tanggal dan kode versi. URL halaman resmi bukan tautan transaksi unduh yang berhasil direkonstruksi. Parameter permintaan dan waktu unduh asli belum diberikan. Kecocokan hash membuktikan kesamaan snapshot, belum membuktikan seluruh provenance.')
para(d,'Kode 6.03 terdapat pada 397.657 baris mentah, 61.03 pada 141.030 dan 6.1NRT pada 91.697. Dokumentasi GIBS memetakan 6.03 ke C6 Standard processing. Arti 61.03 pada ekspor ini belum dipastikan. NRT 2026 tidak menyediakan type; missing struktural dipertahankan. Jumlah tersebut masih sebelum cutoff dan filter Sumatera.')
head(d,'B2 Kamus atribut',2)
para(d,'Tabel B1 menjelaskan kolom penting pada data deteksi.')
rows=[[c.text for c in row.cells] for row in old.tables[1].rows]
para(d,'Tabel B1 Atribut MODIS dan maknanya','Caption');table(d,rows[0],rows[1:],[3,3.5,8.1],10.5)
source(d,'Tabel 2 laporan lama; NASA MODAPS, NASA FIRMS; hasil audit skema.')
para(d,'Scan dan track mengingatkan bahwa dimensi piksel dapat berubah. Instrument menunjukkan instrumen, satellite menunjukkan platform. Type 0 adalah dugaan vegetasi, 1 gunung api, 2 sumber statis lain dan 3 lepas pantai menurut produk; kategori tersebut belum merupakan verifikasi lapangan. Daynight menjelaskan siang/malam saat akuisisi, bukan kategori risiko.')
head(d,'B3 Lima baris nyata sebelum dan sesudah',2)
before=read_csv('hasil/contoh_5_baris_sebelum.csv');after=read_csv('hasil/contoh_5_baris_sesudah.csv')
para(d,'Kelima contoh berasal dari fire_archive_M-C61_834980.csv. L18 berarti nomor baris fisik dengan header sebagai baris 1. Row ID lengkap adalah nama file diikuti :L18, dan seterusnya. Tabel B2/B3 meringkas kolom; CSV contoh tetap memuat atribut lengkap.')
para(d,'Tabel B2 Cuplikan atribut asli','Caption')
table(d,['Baris','Latitude','Longitude','Brightness K','Confidence','FRP MW'],[[r['row_id'].split(':')[-1],r['latitude'],r['longitude'],r['brightness'],r['confidence'],r['frp']] for r in before],[1.3,2.3,2.4,2.9,2.9,2.8],10)
source(d,'hasil/contoh_5_baris_sebelum.csv; row_id dapat ditelusuri ke CSV mentah.')
para(d,'Tabel B3 Representasi waktu dan hasil spatial join','Caption')
table(d,['Baris','Tanggal/jam asal UTC','Timestamp UTC','Provinsi','Versi / type'],[[r['row_id'].split(':')[-1],before[i]['acq_date']+' '+before[i]['acq_time'],r['acq_datetime_utc'].replace('+00:00',''),r['province'],r['version']+' / '+r['type']] for i,r in enumerate(after)],[1.2,3.2,3.8,4,2.4],9.8)
source(d,'hasil/contoh_5_baris_sesudah.csv. Tidak ada pergeseran ke WIB.')
para(d,'Pada L18, 0322 ditulis sebagai 03:22:00 UTC, sementara koordinat, versi dan nilai fisiknya tetap. Provinsi ditambahkan melalui polygon. L30 memiliki type 1; contoh ini memperlihatkan mengapa deteksi tidak otomatis identik dengan kebakaran vegetasi. Tidak ada label lonjakan pada lima baris ini.')
head(d,'B4 Tiga satuan yang tidak boleh tertukar',2)
table(d,['Satuan','Satu objek berarti','Contoh'],[['Deteksi','Rekaman piksel pada waktu/platform tertentu','L18'],['Wilayah-hari','Wilayah kandidat pada satu tanggal','Panel harian'],['Klaster','Deteksi terhubung menurut parameter','ST00901']],[3,8,3.6])
para(d,'Agregasi deteksi ke wilayah-hari tidak menciptakan bukti observasi negatif. Penggabungan ke klaster juga tidak menciptakan label kejadian kebakaran. Kedua agregasi menjawab pertanyaan berbeda.')

head(d,'Bagian C Memahami pengolahan data')
para(d,'Alur yang telah dijalankan dimulai dari audit, parsing dan filter, lalu kalender/fitur kandidat, EDA, clustering, pengujian dan interpretasi. Classification berhenti pada gerbang kelayakan. Penjelasan berikut merujuk hasil tersimpan; revisi dokumen tidak mengeksekusi ulang alur penelitian.')
for title,purpose,why,tech,example,result,proof,error in PROCESSES:
 head(d,'C'+title,2)
 for label,txt in [('Tujuan',purpose),('Alasan',why),('Cara teknis',tech),('Contoh nyata',example),('Hasil aktual',result),('Cara membuktikan',proof),('Kesalahan yang dihindari',error)]:
  p=para(d);p.add_run(label+'. ').bold=True;p.add_run(txt)

def oldmath(doc,idx):
 el=copy.deepcopy(list(doc.element.body)[idx]);p=Paragraph(el,d._body)
 p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.keep_together=True
 for x in el.xpath('.//w:pageBreakBefore'):x.getparent().remove(x)
 d.element.body.insert(len(d.element.body)-1,el)

head(d,'Bagian D Memahami algoritma')
head(d,'D1 Classification dan clustering',2)
para(d,'Classification mirip belajar memilah surat dari contoh yang telah diberi kategori. Label menjadi jawaban latihan. Pada penelitian ini jawaban yang dibutuhkan adalah lonjakan atau tidak lonjakan pada hari berikutnya. Clustering mirip menyusun surat ke kelompok berdasarkan kemiripan tanpa diberi kategori jawaban. Kelompok kemudian ditafsirkan setelah terbentuk.')
para(d,'Analogi membantu memahami mekanisme, tetapi kedekatan ruang-waktu pada data satelit belum membuktikan satu kejadian fisik. Noise tidak mempunyai arti aman dan ID klaster tidak menjadi jawaban supervised yang sah. Clustering sendiri tidak menggantikan kewajiban classification pada tugas mata kuliah.')
head(d,'D2 ST-DBSCAN dua ambang',2)
para(d,'[METODE TAMBAHAN DI LUAR MATERI] Implementasi memerlukan dua kondisi sekaligus: jarak haversine paling besar 2 km dan beda waktu paling besar 48 jam, dalam tahun UTC dan version literal yang sama. Minimum tetangga adalah lima, termasuk titik sendiri. Varian ini tidak diklaim memuat seluruh density factor dan atribut nonspasial dari artikel Birant–Kut.')
oldmath(old,215);oldmath(old,216)
source(d,'Rumus asli laporan lama; notebook indeks 13 menjelaskan N(i).')
para(d,'N(i) adalah himpunan tetangga titik i; d_s adalah jarak ruang; ε_s dan ε_t adalah batas ruang/waktu; z adalah strata. Core memenuhi jumlah minimum. Border menempel pada core tanpa memenuhi minimum sendiri. Noise berada di luar kelompok pada konfigurasi itu. BallTree mencari kandidat spasial, kemudian kondisi jam menyaringnya. Graf menyertakan hubungan titik dengan dirinya sendiri secara eksplisit.')
head(d,'D3 Pemilihan parameter dan chaining',2)
para(d,'Pilihan 2 km/48 jam/5 bersifat eksploratif, bukan parameter optimum. Batas lebih longgar dapat menghubungkan lebih banyak rekaman; minimum lebih besar dapat menghilangkan core. Jumlah klaster tidak harus berubah monoton karena kelompok dapat muncul, bergabung atau hilang. Sensitivitas memakai 1/2/5 km, 24/48/72 jam dan 3/5/10 titik, sehingga terdapat 27 konfigurasi.')
para(d,'Strata memutus hubungan di batas tahun/produk. Anggota dekat batas 72 jam ditandai, tetapi penandaan tidak menyambung ulang klaster. Chaining membuat rentang total klaster dapat melampaui ambang pasangan: A dekat B dan B dekat C tidak mengharuskan A dekat C. Urutan timestamp dan row_id dipertahankan karena border dapat berpindah ketika urutan berubah.')
head(d,'D4 Validasi dan hitungan manual',2)
para(d,'Pada 1.000 rekaman nyata, partisi graf jarang sama dengan matriks penuh dan kode upstream (ARI = 1). Core identik dan lingkungan simetris. Uji ini memeriksa implementasi pada sampel, bukan membuktikan klaster sebagai kejadian lapangan. Silhouette memakai jarak gabungan maksimum jarak ruang/ε_s dan beda waktu/ε_t pada maksimal 1.500 anggota non-noise per strata, seed 42.')
manual=read_csv('clustering/contoh_manual_tetangga_nyata.csv')
para(d,'Tabel D1 Tetangga nyata anchor L47211','Caption')
table(d,['Row ID pendek','Jarak km','Beda jam'],[[r['row_id'].split(':')[-1],f"{float(r['distance_km']):.4f}",f"{float(r['time_difference_hours']):.3f}"] for r in manual],[7,3.8,3.8],10)
para(d,'Semua row_id berawalan fire_archive_M-C61_834980.csv:. Anchor adalah L47211. Koordinat dan timestamp lengkap tetap tersedia pada CSV.','Source')
source(d,'clustering/contoh_manual_tetangga_nyata.csv; berlaku pada sampel validasi.')
para(d,'Sepuluh baris termasuk anchor memenuhi kedua batas. Karena minimum lima termasuk dirinya sendiri, anchor menjadi core dalam sampel tersebut. Sepuluh bukan jumlah tetangga seluruh dataset dan bukan sepuluh kebakaran.')
head(d,'D5 Rancangan classifier yang belum dieksekusi',2)
para(d,'XGBoost adalah kandidat boosting berbasis pohon. Secara konseptual, pohon tambahan memperbaiki kesalahan fungsi prediksi sebelumnya. Penelitian belum memasang/melatih XGBoost atau menghitung pembandingnya. DummyClassifier, baseline status tujuh hari, CART dan Random Forest juga belum dilatih. Uraian berikut merupakan rencana, bukan penjelasan kode model yang sudah ada.')
para(d,'Fitur berasal dari informasi sampai t: hitungan trailing, perubahan historis, FRP, confidence, proporsi platform/malam dan kalender. Label berada pada t+1 setelah syarat coverage/ekspor dipenuhi. Kuantil yang diusulkan adalah 0,90 dari hitungan positif training yang sah; alternatif 0,80 dan 0,95 belum difit. Jika lonjakan berarti kenaikan, rumus selisih historis perlu didefinisikan lebih dahulu.')
para(d,'Fit model, preprocessing dan kuantil hanya pada training masing-masing fold. Validation 2024 memilih konfigurasi; 2025 diuji sekali setelah dibekukan; 2026 tidak dipakai tuning. Histori sebelum validation boleh menjadi fitur jika tersedia pada origin. ID klaster retrospektif seluruh dataset tidak menjadi fitur forecasting karena dapat mengandung masa depan.')
head(d,'D6 Membaca metrik classifier tanpa angka palsu',2)
para(d,'Tabel D2 adalah susunan istilah, bukan confusion matrix empiris. Positif berarti lonjakan deteksi menurut label yang nantinya sah.')
para(d,'Tabel D2 Arti posisi pada confusion matrix','Caption')
table(d,['Aktual','Prediksi tidak lonjakan','Prediksi lonjakan'],[['Tidak lonjakan','TN: benar negatif','FP: positif palsu'],['Lonjakan','FN: lonjakan terlewat','TP: benar positif']],[4,5.3,5.3])
for idx in [59,60,61]:oldmath(oldg,idx)
para(d,'Precision menanyakan bagian prediksi positif yang benar; recall menanyakan bagian positif aktual yang ditemukan. F1 merangkum keduanya. Pembagian dengan nol harus memiliki aturan yang dinyatakan. Macro F1 memberi bobot sama per kelas; balanced accuracy merata-ratakan recall kelas. Tidak ada nilai empirisnya pada penelitian ini.')
para(d,'Kurva precision–recall mengubah ambang probabilitas dan menunjukkan kompromi precision/recall. Average precision merangkum precision memakai kenaikan recall; jangan menyamakannya diam-diam dengan integrasi trapezoid PR-AUC. Prevalensi positif menjadi pembanding dasar, tetapi belum diketahui secara sah. Kalibrasi memeriksa kecocokan probabilitas dengan frekuensi aktual, bukan sekadar banyaknya prediksi benar.')
head(d,'D7 CART manual sesuai materi',2)
para(d,'Sepuluh contoh asli memiliki delapan type 0 dan dua type 1. Gini awal 1 − 0,8² − 0,2² = 0,32. Split demonstrasi confidence ≤70 memberi tiga type 0 dan dua type 1 di kiri serta lima type 0 di kanan. Gini tertimbang 0,24; penurunannya 0,08. Entropy awal 0,721928 bit, entropy tertimbang 0,485475 bit, information gain 0,236453 bit. Nilai 70 merupakan median contoh, bukan ambang lonjakan atau split terbaik yang dicari model.')
source(d,'hasil/contoh_manual_10_baris.csv dan hasil/perhitungan_manual.json; notebook indeks 26. Rumus native lengkap ada pada Lampiran B report.')

head(d,'Bagian E Membaca seluruh gambar dan tabel')
para(d,'Bagian ini memuat sebelas grafik yang tersedia: sembilan pada report dan dua tambahan dari notebook. Gambar asli disalin tanpa mengubah angka atau menggambar ulang. Sesudahnya terdapat panduan bagi seluruh 19 nomor tabel report. Untuk tabel audit historis, gunakan pembaruan status format terbaru.')
for path,label,what,how,meaning,allowed,forbidden in FIG_GUIDES:
 head(d,label,2,break_before=True);pic(d,P/path,'Grafik '+label)
 source(d,path+'; hasil eksekusi lama. Tidak dibuat ulang pada revisi editorial.')
 for lab,txt in [('Apa yang sedang saya lihat?',what),('Bagaimana membacanya?',how),('Apa makna hasilnya?',meaning),('Kesimpulan yang boleh diambil',allowed),('Kesimpulan yang tidak boleh diambil',forbidden)]:
  p=para(d);p.add_run(lab+' ').bold=True;p.add_run(txt)
head(d,'E12 Panduan seluruh tabel report',2,break_before=True)
for no,title,what,how,meaning,allowed,forbidden in TABLE_GUIDES:
 head(d,f'Tabel {no} {title}',3)
 for lab,txt in [('Apa yang dilihat',what),('Cara membaca',how),('Makna hasil',meaning),('Boleh disimpulkan',allowed),('Tidak boleh disimpulkan',forbidden)]:
  p=para(d);p.add_run(lab+'. ').bold=True;p.add_run(txt)

head(d,'Bagian F Penjelasan notebook')
para(d,'Notebook sumber berisi 30 sel: 17 Markdown dan 13 kode. Execution_count kode tersimpan berurutan In[1]–In[13]. Log lama mencatat validasi nbformat dan eksekusi berurutan IPython dalam satu proses tanpa error. Uji antarmuka Google Colab/VS Code belum dilakukan. Revisi ini hanya membaca notebook; tidak mengubah atau menjalankannya ulang.')
groups=[
 ('0','Identitas dan status','Tujuan, identitas, batas data dan status classifier. Keterangan rubrik belum tersedia adalah keadaan saat notebook dibuat; format GEMASTIK kini sudah dibaca.'),
 ('1–2','Konfigurasi lokal','Memeriksa numpy, pandas, scipy, sklearn, matplotlib dan shapely; BASE mengikuti direktori kerja. Tidak mengunduh dataset atau memasang paket secara otomatis.'),
 ('3–4','Definisi fungsi','Sel kode 4 memuat fungsi audit, graf ketetanggaan, ST-DBSCAN, validasi dan gerbang classification. Mendefinisikan fungsi belum berarti menjalankan semua eksperimen.'),
 ('5–6','Audit ulang berkas','audit_again membaca 13 CSV dan menguji konsistensi hash/duplikasi serta checkpoint spasial lama. Spatial join awal tidak dibuat kembali di sel ini.'),
 ('7–9','Kebutuhan FireMask dan QA','Markdown menjelaskan kode produk dan keterbatasan. Sel 9 menampilkan percobaan_akses_hdf.json yang tersimpan; bukan mengunduh raster baru. Log sebelumnya menghasilkan HTTP 401.'),
 ('10–11','Gerbang classification','classification_gate memeriksa origin/target, subset, lookback dan syarat data. Semua eligible_labeled_rows nol; kelas dan prevalensi tetap NA.'),
 ('12–14','Protokol clustering','Rumus tetangga, strata dan 27 konfigurasi dijelaskan. Sel 14 membaca protokol_sebelum_eksperimen.json; parameter utama 2 km/48 jam/5.'),
 ('15–16','Validasi implementasi','validate_implementation membandingkan graf jarang, matriks penuh dan upstream pada 1.000 baris nyata; memeriksa permutasi serta core/noise.'),
 ('17–18','Eksperimen clustering','run_clustering menghitung hasil utama, ringkasan klaster, sensitivitas parameter dan input. Sel ini menghasilkan analisis clustering, bukan classifier.'),
 ('19–20','Tabel diagnostik','Menampilkan sensitivitas, filter kualitas/platform/type serta silhouette. Hasil tersebut tidak mengukur accuracy prediksi lonjakan.'),
 ('21–22','Tujuh visualisasi clustering','plot_all membuat tujuh grafik dari hasil clustering. Empat grafik EDA lama bukan hasil sel ini. Outline polygon disederhanakan untuk tampilan saja.'),
 ('23–24','Geografi dan studi 2026','Menampilkan sepuluh klaster terbesar dan tabel 1 Januari–30 Oktober. Tidak menghasilkan peta prediksi atau evaluasi classifier.'),
 ('25–26','Perhitungan manual nyata','Menampilkan maksimal sepuluh tetangga nyata serta contoh CART berdasarkan type asli. Row ID dipakai untuk telusur ke CSV.'),
 ('27–28','Assertion akhir','Memastikan classification_feasible/model_fitted false, row_id unik, cutoff dipatuhi dan peran core/border/noise tersedia. Lulus assertion bukan lulus persyaratan label.'),
 ('29','Rencana bersyarat','Sel Markdown, bukan kode training. Memuat split, baseline, tuning, metrik dan syarat perbaikan target. Jangan menunjukkannya sebagai model XGBoost yang telah dijalankan.')]
para(d,'Tabel F1 Peta seluruh kelompok sel','Caption')
table(d,['Indeks sel','Kelompok','Apa yang benar-benar dilakukan'],groups,[1.5,3.5,9.6],10)
head(d,'F1 Cuplikan kode dan terjemahan awam',2)
snips=[(2,'BASE=Path.cwd()','BASE berarti lokasi folder kerja. File lokal dicari relatif terhadap folder tersebut; di Colab lokasinya perlu disesuaikan sebagaimana komentar notebook.'),(6,'d=audit_again(BASE)','Buka dan periksa data yang sudah ditempatkan pada folder penelitian. Hasilnya disimpan pada variabel d.'),(11,'gate=classification_gate(BASE)','Periksa apakah pasangan fitur dan label memenuhi syarat. Variabel gate menyimpan keputusan; false berarti pelatihan tidak boleh diklaim berlangsung.'),(18,'result,clusters,sensitivity=run_clustering(BASE,d)','Panggil eksperimen pengelompokan. Tiga keluaran utama adalah baris dengan peran/ID, ringkasan kelompok, dan hasil sensitivitas.'),(28,"assert not gate['classification_feasible'] and not gate['model_fitted']",'Assertion memeriksa bahwa gerbang memang gagal dan classifier tidak difit. Ini menjaga konsistensi status ilmiah, bukan angka performa.')]
for idx,code,explain in snips:
 assert code in ''.join(nb['cells'][idx]['source'])
 head(d,'Sel '+str(idx)+' dengan In['+str(nb['cells'][idx]['execution_count'])+']',3)
 para(d,code,'Code');para(d,explain)
head(d,'F2 Cara membuktikan satu angka',2)
para(d,'Contoh: untuk 3.678 klaster, buka output sel 18 dan clustering/ringkasan_eksperimen.json. Cocokkan dengan jumlah kolom klaster pada hasil_utama_per_strata.csv. Untuk 154.184 deteksi, telusuri log filter dan hasil/data_sesudah_diolah.csv. Untuk satu titik, gunakan row_id. Jangan membuktikan angka hanya dengan membaca narasi laporan.')
para(d,'Run All pada salinan kerja akan menulis ulang berkas hasil di folder BASE. Untuk demonstrasi singkat, tampilkan output tersimpan. Jika dosen meminta eksekusi penuh, ekstrak paket ke folder baru, periksa dependencies dan jalankan berurutan; jangan menjalankannya di folder arsip asli. Hasil interface Colab/VS Code tetap perlu dicatat sesuai uji yang benar-benar dilakukan.')

head(d,'Bagian G Persiapan pertemuan 4 November 2026')
para(d,'Tanggal peninjauan berasal dari instruksi mahasiswa. Pada tanggal revisi 5 November, bagian ini dipertahankan sebagai bahan penjelasan untuk jadwal tersebut dan tindak lanjutnya. Tidak ada catatan hasil pertemuan atau persetujuan dosen yang diasumsikan.')
para(d,'Saya memakai 13 CSV NASA FIRMS MODIS tahun 2015–2026 dengan 630.384 baris mentah. Setelah cutoff 30 Oktober dan filter polygon BIG pada daratan utama delapan provinsi, terdapat 154.184 deteksi. Data mentah disimpan dan diperiksa dengan SHA-256. Hasil yang sudah tersedia adalah audit, EDA dan ST-DBSCAN pendukung. Konfigurasi utama menghasilkan 3.678 klaster serta 74.383 noise. Classification masih menjadi tujuan utama, tetapi label harian belum sah karena coverage dan waktu ketersediaan informasi belum terbukti. Tidak ada XGBoost yang sudah dilatih atau metrik prediksi yang bisa saya laporkan.')
para(d,'Bawa manifest, satu CSV asli, contoh lima baris, polygon/mask, keputusan_classification.json, notebook dengan output tersimpan, ringkasan clustering serta Peta Revisi. Jelaskan kebutuhan metadata ekspor, arti 61.03, raster QA dan available_at. Bahas kesesuaian metode tambahan dan cara menilai classification yang belum dapat dilanjutkan secara sah.')
para(d,'Batas pengumpulan yang diberikan pengguna adalah 11 November 2026 pukul 23.59 sesuai LMS. Zona waktu dan tampilan tenggat belum diverifikasi langsung. Tidak ada unggahan LMS pada revisi ini.')

head(d,'Bagian H Panduan presentasi dan tanya jawab',break_before=True)
para(d,NAME+' | '+NIM+' | Informatika R-002 | Universitas Jambi')
para(d,'Bahan latihan berdasarkan hasil tersimpan. Audit/EDA/ST-DBSCAN telah dijalankan; classification belum dilatih. Identitas tim kompetisi dan klaim manfaat operasional tidak dibuat.')
head(d,'H1 Penjelasan satu menit',2)
para(d,'Penelitian saya mengkaji deteksi hotspot MODIS di daratan utama Sumatera pada 2015–2026. Tujuan awalnya memprediksi lonjakan jumlah deteksi esok hari. Audit terhadap 13 CSV menemukan 630.384 baris mentah dan mempertahankan 154.184 deteksi setelah filter waktu/wilayah. Label harian belum dapat dibentuk karena hari tanpa catatan belum membuktikan pengamatan memadai. Karena itu classifier belum dilatih. Analisis pendukung ST-DBSCAN menghasilkan 3.678 klaster dan sekitar 48,24 persen noise, disertai uji sensitivitas. Klaster adalah kelompok rekaman, bukan kejadian kebakaran terkonfirmasi. Kontribusi saat ini adalah audit transparan dan gambaran pola ruang-waktu, dengan kebutuhan QA, provenance dan available_at yang jelas sebelum klasifikasi dilanjutkan.')
head(d,'H2 Naskah presentasi sembilan slide',2)
para(d,'Naskah berikut dirancang untuk latihan 7–10 menit dengan jeda untuk menunjuk visual. Durasi belum diuji dengan rekaman; gunakan stopwatch dan sesuaikan kecepatan tanpa mengubah status hasil. Ini panduan naskah, bukan berkas slide PPTX.')
for title,script in SCRIPT:head(d,title,3);para(d,script)
head(d,'H3 Sepuluh poin yang harus dipahami',2)
points=['13 CSV mencakup 12 tahun; ada dua berkas 2026.','Hotspot adalah deteksi anomali termal, bukan satu kebakaran.','Jumlah terpilih 154.184 setelah cutoff dan mask daratan utama.','Version disimpan string; 61.03 belum terselesaikan.','Tidak ada rekaman tetap NA sampai pengamatan dan kelengkapan ekspor terbukti.','Classification belum dilatih; nol label sah bukan kelas negatif.','ST-DBSCAN utama 2 km/48 jam/5 termasuk diri, terpisah per tahun/version.','3.678 klaster dan 74.383 noise adalah hasil clustering; noise bukan non-fire.','ARI/silhouette tidak sama dengan accuracy/F1 prediksi.','2026 provisional; gunakan jendela setara dan jangan menyimpulkan luas terbakar atau dampak operasional.']
for i,x in enumerate(points,1):para(d,f'{i}. {x}')
head(d,'H4 Pertanyaan dosen dan jawaban berbasis bukti',2,break_before=True)
for i,(q,a) in enumerate(QA,1):head(d,str(i)+' '+q,3);para(d,a)
head(d,'H5 Glosarium',2,break_before=True)
table(d,['Istilah','Makna dalam penelitian'],GLOSSARY,[3.6,11],10.5)
head(d,'H6 Demonstrasi notebook dari awal sampai akhir',2,break_before=True)
demo=[('Siapkan salinan paket','Ekstrak paket penelitian lama ke folder demonstrasi baru. Arsip asli tetap disimpan. Tunjukkan notebook, data mentah, hasil dan clustering.'),('Periksa lingkungan','Buka README/requirements. Colab atau VS Code perlu paket yang tersedia; tidak ada API key dalam setup notebook. Jangan menyatakan uji native berhasil sebelum dicoba.'),('Buka identitas dan konfigurasi','Sel 0–2: tunjukkan tujuan, seed dan BASE. Bedakan rubrik historis dalam notebook dari panduan format baru.'),('Buktikan data','Sel 3–6: tunjukkan fungsi dan output audit. Telusuri satu row_id dan SHA-256 tanpa mengedit CSV asli.'),('Tunjukkan hambatan label','Sel 7–11: buka log HTTP 401 dan gerbang classification. Jelaskan mengapa eligible=0 bukan target negatif.'),('Jelaskan tetangga','Sel 12–16: tunjukkan dua ambang, strata, minimum lima dan validasi sampel. ARI=1 bukan validasi kejadian lapangan.'),('Baca eksperimen','Sel 17–20: buka ringkasan utama, 27 skenario dan diagnostik silhouette. Sebutkan denominator setiap perbandingan.'),('Baca peta dan studi 2026','Sel 21–24: jelaskan grafik, type, chaining dan jendela tanggal setara. Jangan menyebut peta prediksi.'),('Kerjakan contoh manual','Sel 25–26: cocokkan sepuluh tetangga dan contoh CART ke row_id. Tunjukkan alasan angka, bukan sekadar menghafal.'),('Tutup dengan status','Sel 27–29: baca assertion, rencana split dan syarat data tambahan. Untuk eksekusi penuh gunakan Run All pada salinan; catat waktu/error aktual. Revisi ini tidak menjalankannya ulang.')]
for i,(title,body) in enumerate(demo,1):head(d,str(i)+' '+title,3);para(d,body)
head(d,'H7 Pertanyaan yang belum dapat dijawab',2)
table(d,['Pertanyaan','Bukti yang masih diperlukan'],UNANSWERED,[5.2,9.4],10)
head(d,'Sumber dan jalur bukti panduan',break_before=True)
for ref in [GUIDE_REF,WHO_REF,'Birant, D., & Kut, A. (2007). ST-DBSCAN: An algorithm for clustering spatial–temporal data. Data & Knowledge Engineering, 60(1), 208–221. https://doi.org/10.1016/j.datak.2006.01.013','Cakmak, E., & Plank, M. (n.d.). st_dbscan [Kode sumber berlisensi MIT]. https://github.com/eren-ck/st_dbscan','Giglio, L., Schroeder, W., Hall, J. V., & Justice, C. O. (2021). MODIS Collection 6 and Collection 6.1 active fire product user’s guide (Version 1.0). https://lpdaac.usgs.gov/documents/105/MOD14_User_Guide_V61.pdf','NASA MODAPS. (n.d.). MODIS Aqua and Terra thermal anomalies and fire locations MCD14DL NRT. https://modaps.modaps.eosdis.nasa.gov/services/about/products/c61-nrt/MCD14DL-NRT.html','NASA FIRMS. (n.d.). Fire alerts important notes. https://firms.modaps.eosdis.nasa.gov/alerts/notes.php','NASA GIBS. (n.d.). Accessing via Python. https://nasa-gibs.github.io/gibs-api-docs/python-usage/','Badan Informasi Geospasial. (n.d.). Batas administrasi provinsi. https://geoservices.big.go.id/gis/rest/services/STIG/Batas_Provinsi/MapServer/0']:
 reference(d,ref)
para(d,'Materi kuliah: Classification Decision Tree(2).pdf; [11a] KNN-Exercise-Key-LR(2).pdf; Clustering KMeans(2).pdf; Clustering Hierarchical(2).pdf; 03 - Data Visualization and EDA - PPT.pdf; 04 - Supervised Learning – Regression (I).pdf; 05 - Supervised Learning – Regression (II) - PPT.pdf. Pemetaan halaman dan hash mengikuti manifest_materi.csv serta hasil/peta_kesesuaian_materi.csv. Tahun/penulis yang belum teridentifikasi tidak ditebak.')
para(d,'Bukti penelitian: notebook sumber, manifest_sumber.csv, log_pembersihan.csv, label_definisi.json, audit_paket_final.json, ringkasan_eksperimen.json, validasi_implementasi.json, keputusan_classification.json, sensitivitas_27_skenario.csv, ringkasan_klaster.csv dan tabel/grafik yang jalurnya disebut pada setiap pembahasan. Daftar pustaka lengkap sumber lama tetap tersedia dalam report.')
save(d,'Panduan_Pemahaman_Penelitian_F1E325063.docx')
(W/'panduan_inventory.json').write_text(json.dumps(dict(parts=8,processes=len(PROCESSES),figures=len(FIG_GUIDES),report_tables=len(TABLE_GUIDES),questions=len(QA),glossary=len(GLOSSARY),notebook_cells=len(nb['cells']),code_cells=sum(c['cell_type']=='code' for c in nb['cells']),script_words=sum(len(t.split()) for _,t in SCRIPT)),indent=2))
print('learning guide built')
