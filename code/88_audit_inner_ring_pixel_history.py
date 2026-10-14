"""Descriptive, aligned CDL histories, 2013-2025, exclusive 0-25 miles.

Tile checkpoints resume without repeated successful downloads. Requests that
fail raise; missing coverage never becomes a land-cover zero. No regressions.
"""
import argparse, hashlib, importlib.util, json
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.features import geometry_mask
from shapely.geometry import box, mapping

ROOT=Path(__file__).resolve().parents[1]
YEARS=list(range(2013,2026))
ACRES=900/4046.8564224
OUT=ROOT/'pixel-history-results'
spec=importlib.util.spec_from_file_location('extract',ROOT/'code/07_extract_cdl_raster_band.py')
extract=importlib.util.module_from_spec(spec); spec.loader.exec_module(extract)

def valid(data,mask):
    return mask & (data>0) & (data!=81)

def analyse(stack,good,inside,peak):
    """Counters on annual/pairwise and complete-series support, kept separate."""
    n=len(YEARS)
    annual=np.zeros((n,256),dtype='int64')
    pairs=np.zeros((n-1,256,256),dtype='int64')
    coverage=np.zeros((n,2),dtype='int64')
    for k in range(n):
        m=good[k]&inside
        annual[k]=np.bincount(stack[k][m],minlength=256)
        coverage[k]=[m.sum(),(m&~np.isin(stack[k],[83,111])).sum()]
        if k:
            common=m&good[k-1]
            code=stack[k-1][common].astype('int32')*256+stack[k][common]
            pairs[k-1]=np.bincount(code,minlength=65536).reshape(256,256)
    complete=good.all(axis=0)&inside
    land=complete&(~np.isin(stack,[83,111])).all(axis=0)
    soy=(stack==5)
    freq=np.bincount(soy[:,complete].sum(axis=0),minlength=n+1)
    landfreq=np.bincount(soy[:,land].sum(axis=0),minlength=n+1)
    entries=np.zeros(n,dtype='int64'); first_seen=np.zeros(n,dtype='int64')
    seen=np.zeros(inside.shape,dtype=bool)
    for k in range(n):
        first_seen[k]=(soy[k]&~seen&complete).sum()
        if k: entries[k]=(soy[k]&~soy[k-1]&complete).sum()
        seen|=soy[k]
    endpoints=np.bincount(stack[0][complete].astype('int32')*256+stack[-1][complete],minlength=65536).reshape(256,256)
    cohort=complete&soy[YEARS.index(peak)]
    backward=np.stack([np.bincount(a[cohort],minlength=256) for a in stack])
    maps=np.full((3,*inside.shape),255,dtype='uint8')
    maps[0,complete]=soy[:,complete].sum(axis=0)
    maps[1,complete]=(soy[1:,complete]&~soy[:-1,complete]).sum(axis=0)
    f0=np.isin(stack[0],[141,142,143]); f1=np.isin(stack[-1],[141,142,143])
    maps[2,complete]=np.where(f0[complete]&~f1[complete],1,np.where(~f0[complete]&f1[complete],2,0))
    return dict(annual=annual,pairs=pairs,coverage=coverage,freq=freq,landfreq=landfreq,entries=entries,first_seen=first_seen,endpoints=endpoints,backward=backward,maps=maps,complete=np.array(complete.sum()),fixed_land=np.array(land.sum()),inside=np.array(inside.sum()))

def write_hub(hub,folder,peak,results):
    tables={}
    for k in ['annual','pairs','coverage','freq','landfreq','entries','first_seen','endpoints','backward','complete','fixed_land','inside']:
        tables[k]=sum((r[k] for r in results))
    rows=[]
    for k,year in enumerate(YEARS):
        for code in np.flatnonzero(tables['annual'][k]):
            rows.append(dict(hub_id=hub,year=year,cdl_code=int(code),pixels=int(tables['annual'][k,code])))
    pd.DataFrame(rows).to_csv(folder/'annual_classes.csv',index=False)
    rows=[]
    for k in range(len(YEARS)-1):
        for a,b in zip(*np.nonzero(tables['pairs'][k])):
            rows.append(dict(hub_id=hub,from_year=YEARS[k],to_year=YEARS[k+1],from_code=int(a),to_code=int(b),pixels=int(tables['pairs'][k,a,b]),acres=tables['pairs'][k,a,b]*ACRES))
    pd.DataFrame(rows).to_csv(folder/'annual_transitions.csv',index=False)
    rows=[]
    for a,b in zip(*np.nonzero(tables['endpoints'])):
        rows.append(dict(hub_id=hub,from_year=YEARS[0],to_year=YEARS[-1],from_code=int(a),to_code=int(b),pixels=int(tables['endpoints'][a,b])))
    pd.DataFrame(rows).to_csv(folder/'endpoint_transitions.csv',index=False)
    pd.DataFrame([dict(hub_id=hub,soy_years=k,pixels=int(tables['freq'][k]),fixed_nonwater_pixels=int(tables['landfreq'][k])) for k in range(len(YEARS)+1)]).to_csv(folder/'soy_persistence.csv',index=False)
    rows=[]
    for k,year in enumerate(YEARS):
        for code in np.flatnonzero(tables['backward'][k]):
            rows.append(dict(hub_id=hub,peak_year=peak,year=year,cdl_code=int(code),pixels=int(tables['backward'][k,code])))
    pd.DataFrame(rows).to_csv(folder/'peak_soy_history.csv',index=False)
    pd.DataFrame([dict(hub_id=hub,year=y,valid_pixels=int(tables['coverage'][k,0]),nonwater_pixels=int(tables['coverage'][k,1]),all_years_valid=int(tables['complete']),fixed_nonwater=int(tables['fixed_land']),polygon_pixels=int(tables['inside']),soy_entries=int(tables['entries'][k]),first_observed_soy=int(tables['first_seen'][k])) for k,y in enumerate(YEARS)]).to_csv(folder/'coverage.csv',index=False)
    assert tables['freq'].sum()==tables['complete']==tables['endpoints'].sum()
    assert tables['landfreq'].sum()==tables['fixed_land']
    assert (tables['backward'].sum(axis=1)==tables['backward'].sum(axis=1)[0]).all()
    (folder/'complete.json').write_text(json.dumps(dict(hub_id=hub,peak_year=peak,years=YEARS,tiles=len(results))))

def run(hub,max_tiles=None):
    rings=gpd.read_file(ROOT/'output/facility_rings_exclusive.gpkg').to_crs(5070)
    q=rings[(rings.hub_id==hub)&(rings.ring_index==1)]
    if q.empty: raise ValueError('No polygon; do not manufacture a zero history')
    assert len(q)==1
    g=q.geometry.iloc[0]
    panel=pd.read_csv(ROOT/'data/clean/crop_outcomes_nonwater_exclusive.csv')
    q=panel[(panel.hub_id==hub)&(panel.ring_index==1)&panel.year.isin(YEARS)]
    assert q.year.nunique()==len(YEARS)
    peak=int(q.sort_values(['soy_share_nonwater','year'],ascending=[False,True]).iloc[0].year)
    fingerprint=hashlib.sha256(g.wkb+json.dumps([YEARS,peak,30,30000,'v1']).encode()).hexdigest()
    folder=OUT/f'hub_{hub:03d}'; folder.mkdir(parents=True,exist_ok=True)
    manifest=folder/'manifest.json'
    if manifest.exists(): assert json.loads(manifest.read_text())['fingerprint']==fingerprint
    else: manifest.write_text(json.dumps(dict(fingerprint=fingerprint,hub_id=hub,peak_year=peak)))
    xmin,ymin,xmax,ymax=g.bounds
    xmin=np.floor(xmin/30)*30; ymin=np.floor(ymin/30)*30
    xmax=np.ceil(xmax/30)*30; ymax=np.ceil(ymax/30)*30
    results=[]; index=0
    for x in np.arange(xmin,xmax,30000):
        for y in np.arange(ymin,ymax,30000):
            tile=box(x,y,min(x+30000,xmax),min(y+30000,ymax)); piece=g.intersection(tile)
            if piece.is_empty: continue
            index+=1
            if max_tiles and index>max_tiles: continue
            checkpoint=folder/f'tile_{index:03d}.npz'
            if checkpoint.exists():
                with np.load(checkpoint) as f:results.append({k:f[k] for k in f.files})
                print(f'hub {hub}: reuse tile {index}',flush=True); continue
            arrays=[]; valids=[]; transform=None; shape=None
            for year in YEARS:
                path=folder/f'download_{index}_{year}.tif'
                extract.get_raster(tile,year,path)
                with rasterio.open(path) as src:
                    assert src.crs.to_epsg()==5070
                    if transform is not None: assert src.transform==transform and src.shape==shape,'Grid mismatch'
                    transform=src.transform; shape=src.shape
                    assert abs(transform.a-30)<1e-9 and abs(transform.e+30)<1e-9
                    data=src.read(1)
                    assert data.max()<256
                    arrays.append(data.astype('uint8')); valids.append(valid(data,src.read_masks(1)>0))
                path.unlink()
                print(f'hub {hub} tile {index} year {year}',flush=True)
            inside=geometry_mask([mapping(piece)],shape,transform,invert=True)
            r=analyse(np.stack(arrays),np.stack(valids),inside,peak)
            with rasterio.open(folder/f'history_tile_{index:03d}.tif','w',driver='GTiff',height=shape[0],width=shape[1],count=3,dtype='uint8',crs='EPSG:5070',transform=transform,nodata=255,compress='deflate',tiled=True) as dst:
                dst.write(r.pop('maps'))
                for b,label in enumerate(['soy_years_2013_2025','soy_entries_2014_2025','forest_endpoint_0stable_1loss_2gain'],1): dst.set_band_description(b,label)
            temp=checkpoint.with_suffix('.tmp.npz');np.savez_compressed(temp,**r);temp.replace(checkpoint);results.append(r)
    if max_tiles:
        assert len(results)==min(index,max_tiles);print('Smoke tile completed; not a full hub',flush=True)
    else:write_hub(hub,folder,peak,results)

def merge():
    folders=sorted(OUT.glob('hub_*'))
    expected=pd.read_csv(ROOT/'data/clean/crop_outcomes_nonwater_exclusive.csv')
    expected=set(expected.loc[(expected.ring_index==1)&(expected.nonwater_valid_pixels>0),'hub_id'].astype(int))
    complete={json.loads((p/'complete.json').read_text())['hub_id'] for p in folders if (p/'complete.json').exists()}
    assert complete==expected,f'Incomplete hubs: {expected-complete}'
    target=ROOT/'output/pixel_history_inner';target.mkdir(parents=True,exist_ok=True)
    for name in ['annual_classes','annual_transitions','endpoint_transitions','soy_persistence','peak_soy_history','coverage']:
        x=pd.concat([pd.read_csv(p/(name+'.csv')) for p in folders if (p/'complete.json').exists()],ignore_index=True)
        x.to_csv(target/(name+'.csv'),index=False)
    x=pd.read_csv(target/'annual_transitions.csv');f=[141,142,143]
    x['from_forest']=x.from_code.isin(f);x['to_forest']=x.to_code.isin(f)
    flows=x[x.from_forest!=x.to_forest].copy()
    flows['direction']=np.where(flows.to_forest,'gain','loss')
    flows['other_code']=np.where(flows.to_forest,flows.from_code,flows.to_code)
    flows.groupby(['hub_id','from_year','to_year','direction','other_code'],as_index=False)[['pixels','acres']].sum().to_csv(target/'forest_gain_loss_sources.csv',index=False)
    soy=x[(x.from_code==5)^(x.to_code==5)].copy()
    soy['direction']=np.where(soy.to_code==5,'gain','loss');soy['other_code']=np.where(soy.to_code==5,soy.from_code,soy.to_code)
    soy.groupby(['hub_id','from_year','to_year','direction','other_code'],as_index=False)[['pixels','acres']].sum().to_csv(target/'soy_gain_loss_sources.csv',index=False)
    p=pd.read_csv(target/'soy_persistence.csv')
    totals=p.groupby('soy_years')[['pixels','fixed_nonwater_pixels']].sum()
    report=['# Descriptive 0–25-mile pixel histories, 2013–2025','',f'Completed hubs: {len(complete)}. No regressions.','',totals.to_markdown(),'','Annual transitions use pairwise common coverage. Persistence, endpoints and retrospective peak cohorts use pixels observed in all 13 years. Fixed-nonwater persistence additionally excludes pixels labeled water in any year.','Peak years are chosen separately per hub using the existing annual nonwater share panel. This is descriptive selection, not a policy test.','Forest subtypes remain separate in class tables. A changed CDL forest label does not establish physical forest growth or clearing.','GeoTIFF history maps are retained as per-hub workflow artifacts.']
    (target/'README.md').write_text('\n'.join(report))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--hub',type=int);a.add_argument('--max-tiles',type=int);a.add_argument('--merge',action='store_true');args=a.parse_args()
    if args.merge:merge()
    else:run(args.hub,args.max_tiles)
