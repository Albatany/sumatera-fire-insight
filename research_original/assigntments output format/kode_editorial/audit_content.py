from common import *

# Each finding distinguishes a document issue from an unexecuted research step.
AUDIT = [
('A01','Sampul, hlm. 1; R001','Judul wajib; sesuai sebagian','Judul lama jujur menyebut rancangan, tetapi hasil clustering tertutup oleh tujuan yang tertunda.','Abstrak; ringkasan_eksperimen.json; keputusan_classification.json','Judul panjang; hierarki sampul dapat dipadatkan.','Tidak perlu nama koleksi yang belum pasti.','Tawarkan judul yang menonjolkan hasil aktual; keputusan akhir oleh mahasiswa.','Perlu Revisi'),
('A02','Abstrak, hlm. 2; R015','Komponen wajib tersedia','179 kata; angka dan status model jelas. Latar karhutla dan manfaat masih singkat.','Angka cocok dengan tabel dan log eksekusi lama.','Tetap satu paragraf; catatan editorial dipisahkan.','Konteks sosial perlu sumber yang relevan jika diperluas.','Pertahankan teks; beri arahan penguatan konteks dan kata kunci clustering.','Perlu Revisi'),
('A03','BAB I, hlm. 5; R085–R093','Pendahuluan ada; manfaat belum terpisah','Rumusan masalah dan tujuan bercampur; tujuan belum menyebut clustering yang sudah selesai.','Batas daratan utama dan tidak ada meteorologi dinyatakan.','Pisahkan 1.1 sampai 1.5.','Dampak masyarakat belum diberi rujukan langsung.','Pindahkan paragraf tanpa mengubah substansi; manfaat dan tujuan tambahan ditulis penulis.','Perlu Revisi'),
('A04','BAB II, hlm. 6–7','Belum memenuhi kajian terkait sebagai sintesis penelitian','Isi berupa teori/materi dan kamus, bukan perbandingan studi.','Birant–Kut: bibliografi dan abstrak; teks lengkap belum ditelaah.','Pindahkan kamus ke dataset dan materi ke lampiran.','Jangan menyebut dokumentasi NASA sebagai eksperimen pembanding.','Sediakan tabel bukti yang membedakan artikel, perangkat lunak, dan dokumentasi; isi kekosongan secara terbuka.','Belum Didukung Data'),
('A05','BAB III dan hlm. 20','Solusi usulan ada tetapi tersebar','Target, algoritma aktual dan algoritma rencana perlu dibedakan.','Protokol, notebook sel 4/14/18, definisi label.','Satukan menjadi bagian 3.1–3.7.','ST-DBSCAN dua ambang tidak identik seluruh ekstensi Birant–Kut.','Pertahankan penjelasan varian dan label metode tambahan.','Perlu Revisi'),
('A06','Inventaris, hlm. 11','Dataset memenuhi kebutuhan deskripsi','13 file untuk 12 tahun, 630.384 baris; bukan 12 file.','manifest_sumber.csv; audit_ulang_13_csv.csv','Judul dan sumber tabel perlu dipisah jelas.','Halaman NASA sumber tidak sama dengan URL unduhan asli.','Pertahankan seluruh angka dan rentang tanggal; tambahkan jalur bukti.','Sesuai'),
('A07','Audit versi, hlm. 11/18/33','Kualitas dan keterbatasan tercakup','6.03, 61.03, 6.1NRT dipertahankan; 61.03 belum pasti.','GIBS ValueMap; manifest; audit versi lama.','Temuan berulang dapat dihubungkan dengan rujukan.','Nama M-C61 tidak membuktikan keseragaman koleksi.','Jangan mengubah status versi; cukup rapikan lokasi pembahasan.','Sesuai'),
('A08','Geometri, hlm. 12','Lingkup dataset jelas','154.184 deteksi pada delapan bagian provinsi daratan utama.','audit_geometri.csv; BIG_request.json','Keterangan mask harus dekat peta.','URL BIG salah ketik SIG; metadata dan notebook memakai STIG.','Koreksi URL bibliografi saja dan catat perubahan.','Perlu Revisi'),
('A09','EDA dan kasus 2026, hlm. 13–15','Hasil tersedia','Deskripsi dibedakan dari prediksi; cutoff dicatat.','Tabel waktu, satelit dan jendela 1 Januari–30 Oktober.','Tambahkan sumber per gambar; rujukan sudah sebagian ada.','Sumber NASA cukup untuk makna deteksi, bukan validasi kejadian.','Jaga grafik asli; jelaskan peralihan produk dan keterbatasan pembandingan.','Sesuai'),
('A10','Judul kasus 2026, hlm. 14; R162','Judul subbagian menimbulkan ambiguitas','Frasa Penerapan Model masih muncul, disusul penyangkalan faktual.','Tidak ada prediksi atau model classifier.','Ubah heading struktural menjadi studi deskriptif provisional; simpan judul lama dalam catatan perubahan.','NRT tidak boleh disebut standard tanpa bukti.','Penulis meninjau istilah agar tidak mengesankan penerapan classifier.','Perlu Revisi'),
('A11','Label dan gate, hlm. 8/18','Keterbatasan penting telah dilaporkan','Tidak ada label sah; 23.809 wilayah-hari tanpa rekaman tetap NA.','label_definisi.json; kelayakan_classification_per_split.csv','Rencana metrik ditempatkan terpisah dari hasil.','Sumber negatif independen belum ada.','Jangan mengisi confusion matrix/F1 atau memaksa nol.','Belum Didukung Data'),
('A12','FireMask dan QA, hlm. 19/27','Rencana solusi pengamatan jelas','Raster belum didapat; dua akses HTTP 401.','percobaan_akses_hdf.json; dua metadata CMR.','Tabel kode dapat tetap dipakai dengan sumber halaman NASA.','Metadata contoh bukan inventory lengkap; decoder belum diuji.','Pertahankan status belum tersedia; jangan mengklaim masalah label terselesaikan.','Belum Didukung Data'),
('A13','Metode dan hasil clustering, hlm. 20–26','Eksperimen aktual tersedia','3.678 klaster, 74.383 noise; bukan kejadian kebakaran.','ringkasan_eksperimen.json; hasil_utama_per_strata.csv','Pisahkan hasil angka dari pembahasan makna.','Parameter eksploratif; bukan optimum atau standar NASA.','Pertahankan hasil, rumus, 27 sensitivitas, dan batas varian.','Sesuai'),
('A14','Validasi, hlm. 22–23','Pengujian tersedia','ARI dan silhouette hanya untuk partisi/diagnostik, bukan akurasi prediksi.','validasi_implementasi.json; silhouette_diagnostik.csv','Beri keterangan denominator dan sampel.','Kode pembanding dan lisensi tersedia.','Jelaskan bahwa ARI=1 pada sampel tidak memvalidasi api aktual.','Sesuai'),
('A15','BAB IV keseluruhan','Hasil dan analisis belum menjadi dua komponen terpisah','Fakta data, interpretasi, dan rencana masih bergantian.','Semua tabel dan gambar lama tersedia.','Buat bagian 4 hasil dan bagian 5 analisis.','Rujukan internal harus mengikuti nomor baru.','Pindahkan blok asli; jangan tulis ulang pembahasan otomatis.','Perlu Revisi'),
('A16','BAB V, hlm. 29','Kesimpulan tersedia','Tidak mengklaim classifier berhasil; rekomendasi proporsional.','Status model false; tujuan prediksi belum tercapai.','Pisahkan keterbatasan ke analisis, tindak lanjut tetap terhubung.','Dampak operasional tidak dibuktikan.','Pertahankan isi, beri catatan penulis untuk menjawab tujuan clustering.','Sesuai'),
('A17','Daftar pustaka, hlm. 30–33','Referensi tersedia; perlu perapian','Ada 19 entri; teori, dokumentasi, perangkat lunak dan materi bercampur.','Snapshot NASA/Crossref/kode dan manifest materi.','Hilangkan heading LANJUTAN sebagai bagian terpisah; hanging indent konsisten.','NASA FIRMS n.d. perlu cocok n.d.-a/b; BIG URL perlu STIG.','Perbaiki tautan dan identitas sitasi; sumber baru hanya GEMASTIK dan WHO untuk catatan konteks.','Perlu Revisi'),
('A18','Lampiran audit, hlm. 34–35','Bukti audit tersedia','Status rubrik belum tersedia sudah kedaluwarsa setelah instruksi terbaru.','Panduan resmi pp. 24–26 kini dibaca; LMS hanya keterangan pengguna.','Labeli tabel audit lama sebagai catatan historis.','Format GEMASTIK tidak mengesahkan algoritma tambahan atau classifier yang belum ada.','Tambahkan status terbaru tanpa mengubah log/notebook lama.','Perlu Revisi'),
('A19','Panduan lama, 17 halaman','Pendukung pembelajaran, bukan report kompetisi','24 pertanyaan dan 46 istilah; penjelasan sel/visual belum menyeluruh.','Teks panduan dan notebook 30 sel, 13 kode.','Susun A–H, panduan visual per item dan peta sel bernomor.','Cuplikan ilustratif lama jangan diklaim salinan kode persis.','Perluas belajar dengan kutipan kode aktual dan >=25 tanya jawab.','Perlu Revisi'),
('A20','Status kepengarangan','Batas penggunaan GenAI perlu ditangani','Keaslian naskah tidak dapat disahkan oleh audit otomatis.','GEMASTIK p. 25; permintaan pengguna membatasi peran editorial.','Penanda tinjauan harus tampak di titik terkait.','Tidak membuat deklarasi orisinalitas atau skor deteksi AI.','Mahasiswa membaca, menulis bagian kurang, memverifikasi semua klaim dan menyetujui naskah.','Belum Didukung Data'),
('A21','Kebaruan dan manfaat','Aspek penilaian perlu bukti','Tidak ada tinjauan sistematis atau validasi manfaat operasional.','Studi ini menghasilkan audit dan klaster retrospektif.','Letakkan perbedaan sebagai catatan terukur, bukan slogan kebaruan.','Tidak dapat mengklaim studi pertama atau terbaik.','Tuliskan perbedaan lingkup; manfaat berupa potensi akademik.','Belum Didukung Data'),
]

NOTES = [
('R01','Judul; R001','Judul lama mendahulukan klasifikasi yang masih rancangan.','Usulan judul disediakan di sampul. Pilih atau tulis kembali judul yang menyebut hasil clustering dan audit kesiapan klasifikasi.','Keputusan judul oleh penulis; hasil eksperimen tidak berubah.'),
('R02','Abstrak; R015–R016','Isi angka konsisten, tetapi konteks karhutla dan kata kunci clustering kurang tampak.','Tambahkan satu kalimat konteks yang bersumber; jelaskan manfaat sebagai pemahaman pola deteksi. Pertahankan fakta bahwa classifier belum dilatih.','Tulis sendiri abstrak akhir; angka lama jangan diganti.'),
('R03','Pendahuluan; R085–R091','Pertanyaan prediksi belum ditopang label; tujuan clustering belum eksplisit.','Pisahkan rumusan masalah dan tujuan. Tambahkan pertanyaan tentang pola ruang-waktu sebagai analisis pendukung yang telah dijalankan.','Tulisan substantif baru memerlukan rumusan mahasiswa.'),
('R04','Manfaat; R286','Manfaat akademik sudah dinyatakan, tetapi kaitan masyarakat perlu sumber.','WHO menjelaskan dampak asap dan gangguan layanan akibat wildfire. Gunakan sebagai konteks umum, bukan bukti dampak lokal atau keberhasilan penelitian ini.','Sumber baru WHO disediakan; jangan membuat angka kesehatan Sumatera.'),
('R05','Kajian terkait dan 3.7','Landasan teori belum menjadi sintesis penelitian terdahulu.','Tinjau Birant–Kut dari teks lengkap bila tersedia. Catat dataset, tujuan dan hasil yang benar-benar dilaporkan; jelaskan beda varian dua ambang.','Tabel bukti editorial bukan kajian pustaka final; tidak ada klaim kebaruan.'),
('R06','Batas makna lonjakan; R117–R118','Kuantil jumlah tinggi tidak otomatis menyatakan peningkatan tajam.','Contoh saran kalimat: “Definisi sementara menandai hari dengan jumlah deteksi tinggi. Syarat kenaikan terhadap histori belum ditetapkan.”','Saran untuk ditinjau, bukan perubahan definisi label atau hasil.'),
('R07','Metode; R196/R222','Algoritma tambahan perlu dijelaskan tanpa mengklaim sudah disetujui dosen.','Terangkan alasan dua ambang dan batas replikasi Birant–Kut. Bahas kesesuaian metode tambahan dengan dosen.','Pembahasan kesesuaian metode menjadi bahan diskusi dengan dosen.'),
('R08','Kasus 2026; R162–R170','Judul Penerapan Model berisiko dibaca sebagai eksperimen classifier.','Gunakan istilah studi deskriptif tahun 2026 provisional. Pertahankan keterangan terakhir teramati dan peralihan archive/NRT.','Heading diperbaiki; judul lama dicatat dalam peta revisi.'),
('R09','Validasi dan noise; R228/R236/R240','Istilah teknis padat; pembaca dapat menyamakan ARI dengan accuracy.','Contoh saran: “ARI membandingkan dua pembagian klaster. Nilainya tidak mengukur ketepatan deteksi kebakaran.”','Penjelasan dapat disingkat oleh penulis tanpa menghilangkan batas makna.'),
('R10','Kesimpulan; R280–R285','Tujuan prediksi belum tercapai dan harus tetap jelas.','Jawab tujuan audit dan clustering terlebih dahulu, lalu nyatakan syarat yang menghalangi klasifikasi. Hindari kata berhasil untuk model yang belum dilatih.','Tidak menambahkan kinerja atau kontribusi kebaruan.'),
('R11','Rujukan; R107/R288','Tautan BIG dan akhiran tahun NASA FIRMS tidak konsisten.','SIG diganti STIG berdasarkan BIG_request.json. Sitasi atribut memakai NASA MODAPS; batas pengamatan memakai NASA FIRMS n.d.-b.','Perbaikan mekanis tercatat; metadata dataset asli tidak diubah.'),
('R12','Rubrik; R100/R317/R322','Status lama rubrik tidak tersedia kini tidak lengkap.','Panduan format GEMASTIK telah diverifikasi. Instruksi jadwal dan konteks UTS berasal dari pengguna; penilaian rinci LMS belum dibaca langsung.','Catatan lama disimpan sebagai sejarah audit, bukan status terbaru.'),
('R13','Seluruh naskah','Perapian otomatis tidak menjamin ketentuan kepengarangan.','Baca seluruh naskah, tulis bagian substantif yang kurang dengan pemahaman sendiri, verifikasi sumber, dan putuskan pengungkapan bantuan AI sesuai arahan dosen.','Belum ada pernyataan kepengarangan mandiri atau persetujuan akhir.'),
]

LAYOUT = [
('Organisasi','BAB I–V; hasil dan pembahasan bergabung','Enam bagian bernomor dengan judul/abstrak, pustaka, dan lampiran','Delapan komponen GEMASTIK mudah ditemukan'),
('Ukuran kertas','Letter pada dokumen sumber','Letter 21,59 × 27,94 cm dipertahankan','Pilihan editorial; bagian C tidak menetapkan ukuran'),
('Margin','Kiri 4 cm; sisi lain 3 cm','Kiri 4 cm, kanan 3 cm, atas/bawah 2,7 cm','Pilihan editorial untuk ruang baca dan footer'),
('Teks utama','Times New Roman 12; spasi 1,5; PDF lama Nimbus Roman','DOCX Times New Roman 12; spasi 1,15 dan jarak 6 pt; PDF revisi memakai substitusi Liberation Serif','Pilihan editorial; bukan aturan GEMASTIK. Rumus mempertahankan font simbol yang diperlukan'),
('Heading','Banyak heading kapital memulai halaman baru','Hierarki 14/12 pt; heading melekat ke isi','Mengurangi halaman renggang dan judul terpisah'),
('Tabel','18 tabel; sumber tidak selalu eksplisit','19 tabel report termasuk tabel bukti kajian terkait; header berulang, baris tidak dipecah','Seluruh angka tabel lama dipertahankan'),
('Gambar','9 gambar report dan 11 berkas grafik tersedia','9 gambar report asli tetap; 11 grafik dijelaskan di panduan','Tidak mereplot atau mengubah data grafik'),
('Persamaan','OMML asli tanpa penomoran seragam','OMML asli dipertahankan dan diberi nomor urut','Rumus tetap dapat diedit; makna/angka tidak berubah'),
('Daftar isi','Halaman diketik untuk struktur 35 halaman','Peta navigasi diperbarui setelah render','Nomor halaman mengikuti versi baru'),
('Pustaka','Tiga halaman berjudul lanjutan','Satu bagian; indentasi gantung dan sumber baru ditandai','URL BIG dan identitas sitasi dikoreksi'),
('Catatan penulis','Belum ada penanda editorial','[TINJAU PENULIS Rxx] dekat paragraf terkait','Saran bukan pengganti keputusan kepengarangan'),
('Warna','Grafik asli dan logo warna','Teks/tabel hitam putih; logo dan grafik asli dipertahankan','Grafik tidak diubah agar identik dengan eksperimen'),
]

TABLE_SOURCE = {
1:'Matriks bukti editorial dari Birant dan Kut (2007), metadata Crossref, abstrak penerbit; Cakmak/Plank; Giglio et al. (2021). Tidak ada eksperimen baru.',
2:'Laporan lama Tabel 2; NASA MODAPS dan NASA FIRMS. Skema diperiksa dalam manifest_sumber.csv.',
3:'hasil/manifest_sumber.csv; clustering/audit_ulang_13_csv.csv. Rentang rekaman, bukan bukti coverage.',
4:'hasil/audit_geometri.csv dan data_pendukung/BIG_request.json; hasil audit sebelumnya.',
5:'Giglio et al. (2021), hlm. 22, 27, 54–55; dokumentasi, bukan hasil pembacaan raster penelitian.',
6:'Rancangan temporal dalam hasil/label_definisi.json; belum menjadi hasil model.',
7:'Rancangan model pada laporan lama Tabel 4; seluruh classifier belum dilatih.',
8:'clustering/kelayakan_classification_per_split.csv; notebook indeks 11, output In[5].',
9:'hasil/status_eksekusi.json dan clustering/keputusan_classification.json; tidak ada metrik classifier.',
10:'hasil/tabel/perbandingan_1Jan_30Okt.csv; notebook indeks 24, output In[11].',
11:'clustering/hasil_utama_per_strata.csv; notebook indeks 18, output In[8].',
12:'clustering/sensitivitas_27_skenario.csv; notebook indeks 20, output In[9].',
13:'clustering/sensitivitas_kualitas_satelit_type.csv; notebook indeks 20, output In[9].',
14:'hasil/peta_kesesuaian_materi.csv dan manifest_materi.csv; empat PDF awal.',
15:'hasil/peta_kesesuaian_materi.csv dan manifest_materi.csv; tiga PDF e-learning tambahan.',
16:'hasil/contoh_manual_10_baris.csv dan perhitungan_manual.json; notebook indeks 26, In[12].',
17:'clustering/contoh_manual_tetangga_nyata.csv; notebook indeks 26, In[12].',
18:'Laporan lama Tabel 17, status audit 1 November 2026. Baris rubrik bersifat historis; lihat catatan R12.',
19:'Laporan lama Tabel 18 dan RENCANA_PERBAIKAN_CLASSIFICATION.md. Status format diperbarui dalam catatan R12.'}
FIG_SOURCE = {
1:'hasil/grafik/01_deteksi_tahunan_versi.png; data hasil/tabel/jumlah_tahun_versi.csv.',
2:'hasil/grafik/03_komposisi_satelit.png; data hasil/tabel/jumlah_tahun_satelit.csv.',
3:'hasil/grafik/02_bulanan_sebanding.png; data hasil/tabel/perbandingan_bulanan_1Jan_30Okt.csv.',
4:'hasil/grafik/04_peta_deteksi.png; hasil spatial join BIG dan perbandingan jendela tanggal.',
5:'clustering/grafik/02_sensitivitas_noise.png; sensitivitas_27_skenario.csv.',
6:'clustering/grafik/03_peta_peran_titik.png; hasil_st_dbscan.csv; outline BIG disederhanakan untuk tampilan.',
7:'clustering/grafik/05_type_klaster_terbesar.png; ringkasan_klaster.csv dan hasil_st_dbscan.csv.',
8:'clustering/grafik/04_durasi_ukuran_klaster.png; ringkasan_klaster.csv.',
9:'clustering/grafik/06_rincian_klaster_terbesar.png; anggota ST00901 pada hasil_st_dbscan.csv.'}

LITERATURE = [
['Birant & Kut (2007), artikel; metadata dan abstrak','Objek spasial, temporal, dan atribut nonspasial; detail dataset belum ditelaah dari teks lengkap','ST-DBSCAN, ekstensi DBSCAN','Mengelompokkan objek pada ruang dan waktu','Abstrak melaporkan implementasi dalam data warehouse serta hasil penambangan; tidak ada skor numerik yang dipakai di laporan ini','Penelitian ini memakai dua ambang ruang/waktu, data deteksi MODIS, dan strata tahun/version; tidak mengklaim seluruh ekstensi asli'],
['Cakmak & Plank (n.d.), perangkat lunak','Masukan berwaktu dan koordinat; bukan studi karhutla pembanding','Implementasi ST-DBSCAN','Menyediakan kode pengelompokan','Sumber kode MIT tersedia; hasil uji ARI pada penelitian ini milik eksperimen sendiri, bukan hasil yang diklaim penulis perangkat lunak','Dipakai untuk memeriksa kesetaraan implementasi pada sampel nyata'],
['Giglio et al. (2021), panduan produk','Produk MODIS active fire, termasuk MOD14A1/MYD14A1','Dokumentasi algoritma dan format produk','Menjelaskan arti data dan kualitas pengamatan','Kategori FireMask/QA dan format harian dijelaskan; bukan hasil classifier lonjakan Sumatera','Dipakai untuk audit observabilitas dan rancangan perbaikan target, bukan pembanding skor model']]

def make_peta():
 d=newdoc('Peta Revisi Laporan UTS', 'Pemeriksaan struktur GEMASTIK 2026 dan catatan editorial',review=True)
 para(d,'Naskah sumber: Laporan_UTS_PenambanganData_Klasifikasi_F1E325063.docx versi 1, 35 halaman. Identitas dan hasil lama dipertahankan. Panduan sumber berjumlah 17 halaman. Pemeriksaan ini tidak menjalankan ulang penelitian.')
 para(d,'Judul sumber: “Rancangan Klasifikasi Lonjakan Deteksi Hotspot MODIS dengan Analisis Pendukung Klaster Spasio Temporal di Daratan Utama Sumatera”.')
 para(d,'Heading kasus 2026 sumber: “Studi Kasus Penerapan Model pada Data Hotspot Tahun 2026 (Provisional)”. Pada salinan revisi, heading menjadi studi deskriptif provisional agar tidak mengesankan classifier telah diterapkan.')
 page(d);head(d,'1 Peta pemindahan struktur')
 table(d,['Bagian lama','Tujuan dalam salinan rapi','Perlakuan'],[
 ['Sampul dan abstrak','Judul dan abstrak','Judul usulan bertanda; abstrak lama dipertahankan'],
 ['BAB I','1 Pendahuluan','Pisahkan masalah, tujuan, manfaat, batasan; isi yang kurang diberi catatan'],
 ['BAB II dan referensi','2 Kajian terkait; Lampiran A','Materi kuliah ke lampiran; tabel bukti terkait untuk ditinjau'],
 ['BAB III; FireMask; metode ST-DBSCAN','3 Solusi usulan','Algoritma aktual dan rancangan supervised dibedakan'],
 ['BAB IV: tabel/grafik','4 Hasil eksperimen dan pengujian','Data/hasil dipindahkan tanpa perubahan angka'],
 ['BAB IV: interpretasi; BAB V keterbatasan','5 Analisis hasil eksperimen dan pengujian','Paragraf penafsiran asli dikelompokkan'],
 ['BAB V: kesimpulan/tindak lanjut','6 Kesimpulan','Tetap menyatakan classifier belum dijalankan'],
 ['Pustaka dan lampiran','Daftar pustaka; Lampiran A–D','Sumber baru ditandai; audit lama diberi status historis']], [4,5,5.5])
 head(d,'2 Tabel perubahan tata letak')
 table(d,['Unsur','Sebelum','Sesudah','Alasan'],LAYOUT,[2,3.5,5.5,3.6],9.5)
 head(d,'3 Catatan Humanizer untuk ditinjau penulis',break_before=True)
 para(d,'Peninjauan bahasa memakai skill humanizer untuk menemukan istilah padat, pengulangan, dan kalimat yang mudah disalahpahami. Catatan di bawah tidak menilai apakah teks dibuat AI dan tidak dimaksudkan mengelabui pemeriksaan keaslian. Teks laporan lama tidak ditulis ulang secara menyeluruh. Penanda yang sama muncul di salinan report.')
 for rid,loc,why,suggest,action in NOTES:
  head(d,rid+' '+loc,2)
  para(d,'Alasan perbaikan: '+why).paragraph_format.keep_with_next=True
  para(d,'Arahan/saran: '+suggest).paragraph_format.keep_with_next=True
  note(d,'Tindakan penulis: '+action)
 head(d,'4 Perubahan referensi dan status lama',break_before=True)
 table(d,['Item','Tindakan','Bukti'],[
 ['BIG','Koreksi SIG menjadi STIG hanya dalam salinan dokumen','BIG_request.json dan endpoint resmi STIG yang dapat dibaca'],
 ['NASA FIRMS','Samakan akhiran n.d.-b untuk catatan batas pengamatan','Daftar pustaka lama dan Fire alerts important notes'],
 ['GEMASTIK 2026','Tambahkan acuan format; bukan deklarasi peserta lomba','Panduan resmi, halaman cetak 24–26'],
 ['WHO','Tambahkan sumber konteks bagi penulis dan panduan belajar','Wildfires, halaman resmi; tidak ada data dampak lokal baru'],
 ['Rubrik tidak tersedia','Simpan sebagai status audit lama; beri catatan perkembangan','Format kini terverifikasi; rincian LMS dan persetujuan metode belum diperiksa langsung']], [3,6,5.6])
 head(d,'5 Keputusan yang masih milik mahasiswa')
 para(d,'Mahasiswa menetapkan judul akhir, menulis konteks dan manfaat berdasarkan sumber, melengkapi kajian terkait dari bahan yang benar-benar dibaca, menjelaskan kesesuaian metode kepada dosen, dan meninjau seluruh kalimat. Catatan editorial perlu diselesaikan sebelum pengumpulan. Jangan menghapus catatan hanya agar naskah tampak final.')
 para(d,'Tanggal 4 November 2026 dan tenggat 11 November 2026 pukul 23.59 mengikuti instruksi pengguna tentang LMS. Zona waktu dan tampilan tenggat perlu dicocokkan pada LMS; tidak ada pengiriman atau publikasi dalam pekerjaan ini.')
 head(d,'Sumber pemeriksaan')
 reference(d,GUIDE_REF);reference(d,WHO_REF)
 para(d,'Peninjauan bahasa menggunakan skill humanizer sebagai bantuan editorial, bukan sumber ilmiah penelitian. Kode R01–R13 menandai catatan revisi; kode tiga digit seperti R162 merujuk blok naskah sumber pada jejak_pemindahan_report.csv.','Source')
 save(d,'Peta_Revisi_Laporan_F1E325063.docx')

if __name__=='__main__':make_peta()
