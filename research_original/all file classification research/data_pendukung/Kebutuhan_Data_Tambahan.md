# Data yang dibutuhkan sebelum pemodelan

Paket saat ini menyelesaikan audit dan EDA. Prasyarat berikut belum tersedia.

1. Rubrik UTS resmi agar algoritma tambahan dan format dapat dicocokkan.
2. Metadata ekspor FIRMS asli: parameter area, tanggal awal/akhir, produk, koleksi, URL transaksi yang dapat diverifikasi, waktu akses asli. Periksa kembali Januari 2021 dan tanggal tepi tahun lain. Nama M-C61 tidak mengalahkan nilai version.
3. Metadata primer yang menjelaskan 61.03 dan konflik 6.03 pada nama M-C61. Bila perlu unduh ulang koleksi seragam dari penyedia resmi. Dokumentasikan perubahan, jangan timpa raw.
4. QA MOD14/MYD14 atau produk harian yang sesuai untuk menghitung pengamatan clear-sky, cloud dan no-data pada wilayah. Keberadaan setidaknya satu hotspot pada sebuah provinsi tidak membuktikan seluruh provinsi diamati memadai. Tabel missing-data nasional saja juga tidak menggantikan QA lokal.
5. Waktu data diterima/dipublikasikan (available_at), karena acq_time hanya waktu akuisisi. Tentukan origin dan jeda fitur yang benar-benar dapat dipenuhi.

Skema coverage yang disarankan: province_id, date_utc, sensor, product_version, area_observed_km2, area_clear_km2, expected_overpasses, observed_overpasses, export_complete, coverage_adequate, method, qa_source_id, available_at_utc. Tentukan aturan coverage sebelum melihat hasil model, termasuk perlakuan awan dan fragmentasi spasial. Jangan mengisi field ini dengan tebakan dari jumlah hotspot.

Meteorologi bersifat opsional. Uji API POWER satu titik dua hari berhasil; belum ada seri penelitian dan tidak ada cuaca yang masuk model. Bila digunakan, simpan respons mentah, koordinat grid/resolusi, basis waktu (UTC/LST), unit dan missing sentinel, waktu tersedia, strategi pembobotan luas wilayah, serta lag publikasi. Data esok tidak boleh menjadi fitur esok.

Alternatif mingguan tetap membutuhkan coverage. Alternatif klasifikasi type menjawab pertanyaan yang berbeda dan tidak boleh dipresentasikan sebagai keberhasilan prediksi lonjakan t+1.
