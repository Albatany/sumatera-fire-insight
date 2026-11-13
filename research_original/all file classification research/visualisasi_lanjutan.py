from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from shapely.geometry import shape
def plot_all(base):
 base=Path(base);out=base/'clustering/grafik';out.mkdir(exist_ok=True)
 a=pd.read_csv(base/'clustering/hasil_st_dbscan.csv',dtype={'version':str,'type':str});s=pd.read_csv(base/'clustering/sensitivitas_27_skenario.csv');c=pd.read_csv(base/'clustering/ringkasan_klaster.csv');p=pd.read_csv(base/'clustering/hasil_utama_per_strata.csv')
 plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
 source='Sumber: 13 CSV FIRMS unggahan; olah ST-DBSCAN; mask BIG. Bukan jumlah kejadian atau luas kebakaran.'
 def save(fig,name,title):
  fig.suptitle(title);fig.text(.015,.015,source,fontsize=8)
  # Reserve extra bottom space for square heatmaps and their x-axis labels.
  bottom = .14 if name == '02_sensitivitas_noise.png' else .055
  fig.tight_layout(rect=[0,bottom,1,.94]);fig.savefig(out/name,dpi=170);plt.close(fig)
 fig,ax=plt.subplots(2,1,figsize=(10,7),sharex=True);ax[0].bar(p.partition,p.clusters,color='.25');ax[0].set_ylabel('Jumlah klaster');ax[1].bar(p.partition,p.noise_percent,color='.6');ax[1].set_ylabel('Noise (%)');ax[1].tick_params(axis='x',rotation=55)
 save(fig,'01_klaster_noise_per_strata.png','Hasil utama menurut tahun dan version literal')
 fig,axes=plt.subplots(1,3,figsize=(11,4.4))
 for ax,m in zip(axes,[3,5,10]):
  mat=s[s.min_samples.eq(m)].pivot(index='eps_temporal_hours',columns='eps_spatial_km',values='noise_percent').sort_index()
  ax.imshow(mat,origin='lower',cmap='Greys',vmin=20,vmax=100);ax.set_xticks(range(3),[1,2,5]);ax.set_yticks(range(3),[24,48,72]);ax.set_title(f'min_samples = {m}');ax.set_xlabel('Jarak spasial (km)')
  for i in range(3):
   for j in range(3):ax.text(j,i,f'{mat.iloc[i,j]:.1f}%',ha='center',va='center',color='white' if mat.iloc[i,j]>58 else 'black')
 axes[0].set_ylabel('Jarak waktu (jam)');save(fig,'02_sensitivitas_noise.png','Sensitivitas noise pada 27 konfigurasi')
 geo=json.loads((base/'hasil/sumatera_daratan_utama.geojson').read_text());fig,axes=plt.subplots(1,3,figsize=(10,6.5),sharex=True,sharey=True)
 for ax,year in zip(axes,[2015,2025,2026]):
  for feat in geo['features']:
   g=shape(feat['geometry']).simplify(.01);parts=list(g.geoms) if g.geom_type=='MultiPolygon' else [g]
   for x in parts:ax.plot(*x.exterior.xy,color='.65',lw=.4)
  for role,color,size in [('noise','.8',2),('border','.4',3),('core','black',3)]:
   b=a[(a.year==year)&a.point_role.eq(role)];ax.scatter(b.longitude,b.latitude,s=size,c=color,label=role,alpha=.6)
  ax.set_aspect('equal');ax.set_title(str(year)+(' parsial' if year==2026 else ''));ax.set_xlabel('Bujur (derajat)')
 axes[0].set_ylabel('Lintang (derajat)');axes[1].legend(loc='lower left',fontsize=8);save(fig,'03_peta_peran_titik.png','Sebaran core border dan noise; 2026 sampai 30 Oktober')
 fig,axes=plt.subplots(1,2,figsize=(10,4.5));axes[0].hist(c.duration_days,bins=40,color='.35');axes[0].axvline(2,ls='--',c='black',label='eps waktu 2 hari');axes[0].legend();axes[0].set_ylabel('Jumlah klaster');axes[1].scatter(c.duration_days,c.detections,s=9,c='black',alpha=.4);axes[1].set_yscale('log');axes[1].set_ylabel('Deteksi (skala log)')
 for ax in axes:ax.set_xlabel('Durasi klaster (hari)')
 save(fig,'04_durasi_ukuran_klaster.png','Efek rantai ketetanggaan pada durasi klaster')
 top=c.nlargest(6,'detections').iloc[::-1];fig,ax=plt.subplots(figsize=(10,4.5));left=np.zeros(len(top))
 for key,color in [('type_0','.8'),('type_1','.6'),('type_2','.25'),('type_3','black'),('type_unknown','.95')]:
  ax.barh(top.cluster_id,top[key],left=left,color=color,edgecolor='.4',label=key.replace('_',' '));left+=top[key]
 ax.set_xlabel('Jumlah deteksi');ax.legend(loc='lower right',fontsize=8);save(fig,'05_type_klaster_terbesar.png','Komposisi type pada enam klaster terbesar')
 big=c.nlargest(1,'detections').iloc[0];b=a[a.cluster_id.eq(big.cluster_id)];fig,axes=plt.subplots(1,2,figsize=(10,4.8));axes[0].scatter(b.longitude,b.latitude,s=3,c='black',alpha=.3);axes[0].set_xlabel('Bujur');axes[0].set_ylabel('Lintang');t=b.groupby('acq_date').size();axes[1].plot(pd.to_datetime(t.index),t.values,c='black');axes[1].tick_params(axis='x',rotation=45);axes[1].set_ylabel('Deteksi per tanggal tercatat')
 save(fig,'06_rincian_klaster_terbesar.png',f'{big.cluster_id}: {big.detections} deteksi; {big.duration_days:.2f} hari')
 fig,axes=plt.subplots(1,2,figsize=(10,4.5));axes[0].hist(a.confidence,bins=20,color='.4');axes[0].set_xlabel('Confidence MODIS');axes[1].hist(np.log1p(a.frp),bins=35,color='.4');axes[1].set_xlabel('log(1 + FRP dalam MW)')
 for ax in axes:ax.set_ylabel('Jumlah deteksi')
 save(fig,'07_distribusi_confidence_frp.png','Distribusi confidence dan FRP deteksi terpilih')
 return out
if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--base',type=Path,default=Path.cwd());plot_all(ap.parse_args().base)
