"""Paired, aligned 2018/2019 CDL pixels in exclusive ring polygons.

Failures raise: a failed request is never interpreted as no coverage.
Raw rasters are temporary. Default smoke audit: hub 1, innermost band.
"""
import argparse
import importlib.util
from pathlib import Path
import tempfile
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.features import geometry_mask
from shapely.geometry import box, mapping

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('extract',ROOT/'code/07_extract_cdl_raster_band.py')
extract=importlib.util.module_from_spec(spec); spec.loader.exec_module(extract)

def category(v):
    result=np.full(v.shape,10,dtype=np.uint8)
    result[v==5]=0; result[v==1]=1; result[v==61]=2
    crop=np.isin(v,[n for n in range(1,256) if extract.cropland(n)])
    result[crop & ~np.isin(v,[1,5,61])]=3
    result[v==141]=4; result[v==142]=5; result[v==143]=6
    result[np.isin(v,[190,195])]=7
    result[v==152]=8; result[v==176]=9
    return result

def main():
    a=argparse.ArgumentParser(); a.add_argument('--hub',type=int,required=True)
    a.add_argument('--ring',type=int,default=1); args=a.parse_args()
    rings=gpd.read_file(ROOT/'output/facility_rings_exclusive.gpkg').to_crs(5070)
    s=rings[(rings.hub_id==args.hub)&(rings.ring_index==args.ring)]
    labels=['soy','corn','fallow_idle','other_cropland','deciduous_forest','evergreen_forest','mixed_forest','wetlands','shrub_scrub','grassland_pasture','other_non_crop']
    counts=np.zeros((11,11),dtype=np.int64); coverage=np.zeros(3,dtype=np.int64)
    if len(s):
        assert len(s)==1
        g=s.geometry.iloc[0]; xmin,ymin,xmax,ymax=g.bounds
        # Global 30m alignment and equal windows in both years.
        xmin=np.floor(xmin/30)*30; ymin=np.floor(ymin/30)*30
        xmax=np.ceil(xmax/30)*30; ymax=np.ceil(ymax/30)*30
        with tempfile.TemporaryDirectory() as folder:
            for x in np.arange(xmin,xmax,30000):
                for y in np.arange(ymin,ymax,30000):
                    tile=box(x,y,min(x+30000,xmax),min(y+30000,ymax))
                    piece=g.intersection(tile)
                    if piece.is_empty: continue
                    arrays=[]; valids=[]; transform=None
                    for year in [2018,2019]:
                        path=Path(folder)/f'{year}.tif'
                        extract.get_raster(tile,year,path)
                        with rasterio.open(path) as src:
                            assert src.crs.to_epsg()==5070
                            if transform is not None: assert src.transform==transform, 'Grid mismatch'
                            transform=src.transform
                            data=src.read(1); valid=src.read_masks(1)>0
                            inside=geometry_mask([mapping(piece)],data.shape,src.transform,invert=True)
                            arrays.append(data); valids.append(valid & inside & (data>0))
                    assert arrays[0].shape==arrays[1].shape
                    common=valids[0]&valids[1]
                    coverage+=np.array([valids[0].sum(),valids[1].sum(),common.sum()])
                    pair=category(arrays[0][common])*11+category(arrays[1][common])
                    counts+=np.bincount(pair,minlength=121).reshape(11,11)
                    print(f'hub {args.hub}: aligned tile completed',flush=True)
    out=ROOT/'transition-results'/f'hub_{args.hub:03d}'/f'ring_{args.ring}'
    out.mkdir(parents=True,exist_ok=True)
    pd.DataFrame([dict(hub_id=args.hub,ring_index=args.ring,from_2018=labels[i],to_2019=labels[j],pixels=int(counts[i,j])) for i in range(11) for j in range(11)]).to_csv(out/'transitions.csv',index=False)
    pd.DataFrame([dict(hub_id=args.hub,ring_index=args.ring,valid_2018=int(coverage[0]),valid_2019=int(coverage[1]),common_valid=int(coverage[2]))]).to_csv(out/'coverage.csv',index=False)

if __name__=='__main__': main()
