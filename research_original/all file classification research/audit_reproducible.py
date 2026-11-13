"""Audit reproduktif. Tidak melatih model pada target yang belum sah."""
from pathlib import Path
import io, json, zipfile, hashlib, platform, importlib.metadata as md
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

SEED = 42
np.random.seed(SEED)
CUTOFF = pd.Timestamp('2026-10-30 23:59:59', tz='UTC')
NASA_URL = 'https://firms.modaps.eosdis.nasa.gov/download/'
VERSION_STATUS = {'6.03':'standard_documented_code_C6',
                  '61.03':'archive_code_unresolved',
                  '6.1NRT':'NRT_documented_code_C61'}

def save_json(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False, default=str))

def sha256(b):
    return hashlib.sha256(b).hexdigest()

def load_raw(source, out):
    """Baca seluruh CSV; tahun berasal dari acq_date, bukan urutan nama."""
    source, out = Path(source), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    if source.is_file() and source.suffix.lower()=='.zip':
        with zipfile.ZipFile(source) as z:
            if z.testzip() is not None: raise ValueError('CRC ZIP gagal')
            blobs=[(Path(n).name,z.read(n)) for n in z.namelist() if n.lower().endswith('.csv')]
        archive_hash=sha256(source.read_bytes())
    elif source.is_dir():
        blobs=[(p.name,p.read_bytes()) for p in sorted(source.glob('*.csv'))]
        archive_hash=None
    else: raise FileNotFoundError(f'ZIP atau folder CSV tidak ditemukan: {source}')
    if not blobs: raise ValueError('Tidak ada CSV dalam sumber')
    if len({n for n,b in blobs})!=len(blobs): raise ValueError('Nama CSV tidak unik')
    frames=[]; manifests=[]; quality=[]; missing=[]
    required=['latitude','longitude','brightness','scan','track','acq_date','acq_time','satellite','instrument','confidence','version','bright_t31','frp','daynight']
    for name, b in blobs:
        d=pd.read_csv(io.BytesIO(b),dtype=str,keep_default_na=False)
        if not set(required).issubset(d): raise ValueError(f'Skema tidak lengkap: {name}')
        original_columns=list(d.columns)
        dt=pd.to_datetime(d.acq_date,errors='coerce')
        ts=pd.to_datetime(d.acq_date+' '+d.acq_time.str.zfill(4),format='%Y-%m-%d %H%M',utc=True,errors='coerce')
        counts=d.version.value_counts().to_dict()
        yr=sorted(dt.dt.year.dropna().astype(int).unique().tolist())
        for y in yr:
            end=min(pd.Timestamp(f'{y}-12-31'),CUTOFF.tz_localize(None).normalize())
            for day in pd.date_range(f'{y}-01-01',end).difference(dt):
                missing.append({'source_file':name,'date':str(day.date()),'interpretation':'tidak ada baris dalam file; coverage belum diketahui'})
        rec={'source_file':name,'bytes':len(b),'sha256':sha256(b),'rows':len(d),
             'year_observed':';'.join(map(str,yr)),'date_min':str(dt.min().date()),'date_max':str(dt.max().date()),
             'timestamp_min_utc':str(ts.min()),'timestamp_max_utc':str(ts.max()),
             'version_values':json.dumps(counts),'instrument_values':json.dumps(d.instrument.value_counts().to_dict()),
             'satellite_values':json.dumps(d.satellite.value_counts().to_dict()),
             'type_values':json.dumps(d['type'].value_counts().to_dict()) if 'type' in d else 'COLUMN_ABSENT',
             'schema':','.join(original_columns),'n_columns':len(original_columns),
             'nrt_documented_pct':100*d.version.eq('6.1NRT').mean(),
             'standard_documented_code_pct':100*d.version.eq('6.03').mean(),
             'unresolved_code_pct':100*(~d.version.isin(['6.03','6.1NRT'])).mean(),
             'product_claim_from_filename':'NRT' if 'nrt' in name else 'archive',
             'NASA_landing_url':NASA_URL,'exact_original_download_url':'UNKNOWN_NOT_PROVIDED',
             'original_download_access_utc':'UNKNOWN_NOT_PROVIDED',
             'audit_access_utc':datetime.now(timezone.utc).isoformat(),
             'provenance_note':'unggahan pengguna; hash menjamin integritas snapshot, bukan autentikasi NASA',
             'distinct_dates':int(dt.nunique()),'invalid_datetime':int(ts.isna().sum()),
             'duplicates_all_original_columns':int(d.duplicated().sum()),'after_cutoff':int(ts.gt(CUTOFF).sum())}
        for c in original_columns:
            quality.append({'source_file':name,'column':c,'empty_cells':int(d[c].eq('').sum()),'structurally_absent':False})
        if 'type' not in d:
            quality.append({'source_file':name,'column':'type','empty_cells':len(d),'structurally_absent':True})
            d['type']=pd.NA
        d['source_file']=name
        d['source_row']=np.arange(2,len(d)+2)
        d['row_id']=name+':L'+d.source_row.astype(str)
        d['acq_datetime_utc']=ts
        d['processing_status']=d.version.map(VERSION_STATUS).fillna('unknown')
        for c in ['latitude','longitude','brightness','scan','track','confidence','bright_t31','frp']:
            d[c]=pd.to_numeric(d[c],errors='coerce')
            rec[c+'_min']=d[c].min();rec[c+'_max']=d[c].max()
            rec[c+'_mean']=d[c].mean();rec[c+'_median']=d[c].median()
            rec[c+'_invalid']=int(d[c].isna().sum())
        manifests.append(rec); frames.append(d)
    all_data=pd.concat(frames,ignore_index=True)
    all_data['year']=all_data.acq_datetime_utc.dt.year
    all_data['month']=all_data.acq_datetime_utc.dt.month
    all_data['date']=all_data.acq_datetime_utc.dt.floor('D')
    valid=(all_data.acq_datetime_utc.notna() & all_data.latitude.between(-90,90) & all_data.longitude.between(-180,180)
           & all_data.confidence.between(0,100)&all_data.frp.ge(0)&all_data.instrument.eq('MODIS'))
    invalid=all_data.loc[~valid].copy()
    invalid.to_csv(out/'baris_tidak_valid.csv',index=False)
    future=all_data.loc[valid & all_data.acq_datetime_utc.gt(CUTOFF)].copy()
    future.to_csv(out/'baris_di_luar_cutoff.csv',index=False)
    clean=all_data.loc[valid & all_data.acq_datetime_utc.le(CUTOFF)].copy()
    key=['latitude','longitude','acq_datetime_utc','satellite','instrument']
    dup=clean.duplicated(key,keep=False)
    clean.loc[dup].to_csv(out/'kandidat_duplikasi.csv',index=False)
    # Jangan menghapus dua pengamatan karena hanya berdekatan dalam ruang/waktu.
    pd.DataFrame(manifests).to_csv(out/'manifest_sumber.csv',index=False)
    pd.DataFrame(quality).to_csv(out/'audit_kelengkapan.csv',index=False)
    pd.DataFrame(missing).to_csv(out/'tanggal_tanpa_baris_per_file.csv',index=False)
    logs=[{'step':'baca semua CSV','input_rows':len(all_data),'removed_rows':0,'output_rows':len(all_data)},
          {'step':'karantina nilai tidak valid','input_rows':len(all_data),'removed_rows':len(invalid),'output_rows':int(valid.sum())},
          {'step':'cutoff 30 Oktober 2026 UTC','input_rows':int(valid.sum()),'removed_rows':len(future),'output_rows':len(clean)}]
    basic={'csv_count':len(blobs),'years':sorted(all_data.year.unique().tolist()),'raw_rows':len(all_data),
           'retained_before_spatial':len(clean),'excluded_cutoff':len(future),'invalid_rows':len(invalid),
           'duplicate_key_rows':int(dup.sum()),'zip_sha256':archive_hash,
           'versions_raw':all_data.version.value_counts().to_dict(),
           'cutoff_requested_utc':str(CUTOFF),'max_actual_timestamp_before_cutoff':str(clean.acq_datetime_utc.max()),
           'coverage_verified':False,'availability_at_prediction_time_verified':False}
    if set(basic['years'])!=set(range(2015,2027)): raise ValueError('Cakupan tahun bukan 2015-2026')
    save_json(out/'audit_ringkas.json',basic)
    print(pd.DataFrame(manifests)[['source_file','rows','date_min','date_max','version_values']].to_string(index=False))
    print('Jumlah CSV:',len(blobs),'Baris asli:',len(all_data),'Di luar cutoff:',len(future))
    return all_data,clean,basic,logs

def prepare_geography(raw_path,out):
    import shapely
    from shapely.geometry import Polygon, mapping
    from pyproj import Geod
    raw_path,out=Path(raw_path),Path(out)
    data=json.loads(raw_path.read_text()); geod=Geod(ellps='WGS84')
    features=[]; audit=[]
    for f in data['features']:
        if f['geometry']['type']!='MultiPolygon': raise ValueError('Skema geometri berubah')
        # Sumber memiliki dimensi Z/M null. Hanya longitude/latitude digunakan.
        polys=[Polygon([v[:2] for v in poly[0]],[[v[:2] for v in ring] for ring in poly[1:]]) for poly in f['geometry']['coordinates']]
        # Komponen daratan utama tiap provinsi = polygon dengan luas geodesik terbesar.
        areas=[abs(geod.geometry_area_perimeter(p)[0]) for p in polys]
        mainland=polys[int(np.argmax(areas))]
        fixed=shapely.make_valid(mainland)
        if fixed.geom_type=='GeometryCollection':
            fixed=shapely.union_all([p for p in fixed.geoms if p.geom_type in ['Polygon','MultiPolygon']])
        if fixed.is_empty or not fixed.is_valid: raise ValueError('Perbaikan geometri gagal')
        props=f['properties']
        audit.append({'province_id':props['KDPPUM'],'province':props['WADMPR'],
                      'components_original':len(polys),'method':'largest_geodesic_area_component_per_province',
                      'valid_before':mainland.is_valid,'valid_after':fixed.is_valid,
                      'area_km2_before':max(areas)/1e6,'area_km2_after':abs(geod.geometry_area_perimeter(fixed)[0])/1e6,
                      'removed_dimensions':'Z/M; horizontal coordinates retained','derived_geometry_type':fixed.geom_type})
        features.append({'type':'Feature','properties':props,'geometry':mapping(fixed)})
    if len(features)!=8: raise ValueError('Diharapkan delapan provinsi daratan utama')
    geo={'type':'FeatureCollection','features':features}
    save_json(out/'sumatera_daratan_utama.geojson',geo)
    pd.DataFrame(audit).to_csv(out/'audit_geometri.csv',index=False)
    return geo

def spatial_join(clean,geo,out,logs):
    import shapely
    from shapely.geometry import shape
    d=clean.copy(); hits=np.zeros(len(d),dtype=np.int16)
    province=np.full(len(d),'',dtype=object);code=np.full(len(d),'',dtype=object)
    for f in geo['features']:
        poly=shape(f['geometry']);shapely.prepare(poly)
        hit=shapely.intersects_xy(poly,d.longitude.to_numpy(),d.latitude.to_numpy())
        hits+=hit;province[hit]=f['properties']['WADMPR'];code[hit]=f['properties']['KDPPUM']
    d['province']=province;d['province_id']=code;d['polygon_matches']=hits
    d.loc[hits>1].to_csv(Path(out)/'baris_batas_ambigu.csv',index=False)
    keep=d.loc[hits==1].copy()
    logs.append({'step':'spatial join daratan utama Sumatera; tepat satu polygon','input_rows':len(d),
                 'removed_rows':int((hits!=1).sum()),'output_rows':len(keep)})
    pd.DataFrame(logs).to_csv(Path(out)/'log_pembersihan.csv',index=False)
    keep.to_csv(Path(out)/'data_sesudah_diolah.csv',index=False)
    print('Deteksi daratan utama Sumatera:',len(keep),'batas ambigu:',int((hits>1).sum()))
    return keep

def describe(d,out):
    out=Path(out);tables=out/'tabel';charts=out/'grafik'
    tables.mkdir(exist_ok=True); charts.mkdir(exist_ok=True)
    for cols,name in [(['year','version'],'jumlah_tahun_versi'),(['year','satellite'],'jumlah_tahun_satelit'),
                      (['year','daynight'],'jumlah_tahun_siang_malam'),(['year','province'],'jumlah_tahun_provinsi'),
                      (['year','type'],'jumlah_tahun_type'),(['year','month','version'],'jumlah_bulan_versi')]:
        d.groupby(cols,dropna=False).size().rename('detections').reset_index().to_csv(tables/(name+'.csv'),index=False)
    d.groupby('year')[['confidence','frp']].agg(['count','mean','median','min','max']).to_csv(tables/'ringkasan_confidence_frp.csv')
    # Tanggal tanpa baris tetap NA. Ini panel AUDIT; belum merupakan sampel klasifikasi.
    units=d[['province_id','province']].drop_duplicates().sort_values('province_id')
    dates=pd.date_range(pd.Timestamp('2015-01-01',tz='UTC'),CUTOFF.normalize())
    idx=pd.MultiIndex.from_product([units.province_id,dates],names=['province_id','date'])
    agg=d.groupby(['province_id','date']).agg(recorded_detection_count=('row_id','size'),
        frp_mean_recorded=('frp','mean'),frp_max_recorded=('frp','max'),confidence_mean_recorded=('confidence','mean'),
        aqua_count_recorded=('satellite',lambda s:s.eq('Aqua').sum()),night_count_recorded=('daynight',lambda s:s.eq('N').sum()))
    panel=agg.reindex(idx).reset_index().merge(units,on='province_id',how='left')
    panel['coverage_status']='UNKNOWN_NO_QA'
    panel['eligible_for_supervised_learning']=False
    panel['no_row_interpretation']=np.where(panel.recorded_detection_count.isna(),'no_record_not_verified_zero','positive_records_coverage_unknown')
    panel.to_csv(out/'data_panel_wilayah_harian.csv',index=False)
    features=panel[['province_id','province','date','coverage_status','eligible_for_supervised_learning']].copy()
    # Cutoff fitur hari t, target di t+1. Tidak ada zero filling atau imputasi.
    for w in [1,3,7,14,30]:
        features[f'count_trailing_{w}d_recorded']=panel.groupby('province_id').recorded_detection_count.transform(lambda s:s.rolling(w,min_periods=w).sum())
    features['change_1d_recorded']=panel.groupby('province_id').recorded_detection_count.diff()
    for c in ['frp_mean_recorded','confidence_mean_recorded']:
        features[c+'_7d']=panel.groupby('province_id')[c].transform(lambda s:s.rolling(7,min_periods=7).mean())
    features['frp_max_recorded_7d']=panel.groupby('province_id').frp_max_recorded.transform(lambda s:s.rolling(7,min_periods=7).max())
    for c in ['aqua_count_recorded','night_count_recorded']:
        numerator=panel.groupby('province_id')[c].transform(lambda s:s.rolling(7,min_periods=7).sum())
        features[c.replace('count','fraction')+'_7d']=numerator/features.count_trailing_7d_recorded
    features['month_t']=features.date.dt.month
    features['target_date']=features.date+pd.Timedelta(days=1)
    features['availability_status']='EVENT_TIME_ONLY_AVAILABLE_AT_UNKNOWN'
    features['y_surge']=pd.Series(pd.NA,index=features.index,dtype='Int64')
    features['candidate_split']=np.select([features.target_date.dt.year<=2023,features.target_date.dt.year==2024,
                                          features.target_date.dt.year==2025,features.target_date.dt.year==2026],
                                         ['train','validation','test_2025','case_2026'],default='outside')
    features['same_split_year_boundary']=features.date.dt.year.eq(features.target_date.dt.year)
    features.to_csv(out/'data_fitur_tanpa_target_bocor.csv',index=False)
    features.to_csv(out/'data_fitur.csv',index=False)
    # Pembagian belum dilaksanakan sebagai data latih/uji: y belum teridentifikasi.
    match=d.loc[(d.year.isin([2024,2025,2026])) & ((d.month<10)|((d.month==10)&(d.date.dt.day<=30)))].copy()
    cmp=match.groupby('year').agg(detections=('row_id','size'),dates_with_rows=('date','nunique'),
           confidence_mean=('confidence','mean'),frp_mean_MW=('frp','mean'),frp_median_MW=('frp','median'),
           nrt_rows=('version',lambda s:s.eq('6.1NRT').sum()),type_missing=('type',lambda s:s.isna().sum()))
    cmp.to_csv(tables/'perbandingan_1Jan_30Okt.csv')
    match.groupby(['year','province']).size().rename('detections').to_csv(tables/'perbandingan_spasial_1Jan_30Okt.csv')
    months=match.groupby(['year','month']).size().unstack(0)
    months.to_csv(tables/'perbandingan_bulanan_1Jan_30Okt.csv')
    style={'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':150}
    plt.rcParams.update(style)
    def finish(fig,name):
        fig.text(.01,.008,'Sumber: CSV unggahan NASA FIRMS; olah aktual. Deteksi tidak sama dengan kejadian atau luas kebakaran.',fontsize=7)
        fig.tight_layout(rect=[0,.035,1,1]);fig.savefig(charts/(name+'.png'),dpi=180);plt.close(fig)
    annual=d.groupby(['year','version']).size().unstack(fill_value=0).reindex(columns=['6.03','61.03','6.1NRT'],fill_value=0)
    fig,ax=plt.subplots(figsize=(8,4));annual.plot.bar(stacked=True,color=['#222222','#888888','#cccccc'],ax=ax)
    ax.set(title='Deteksi daratan utama Sumatera menurut tahun dan versi',xlabel='Tahun; 2026 hanya sampai 30 Oktober',ylabel='Baris deteksi');ax.legend(title='version literal');ax.tick_params(axis='x',rotation=0)
    finish(fig,'01_deteksi_tahunan_versi')
    fig,ax=plt.subplots(figsize=(8,4))
    for y,ls in [(2024,'-'),(2025,'--'),(2026,':')]: ax.plot(months.index,months[y],linestyle=ls,marker='o',color='black',label=str(y))
    ax.set(title='Perbandingan deskriptif pada jendela tanggal yang sama',xlabel='Bulan; Oktober hanya tanggal 1 sampai 30',ylabel='Baris deteksi',xticks=range(1,11));ax.legend()
    finish(fig,'02_bulanan_sebanding')
    sat=d.groupby(['year','satellite']).size().unstack(fill_value=0)
    fig,ax=plt.subplots(figsize=(8,4));sat.div(sat.sum(axis=1),axis=0).mul(100).plot.bar(stacked=True,color=['#444444','#bbbbbb'],ax=ax)
    ax.set(title='Komposisi deteksi Aqua dan Terra',xlabel='Tahun; 2026 parsial',ylabel='Persen dari baris deteksi');ax.tick_params(axis='x',rotation=0)
    finish(fig,'03_komposisi_satelit')
    return panel,features,cmp

def map_plot(d,geo,out):
    from shapely.geometry import shape
    fig,axes=plt.subplots(1,3,figsize=(9,5),sharex=True,sharey=True)
    for ax,y in zip(axes,[2024,2025,2026]):
        for f in geo['features']:
            poly=shape(f['geometry']);poly=poly.simplify(.002,preserve_topology=True) # visual saja; join tanpa simplifikasi
            parts=[poly] if poly.geom_type=='Polygon' else list(poly.geoms)
            for p in parts:
                x,z=p.exterior.xy;ax.plot(x,z,color='#999999',lw=.4)
        sub=d.loc[(d.year==y)&((d.month<10)|((d.month==10)&(d.date.dt.day<=30)))]
        ax.scatter(sub.longitude,sub.latitude,s=.25,color='black',alpha=.25,rasterized=True)
        ax.set_title(f'{y}\nn = {len(sub):,}'.replace(',','.'));ax.set_xlabel('Bujur (derajat)');ax.set_aspect('equal')
    axes[0].set_ylabel('Lintang (derajat)')
    fig.suptitle('Sebaran deteksi 1 Januari sampai 30 Oktober',fontsize=12)
    fig.text(.02,.02,'Sumber: CSV FIRMS unggahan; batas BIG, komponen daratan utama. Semua titik ditampilkan; bukan peta prediksi.',fontsize=7)
    fig.tight_layout(rect=[0,.05,1,.92]);fig.savefig(Path(out)/'grafik/04_peta_deteksi.png',dpi=200);plt.close(fig)

def manual_example(d,out):
    s=d.loc[d.year.eq(2015)].sort_values(['acq_datetime_utc','source_row']).head(10).copy()
    # Latihan rumus pada kategori type asli, bukan label lonjakan t+1.
    def entropy(v):
        p=v.value_counts(normalize=True).to_numpy();return float(-(p*np.log2(p)).sum())
    def gini(v):
        p=v.value_counts(normalize=True).to_numpy();return float(1-(p*p).sum())
    threshold=float(s.confidence.median());left=s.confidence.le(threshold)
    child_h=sum(mask.mean()*entropy(s.loc[mask,'type']) for mask in [left,~left] if mask.any())
    child_g=sum(mask.mean()*gini(s.loc[mask,'type']) for mask in [left,~left] if mask.any())
    result={'purpose':'Latihan CART pada type asli; BUKAN hasil klasifikasi lonjakan atau penentuan target utama',
            'selection':'10 deteksi pertama daratan utama Sumatera tahun 2015; urut waktu UTC lalu source_row',
            'n':len(s),'class_counts':s.type.value_counts().to_dict(),'split_attribute':'confidence',
            'split_threshold':threshold,'parent_entropy_bits':entropy(s.type),'parent_gini':gini(s.type),
            'left_n':int(left.sum()),'left_counts':s.loc[left,'type'].value_counts().to_dict(),
            'right_n':int((~left).sum()),'right_counts':s.loc[~left,'type'].value_counts().to_dict(),
            'weighted_child_entropy':child_h,'information_gain_bits':entropy(s.type)-child_h,
            'weighted_child_gini':child_g,'gini_decrease':gini(s.type)-child_g}
    s[['row_id','source_file','source_row','acq_date','acq_time','province','latitude','longitude','confidence','frp','type']].to_csv(Path(out)/'contoh_manual_10_baris.csv',index=False)
    s.head(5).to_csv(Path(out)/'contoh_5_baris_sesudah.csv',index=False)
    save_json(Path(out)/'perhitungan_manual.json',result)
    print(json.dumps(result,indent=2));return result

def research_gate(out,basic,d,panel,features):
    out=Path(out)
    reasons=['Coverage wilayah-hari dan cloud/fire mask tidak tersedia; nol yang sah belum teridentifikasi.',
             'Makna kode 61.03 dan konflik 6.03 versus nama M-C61 belum selesai diaudit dengan metadata ekspor.',
             'Waktu ketersediaan data (available_at), parameter permintaan unduh, dan bukti kelengkapan ekspor belum tersedia.',
             'Rubrik UTS resmi tidak dilampirkan; empat PDF adalah materi/latihan.']
    status={'status':'AUDIT_AND_EDA_EXECUTED_MODEL_NOT_EXECUTED','seed':SEED,'blocking_reasons':reasons,
            'spatial_scope':'largest geodesic polygon of each of eight mainland Sumatra provinces; small offshore islands excluded',
            'n_sumatra_detections':len(d),'panel_candidate_rows':len(panel),
            'panel_dates_without_records':int(panel.recorded_detection_count.isna().sum()),
            'eligible_model_rows':0,'target_threshold_fitted':False,'model_fitted':False,'test_2025_evaluated':False,
            'case_2026_evaluated':False,'2026_descriptive_only':True,
            'meteorology_in_model':False,'nrt_sumatra_rows':int(d.version.eq('6.1NRT').sum()),
            'source_timestamp_not_availability_timestamp':True,'study_2026_max_observed_utc':str(d.loc[d.year.eq(2026),'acq_datetime_utc'].max())}
    save_json(out/'status_eksekusi.json',status)
    label={'status':'BELUM_DIFIT_BELUM_ADA_LABEL_SAH','target':'lonjakan deteksi tercatat wilayah pada t+1',
           'formula':'y[g,t+1] = 1{N[g,t+1] > q[g,0.90,training]} only if coverage and export completeness are verified; else NA',
           'quantile_definition':'higher; per wilayah, hanya hitungan harian positif training yang coverage-nya sah',
           'primary_quantile_proposed':0.90,'sensitivity_quantiles_proposed':[0.80,0.95],
           'numeric_thresholds':None,'training_years':[2015,2023],'validation_year':2024,'final_test_year':2025,
           'case_year':2026,'cutoff_utc':str(CUTOFF),'negative_class_definition':'0 berarti tidak melampaui ambang pada pengamatan layak, bukan tidak ada api',
           'time_design':'Origin at end of UTC day t, predicting UTC day t+1. Only records available by origin may be features.',
           'notebook_behavior':'No fitting, target fabrication, zero-fill or fake predictions when prerequisites are missing.'}
    save_json(out/'label_definisi.json',label)
    versions={'python':platform.python_version()}
    for package in ['pandas','numpy','matplotlib','scikit-learn','joblib','shapely','pyproj','nbformat','nbclient','ipykernel','xgboost','shap']:
        try:versions[package]=md.version(package)
        except md.PackageNotFoundError:versions[package]='NOT_INSTALLED'
    save_json(out/'versi_lingkungan.json',versions)
    print('PEMODELAN BELUM DIEKSEKUSI. Audit dan EDA selesai. Tidak ada model atau metrik final.')
    return status

def run(source,polygon_path,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    all_data,clean,basic,logs=load_raw(source,out)
    geo=prepare_geography(polygon_path,out)
    d=spatial_join(clean,geo,out,logs)
    panel,features,cmp=describe(d,out)
    map_plot(d,geo,out)
    manual=manual_example(d,out)
    # Simpan lima baris sumber secara verbatim sesuai row id sebelum konversi tipe.
    wanted=d.loc[d.year.eq(2015)].sort_values(['acq_datetime_utc','source_row']).head(5)
    src=Path(source)
    examples=[]
    if src.suffix.lower()=='.zip':
        with zipfile.ZipFile(src) as z:
            for n,g in wanted.groupby('source_file'):
                original=pd.read_csv(io.BytesIO(z.read(n)),dtype=str,keep_default_na=False)
                picked=original.iloc[(g.source_row-2).to_numpy()].copy()
                picked.insert(0,'row_id',g.row_id.to_numpy());examples.append(picked)
    else:
        for n,g in wanted.groupby('source_file'):
            original=pd.read_csv(src/n,dtype=str,keep_default_na=False)
            picked=original.iloc[(g.source_row-2).to_numpy()].copy();picked.insert(0,'row_id',g.row_id.to_numpy());examples.append(picked)
    pd.concat(examples).to_csv(out/'contoh_5_baris_sebelum.csv',index=False)
    status=research_gate(out,basic,d,panel,features)
    assert len(d)==panel.recorded_detection_count.sum()
    assert not features.eligible_for_supervised_learning.any()
    assert features.y_surge.isna().all()
    assert d.acq_datetime_utc.max()<=CUTOFF
    save_json(out/'assertions.json',{'sum_daily_matches_detections':True,'zero_eligible_rows':True,'no_fabricated_labels':True,'cutoff_ok':True})
    return basic,status,manual

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--polygon',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();run(a.source,a.polygon,a.out)
