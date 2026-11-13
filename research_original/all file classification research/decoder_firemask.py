"""Persiapan lokal saja. BELUM DIUJI pada HDF nyata; tidak membuat label supervised."""
from pathlib import Path
import re
import numpy as np
def read_daily_planes(path):
    try:from pyhdf.SD import SD,SDC
    except ImportError as e:raise RuntimeError('Paket opsional pyhdf diperlukan untuk HDF4 lokal.') from e
    f=SD(str(Path(path)),SDC.READ)
    try:
        fm=f.select('FireMask');fire=fm.get();qa=f.select('QA').get()
        attrs={**f.attributes(),**fm.attributes()}
        if fire.shape!=qa.shape or fire.ndim!=3:raise ValueError('Periksa dimensi FireMask/QA dan orientasi plane.')
        dates=attrs.get('Dates',attrs.get('DAYSOFYEAR'))
        if dates is None:raise ValueError('Tanggal plane tidak ditemukan; jangan mengasumsikan delapan tanggal.')
        return {'fire':fire,'qa':qa,'date_metadata_raw':dates,'attributes':attrs,
                'status':'Tanggal metadata wajib ditafsirkan dan dicocokkan plane sebelum agregasi; belum otomatis.'}
    finally:f.end()
def summarize_plane(fire,qa,land_area_weights):
    fire=np.asarray(fire);qa=np.asarray(qa);weights=np.asarray(land_area_weights,float)
    if not (fire.shape==qa.shape==weights.shape):raise ValueError('Grid/shape belum aligned.')
    if np.any(weights<0) or weights.sum()<=0:raise ValueError('Bobot luas daratan tidak valid.')
    qa_land=np.isin(qa.astype(np.uint16)&3,[1,2]);clear=qa_land&np.isin(fire,[5,7,8,9]);detected=qa_land&np.isin(fire,[7,8,9])
    return dict(coverage=float(weights[clear].sum()/weights.sum()),fire_cells=int((detected&(weights>0)).sum()),
                clear_nonfire_cells=int(((fire==5)&qa_land&(weights>0)).sum()),cloud_area=float(weights[fire==4].sum()),
                unknown_area=float(weights[fire==6].sum()),unprocessed_area=float(weights[np.isin(fire,[0,1,2])].sum()),
                target_status='NOT_ASSIGNED; coverage threshold and availability not verified')
