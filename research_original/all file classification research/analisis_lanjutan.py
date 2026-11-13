"""ST-DBSCAN dua ambang, audit ulang, dan gerbang classification; raw read-only."""
from pathlib import Path
import json,io,hashlib,zipfile,time,platform,importlib.util,importlib.metadata as meta
from datetime import datetime,timezone
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.cluster import DBSCAN
from sklearn.neighbors import BallTree
from sklearn.metrics import adjusted_rand_score,silhouette_score
from sklearn.metrics.pairwise import haversine_distances
SEED=42;R_KM=6371.0088;PRIMARY=(2.,48.,5)
CUTOFF=pd.Timestamp('2026-10-30 23:59:59',tz='UTC')
GRID=[(s,t,m) for s in (1.,2.,5.) for t in (24.,48.,72.) for m in (3,5,10)]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def save_json(p,obj):Path(p).write_text(json.dumps(obj,indent=2,ensure_ascii=False,default=str))
def audit_again(base):
 base=Path(base);out=base/'clustering';out.mkdir(exist_ok=True)
 protocol=out/'protokol_sebelum_eksperimen.json'
 if not protocol.exists():save_json(protocol,dict(primary=PRIMARY,sensitivity_grid=GRID,seed=SEED,partition='tahun UTC dan version literal',metric='haversine and absolute UTC hours',scope='all valid retained detections; not confirmed vegetation fires',rationale='2 km beberapa piksel nominal; 48 jam lintasan berulang; 5 rekaman termasuk diri; eksploratif',recovery_note='Parameter dipertahankan dari eksperimen sesi sebelumnya; berkas dipulihkan dengan eksekusi ulang, bukan pemilihan ulang berdasarkan hasil',created_utc=datetime.now(timezone.utc).isoformat()))
 for rel,digest in json.loads((base/'checkpoint_sha256.json').read_text()).items():assert sha(base/rel)==digest,rel
 raw=base/'data_sebelum_diolah/NASA_MODIS_2015_2026_RAW.zip'
 expected=json.loads((base/'hasil/audit_ringkas.json').read_text());assert sha(raw)==expected['zip_sha256']
 old=pd.read_csv(base/'hasil/manifest_sumber.csv',dtype=str).set_index('source_file')
 rows=[];allkeys=[]
 with zipfile.ZipFile(raw) as z:
  assert z.testzip() is None
  for n in sorted(n for n in z.namelist() if n.lower().endswith('.csv')):
   b=z.read(n);a=pd.read_csv(io.BytesIO(b),dtype=str,keep_default_na=False);h=hashlib.sha256(b).hexdigest()
   assert h==old.loc[Path(n).name,'sha256'] and len(a)==int(old.loc[Path(n).name,'rows'])
   ts=pd.to_datetime(a.acq_date+' '+a.acq_time.str.zfill(4),format='%Y-%m-%d %H%M',utc=True)
   key=pd.DataFrame(dict(latitude=pd.to_numeric(a.latitude),longitude=pd.to_numeric(a.longitude),time=ts,satellite=a.satellite,instrument=a.instrument,source_file=n));allkeys.append(key)
   rows.append(dict(source_file=n,sha256=h,hash_match_previous=True,rows=len(a),exact_duplicates_within_file=int(a.duplicated().sum()),date_min=str(ts.min()),date_max=str(ts.max()),versions_literal=json.dumps(a.version.value_counts().to_dict()),nrt_documented_rows=int(a.version.eq('6.1NRT').sum()),standard_documented_code_rows=int(a.version.eq('6.03').sum()),archive_unresolved_6103_rows=int(a.version.eq('61.03').sum()),original_download_url='BELUM_DIBERIKAN',original_access_time='BELUM_DIBERIKAN'))
 pd.DataFrame(rows).to_csv(out/'audit_ulang_13_csv.csv',index=False)
 keys=pd.concat(allkeys,ignore_index=True);dup=keys.duplicated(['latitude','longitude','time','satellite','instrument'],keep=False)
 keys.loc[dup].to_csv(out/'duplikasi_kunci_audit_ulang.csv',index=False)
 d=pd.read_csv(base/'hasil/data_sesudah_diolah.csv',dtype={'version':str,'type':str},low_memory=False)
 d['acq_datetime_utc']=pd.to_datetime(d.acq_datetime_utc,utc=True)
 assert len(d)==154184 and d.row_id.is_unique and d.acq_datetime_utc.max()<=CUTOFF
 d=d.sort_values(['year','version','acq_datetime_utc','row_id']).reset_index(drop=True);d['partition']=d.year.astype(str)+'__'+d.version
 d['boundary_near_72h']=False
 for _,g in d.groupby('partition'):
  y=int(g.year.iloc[0]);v=g.version.iloc[0];lo=pd.Timestamp(f'{y}-01-01',tz='UTC');hi=min(pd.Timestamp(f'{y+1}-01-01',tz='UTC'),CUTOFF+pd.Timedelta(seconds=1))
  if y==2026 and v=='61.03':hi=pd.Timestamp('2026-09-01',tz='UTC')
  if y==2026 and v=='6.1NRT':lo=pd.Timestamp('2026-09-01',tz='UTC')
  d.loc[g.index,'boundary_near_72h']=((g.acq_datetime_utc-lo).dt.total_seconds()<=259200)|((hi-g.acq_datetime_utc).dt.total_seconds()<=259200)
 save_json(out/'audit_ulang_ringkas.json',dict(csv_count=len(rows),raw_rows=len(keys),exact_key_duplicates=int(dup.sum()),unchanged_raw=True,raw_zip_sha256=sha(raw),retained_detections=len(d),processed_csv_sha256=sha(base/'hasil/data_sesudah_diolah.csv'),unresolved_version='61.03',access_utc=datetime.now(timezone.utc).isoformat()))
 return d
def build_edges(g,max_space=5.,max_hours=72.):
 xy=np.radians(g[['latitude','longitude']].to_numpy(float));hours=g.acq_datetime_utc.astype('int64').to_numpy()/3.6e12
 tree=BallTree(xy,metric='haversine');rr=[];cc=[];ss=[];tt=[]
 for start in range(0,len(g),256):
  ind,dist=tree.query_radius(xy[start:start+256],r=max_space/R_KM,return_distance=True)
  for off,(js,dd) in enumerate(zip(ind,dist)):
   i=start+off;dt=np.abs(hours[js]-hours[i]);ok=dt<=max_hours
   rr.append(np.full(ok.sum(),i,dtype=np.int32));cc.append(js[ok].astype(np.int32));ss.append(dd[ok]*R_KM);tt.append(dt[ok])
 return tuple(np.concatenate(x) for x in (rr,cc,ss,tt))
def fit_edges(n,edges,s,t,m):
 row,col,space,hours=edges;ok=(space<=s)&(hours<=t)
 graph=csr_matrix((np.ones(ok.sum()),(row[ok],col[ok])),shape=(n,n));graph.sort_indices();assert np.all(graph.diagonal()==1)
 fit=DBSCAN(eps=1.,min_samples=m,metric='precomputed',n_jobs=1).fit(graph)
 core=np.zeros(n,bool);core[fit.core_sample_indices_]=True
 return fit.labels_,core,graph
def params(s,t,m):return f's{int(s)}_h{int(t)}_m{m}'
def run_clustering(base,d):
 out=Path(base)/'clustering';start=time.monotonic();configs=[PRIMARY]+[p for p in GRID if p!=PRIMARY]
 labelsall={params(*p):np.full(len(d),-1,dtype=np.int32) for p in configs};offsets={k:0 for k in labelsall};coreall=np.zeros(len(d),bool)
 rows=[];sils=[];silrows=[];qualities=[]
 for part,g0 in d.groupby('partition',sort=True):
  ids=g0.index.to_numpy();g=g0.reset_index(drop=True);edges=build_edges(g)
  for s,t,m in configs:
   label,core,graph=fit_edges(len(g),edges,s,t,m);key=params(s,t,m);ncl=int(label.max()+1);yes=label>=0
   global_l=label.copy();global_l[yes]+=offsets[key];offsets[key]+=ncl;labelsall[key][ids]=global_l
   durations=g.assign(label=label).loc[yes].groupby('label').acq_datetime_utc.agg(['min','max']);days=(durations['max']-durations['min']).dt.total_seconds()/86400
   sizes=np.bincount(label[yes]) if yes.any() else np.array([0])
   rows.append(dict(partition=part,config=key,eps_spatial_km=s,eps_temporal_hours=t,min_samples=m,n=len(g),clusters=ncl,noise=int((~yes).sum()),core=int(core.sum()),border=int((yes&~core).sum()),largest_cluster=int(sizes.max()),max_duration_days=float(days.max()) if len(days) else 0.))
   if (s,t,m)==PRIMARY:primary_label=label.copy();coreall[ids]=core
  valid=np.flatnonzero(primary_label>=0);pick=np.sort(np.random.default_rng(SEED).choice(valid,min(1500,len(valid)),replace=False));score=None
  if 2<=len(np.unique(primary_label[pick]))<len(pick):
   xy=np.radians(g.loc[pick,['latitude','longitude']].to_numpy());h=g.loc[pick,'acq_datetime_utc'].astype('int64').to_numpy()/3.6e12
   dist=np.maximum(haversine_distances(xy)*R_KM/PRIMARY[0],np.abs(h[:,None]-h[None,:])/PRIMARY[1]);np.fill_diagonal(dist,0)
   score=float(silhouette_score(dist,primary_label[pick],metric='precomputed'))
  sils.append(dict(partition=part,nonnoise_n=len(valid),sample_n=len(pick),silhouette=score,seed=SEED))
  silrows.extend([{'partition':part,'row_id':g.row_id.iloc[i]} for i in pick])
  filters={'confidence_ge30':g.confidence>=30,'confidence_ge80':g.confidence>=80,'Terra_only':g.satellite.eq('Terra'),'Aqua_only':g.satellite.eq('Aqua')}
  if g.type.notna().any():filters['type0_only']=g.type.eq('0')
  for name,mask in filters.items():
   ix=np.flatnonzero(mask.to_numpy());q=g.iloc[ix].reset_index(drop=True)
   if len(q):
    ll,_,_=fit_edges(len(q),build_edges(q),*PRIMARY);yes=ll>=0;sizes=np.bincount(ll[yes]) if yes.any() else np.array([0])
    qualities.append(dict(partition=part,scenario=name,n=len(q),clusters=int(ll.max()+1),noise=int((~yes).sum()),largest_cluster=int(sizes.max()),ARI_primary_on_same_rows=float(adjusted_rand_score(primary_label[ix],ll))))
 primary=labelsall[params(*PRIMARY)];result=d.copy();result['cluster_label']=primary
 result['cluster_id']=np.where(primary<0,'NOISE',[f'ST{x:05d}' for x in primary]);result['point_role']=np.where(primary<0,'noise',np.where(coreall,'core','border'))
 result.to_csv(out/'hasil_st_dbscan.csv',index=False)
 pd.DataFrame({'row_id':d.row_id,**labelsall}).to_csv(out/'keanggotaan_27_skenario.csv',index=False)
 per=pd.DataFrame(rows);per.to_csv(out/'sensitivitas_per_strata.csv',index=False)
 base_rows=per[per.config.eq(params(*PRIMARY))].copy();base_rows['noise_percent']=base_rows.noise/base_rows.n*100;base_rows.to_csv(out/'hasil_utama_per_strata.csv',index=False)
 totals=[]
 for s,t,m in configs:
  key=params(s,t,m);a=per[per.config.eq(key)];ll=labelsall[key];both=(primary>=0)&(ll>=0)
  totals.append(dict(config=key,eps_spatial_km=s,eps_temporal_hours=t,min_samples=m,**{k:int(a[k].sum()) for k in ['n','clusters','noise','core','border']},largest_cluster=int(a.largest_cluster.max()),max_duration_days=float(a.max_duration_days.max()),noise_percent=float((ll<0).mean()*100),ARI_including_noise=float(adjusted_rand_score(primary,ll)),ARI_common_nonnoise=float(adjusted_rand_score(primary[both],ll[both])) if both.any() else None,common_nonnoise_n=int(both.sum())))
 sensitivity=pd.DataFrame(totals);sensitivity.to_csv(out/'sensitivitas_27_skenario.csv',index=False)
 summary=[]
 for cluster,g in result[result.cluster_label>=0].groupby('cluster_id',sort=True):
  lat=g.latitude.mean();lon=g.longitude.mean();radius=haversine_distances(np.radians([[lat,lon]]),np.radians(g[['latitude','longitude']].to_numpy()))[0]*R_KM
  a=dict(cluster_id=cluster,partition=g.partition.iloc[0],detections=len(g),start_utc=str(g.acq_datetime_utc.min()),end_utc=str(g.acq_datetime_utc.max()),duration_days=(g.acq_datetime_utc.max()-g.acq_datetime_utc.min()).total_seconds()/86400,centroid_latitude=lat,centroid_longitude=lon,max_radius_km=radius.max(),dominant_province=g.province.mode().iloc[0],provinces=';'.join(sorted(g.province.unique())),confidence_mean=g.confidence.mean(),frp_mean_MW=g.frp.mean(),frp_max_MW=g.frp.max(),near_boundary_n=int(g.boundary_near_72h.sum()))
  a.update({f'type_{v}':int(g.type.eq(str(v)).sum()) for v in range(4)});a['type_unknown']=int(g.type.isna().sum());summary.append(a)
 summary=pd.DataFrame(summary);summary.to_csv(out/'ringkasan_klaster.csv',index=False);summary.nlargest(15,'detections').to_csv(out/'klaster_terbesar_15.csv',index=False)
 pd.DataFrame(qualities).to_csv(out/'sensitivitas_kualitas_satelit_type.csv',index=False);pd.DataFrame(sils).to_csv(out/'silhouette_diagnostik.csv',index=False);pd.DataFrame(silrows).to_csv(out/'row_id_sampel_silhouette.csv',index=False)
 result.groupby(['year','version','province','point_role']).size().rename('detections').reset_index().to_csv(out/'keanggotaan_per_wilayah.csv',index=False)
 save_json(out/'ringkasan_eksperimen.json',dict(n=len(d),clusters=len(summary),noise=int((primary<0).sum()),noise_percent=float((primary<0).mean()*100),core=int(coreall.sum()),border=int(((primary>=0)&~coreall).sum()),largest_cluster=int(summary.detections.max()),max_duration_days=float(summary.duration_days.max()),strata=len(base_rows),configurations=len(configs),elapsed_seconds=round(time.monotonic()-start,2),classification_model_fitted=False))
 return result,summary,sensitivity
def validate_implementation(base,d):
 base=Path(base);out=base/'clustering';pool=d[(d.year==2015)&(d.month==9)].copy();center=pool[['latitude','longitude']].median().to_numpy()
 distance=haversine_distances(np.radians([center]),np.radians(pool[['latitude','longitude']].to_numpy()))[0]
 g=pool.iloc[np.argsort(distance,kind='stable')[:1000]].sort_values(['acq_datetime_utc','row_id']).reset_index(drop=True)
 ll,core,graph=fit_edges(len(g),build_edges(g),*PRIMARY);xy=np.radians(g[['latitude','longitude']].to_numpy());h=g.acq_datetime_utc.astype('int64').to_numpy()/3.6e12
 full=np.maximum(haversine_distances(xy)*R_KM/2,np.abs(h[:,None]-h[None,:])/48);np.fill_diagonal(full,0);dense=DBSCAN(eps=1,min_samples=5,metric='precomputed').fit(full)
 assert adjusted_rand_score(ll,dense.labels_)==1 and np.array_equal(np.flatnonzero(core),np.sort(dense.core_sample_indices_)) and (graph!=graph.T).nnz==0
 upstream=base/'sources/st_dbscan_upstream.py';spec=importlib.util.spec_from_file_location('reference_stdbscan',upstream);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 lat,lon=xy.T;xyz=R_KM*np.column_stack([np.cos(lat)*np.cos(lon),np.cos(lat)*np.sin(lon),np.sin(lat)])
 ref=mod.ST_DBSCAN(eps1=2*R_KM*np.sin(2/(2*R_KM)),eps2=48,min_samples=5,metric='euclidean').fit(np.column_stack([h,xyz]));ari=float(adjusted_rand_score(ll,ref.labels));assert ari==1
 order=np.random.default_rng(SEED).permutation(len(g));shuffled,_,_=fit_edges(len(g),build_edges(g.iloc[order].reset_index(drop=True)),*PRIMARY);restored=np.empty(len(g),int);restored[order]=shuffled
 record=dict(actual_rows=len(g),dense_vs_sparse_ARI=1.,upstream_reference_ARI=ari,core_indices_identical=True,symmetric_neighborhood=True,permuted_order_ARI=float(adjusted_rand_score(ll,restored)),permuted_order_core_ARI=float(adjusted_rand_score(ll[core],restored[core])),permuted_order_noise_membership_equal=bool(np.array_equal(ll<0,restored<0)),cluster_count_in_sample=int(ll.max()+1),synthetic_data_used=False,upstream_sha256=sha(upstream))
 save_json(out/'validasi_implementasi.json',record);g[['row_id','latitude','longitude','acq_datetime_utc']].to_csv(out/'row_id_validasi_implementasi.csv',index=False)
 i=int(np.flatnonzero(core)[0]);ix=np.flatnonzero(full[i]<=1)[:10];ex=g.loc[ix,['row_id','latitude','longitude','acq_datetime_utc']].copy();ex.insert(0,'anchor_row_id',g.row_id.iloc[i]);ex['distance_km']=haversine_distances(xy[[i]],xy[ix])[0]*R_KM;ex['time_difference_hours']=abs(h[ix]-h[i]);ex['anchor_total_neighbors_including_self']=int((full[i]<=1).sum());ex.to_csv(out/'contoh_manual_tetangga_nyata.csv',index=False)
 return record
def classification_gate(base):
 base=Path(base);out=base/'clustering';p=pd.read_csv(base/'hasil/data_panel_wilayah_harian.csv');f=pd.read_csv(base/'hasil/data_fitur.csv')
 f['date']=pd.to_datetime(f.date,utc=True);f['target_date']=pd.to_datetime(f.target_date,utc=True)
 def split(s):return np.select([s.dt.year<=2023,s.dt.year==2024,s.dt.year==2025,s.dt.year==2026],['train','validation','test_2025','case_2026'],default='outside')
 f['origin_split']=split(f.date);f['target_split']=split(f.target_date);f['same_subset']=f.origin_split.eq(f.target_split);f['target_within_cutoff']=f.target_date.le(CUTOFF.normalize());f['calendar_lookback_30d']=f.date.ge(pd.Timestamp('2015-01-30',tz='UTC'));f['candidate_time_eligible']=f.same_subset&f.target_within_cutoff&f.calendar_lookback_30d;f['eligible_for_supervised_learning']=False;f['y_surge']=np.nan
 f.to_csv(out/'calon_fitur_dengan_gate_temporal.csv',index=False);rows=[]
 for key,g in f.groupby('target_split'):rows.append(dict(subset=key,calendar_rows=len(g),time_eligible_before_QA=int(g.candidate_time_eligible.sum()),complete_recorded_30d_feature=int(g.count_trailing_30d_recorded.notna().sum()),coverage_verified_rows=0,availability_verified_rows=0,eligible_labeled_rows=0,positive_class_count=None,negative_class_count=None,prevalence=None))
 pd.DataFrame(rows).to_csv(out/'kelayakan_classification_per_split.csv',index=False);p.recorded_detection_count.dropna().describe(percentiles=[.5,.8,.9,.95,.99]).to_csv(out/'distribusi_hitung_positif_bukan_target.csv')
 gate=dict(classification_feasible=False,reason_codes=['QA_NOT_AVAILABLE','AVAILABLE_AT_UNKNOWN','PROVENANCE_UNRESOLVED'],negative_labels_created=0,target_quantiles_fitted=False,model_fitted=False,test2025_evaluated=False,cluster_ids_used_as_features=False,cluster_noise_used_as_negative_labels=False,candidate_rows=len(p),region_days_without_records=int(p.recorded_detection_count.isna().sum()))
 save_json(out/'keputusan_classification.json',gate);versions={'python':platform.python_version()}
 for name in ['numpy','pandas','scipy','scikit-learn','matplotlib','shapely','pyproj','nbformat','ipython','xgboost','shap']:
  try:versions[name]=meta.version(name)
  except meta.PackageNotFoundError:versions[name]='NOT_INSTALLED'
 save_json(out/'versi_lingkungan_revisi.json',versions);return gate
if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--base',type=Path,default=Path.cwd());base=ap.parse_args().base
 d=audit_again(base);print(validate_implementation(base,d));run_clustering(base,d);print(classification_gate(base))
