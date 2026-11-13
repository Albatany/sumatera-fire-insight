# Mulai di sini — SUMAFIRE INSIGHT

Muhammad Aziz Syah Dani · F1E325063 · Informatika · Universitas Jambi.

Paket lengkap memuat website mandiri, snapshot opsional dari hasil penelitian nyata, serta dua ZIP asli penelitian dan revisi technical report. Seluruh kode/notebook/data/laporan penelitian dipertahankan. Kode yang dirapikan hanya proyek website baru.

## Urutan paling cepat

1. Ekstrak seluruh ZIP ini.
2. Buka folder sumafire-insight di VS Code.
3. Pasang Node.js 24 LTS dan Python 3.11+.
4. Terminal Windows PowerShell:

```powershell
npm.cmd ci
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
npm.cmd run data:install-snapshot -- "..\prepared_snapshot"
npm.cmd run data:verify
npm.cmd run dev
```

Linux Bash:

```bash
npm ci
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
npm run data:install-snapshot -- "../prepared_snapshot"
npm run data:verify
npm run dev
```

5. Buka URL yang dicetak terminal, biasanya http://localhost:3000.
6. Periksa Overview → Data transparency → Cluster explorer → Prediction lab.

Bila ingin menyambungkan manual dari penelitian sendiri, jangan pasang snapshot di atas. Ikuti sumafire-insight/DATA_IMPORT_GUIDE.md (20 langkah). Website source mandiri boleh dijalankan tanpa data dan akan menampilkan empty state.

## Isi paket

| Lokasi | Isi |
| --- | --- |
| sumafire-insight | Seluruh source code, setup, data contract, panduan manual, deployment, hasil tes, screenshot |
| prepared_snapshot | DuckDB/Parquet, agregat, metadata, hash; data olahan yang sudah diverifikasi, belum otomatis aktif |
| research_original/Paket_UTS_Klasifikasi_F1E325063.zip | Notebook, CSV mentah dalam ZIP asal, hasil pengolahan, clustering, audit, materi, grafik dan laporan awal |
| research_original/Paket_Revisi_GEMASTIK_2026_F1E325063.zip | Technical report revisi DOCX/PDF, panduan pemahaman/presentasi dan audit editorial |
| ARCHIVE_MANIFEST.json | Bukti kedua arsip disalin byte-for-byte |

Tidak ada model classification baru atau metrik palsu. Hasil ST-DBSCAN sudah tersedia pada penelitian; website hanya membacanya. Data yang tampil berasal dari impor/snapshot, bukan feed NASA langsung. Browser tanpa WebGL2 memakai peta cadangan; density memerlukan WebGL2. Windows dan deployment Vercel belum diuji langsung. Status lengkap ada di docs/TEST_REPORT.md.

Untuk demonstrasi dosen, ikuti docs/DEMO_DOSEN.md. Laporan substantif tetap perlu peninjauan dan persetujuan sendiri sesuai instruksi GEMASTIK/dosen. Paket ini belum diunggah ke LMS, GitHub atau Vercel.
