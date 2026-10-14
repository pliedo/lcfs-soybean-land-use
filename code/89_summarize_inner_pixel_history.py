"""Validate and visualize descriptive CDL histories; never fits regressions.
Usage: python code/89_summarize_inner_pixel_history.py --input output/pixel_history_inner --maps pixel-history-results --out output/pixel_history_inner/report
"""
from pathlib import Path
import argparse,json
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.colors import ListedColormap,BoundaryNorm
import rasterio
from rasterio.merge import merge
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

ACRES=900/4046.8564224
FOREST=[141,142,143]
NAMES={1:'Corn',5:'Soybeans',26:'Double-crop wheat/soy',24:'Winter wheat',23:'Spring wheat',36:'Alfalfa',37:'Other hay',61:'Fallow/idle',83:'Water',111:'Open water',121:'Developed open space',122:'Developed low intensity',123:'Developed medium intensity',124:'Developed high intensity',131:'Barren',141:'Deciduous forest',142:'Evergreen forest',143:'Mixed forest',152:'Shrub/scrub',176:'Grass/pasture',190:'Woody wetlands',195:'Herbaceous wetlands'}
def label(c):return NAMES.get(int(c),f'CDL {int(c)}')
def group(c):
    if c==5:return 'Soybeans'
    if c==1:return 'Corn'
    if c in [26,239,240,241,254]:return 'Double-crop soy'
    if c in [141,142,143]:return 'Forest'
    if c in [190,195]:return 'Wetlands'
    if c in [36,37,176]:return 'Grass/pasture/hay'
    if c==61:return 'Fallow/idle'
    if c in [83,111]:return 'Water'
    if (1<=c<=61 or 66<=c<=77 or 204<=c<=254):return 'Other crops'
    return 'Other cover'

def main():
    a=argparse.ArgumentParser();a.add_argument('--input',default='output/pixel_history_inner');a.add_argument('--maps',default='pixel-history-results');a.add_argument('--out',default='output/pixel_history_inner/report');args=a.parse_args()
    p=Path(args.input);out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    c=pd.read_csv(p/'coverage.csv');an=pd.read_csv(p/'annual_classes.csv');tr=pd.read_csv(p/'annual_transitions.csv');ep=pd.read_csv(p/'endpoint_transitions.csv');fr=pd.read_csv(p/'forest_gain_loss_sources.csv');sy=pd.read_csv(p/'soy_gain_loss_sources.csv');freq=pd.read_csv(p/'soy_persistence.csv');pk=pd.read_csv(p/'peak_soy_history.csv')
    ids=sorted(c.hub_id.unique());assert len(ids)==57 and c.groupby('hub_id').year.nunique().eq(13).all()
    total=an.groupby(['hub_id','year']).pixels.sum();assert (total==c.set_index(['hub_id','year']).valid_pixels).all()
    complete=c.groupby('hub_id').all_years_valid.first();fixed=c.groupby('hub_id').fixed_nonwater.first()
    assert (freq.groupby('hub_id').pixels.sum()==complete).all()
    assert (freq.groupby('hub_id').fixed_nonwater_pixels.sum()==fixed).all()
    assert (ep.groupby('hub_id').pixels.sum()==complete).all()
    assert pk.groupby(['hub_id','year']).pixels.sum().groupby('hub_id').nunique().eq(1).all()
    paired=tr.groupby(['hub_id','to_year']).pixels.sum()
    assert len(paired)==57*12
    for (hub,y),v in paired.items():assert v<=min(c[(c.hub_id==hub)&c.year.isin([y-1,y])].valid_pixels)
    # Full-resolution map audit of every tile, with a separate display mosaic.
    map_stats=[];mosaics={}
    for hub in ids:
        files=sorted((Path(args.maps)/f'hub_{hub:03d}').glob('history_*.tif'));assert files,f'Missing maps hub {hub}'
        hist=np.zeros(14,dtype='int64');forest=np.zeros(3,dtype='int64');entries=0
        sources=[]
        for file in files:
            src=rasterio.open(file);assert src.crs.to_epsg()==5070 and src.count==3 and src.res==(30.,30.)
            x=src.read();mask=x[0]!=255
            hist+=np.bincount(x[0][mask],minlength=14);forest+=np.bincount(x[2][mask],minlength=3);entries+=int(x[1][mask].sum())
            sources.append(src)
        expected=freq[freq.hub_id==hub].set_index('soy_years').pixels.reindex(range(14)).to_numpy();assert np.array_equal(hist,expected)
        e=ep[ep.hub_id==hub]
        assert forest[2]==e[e.to_code.isin(FOREST)&~e.from_code.isin(FOREST)].pixels.sum()
        assert forest[1]==e[e.from_code.isin(FOREST)&~e.to_code.isin(FOREST)].pixels.sum()
        assert entries==c[c.hub_id==hub].soy_entries.sum()
        image,tf=merge(sources,res=120,nodata=255);mosaics[hub]=image
        for src in sources:src.close()
        map_stats.append(dict(hub_id=hub,tiles=len(files),complete_pixels=int(hist.sum()),always_soy=int(hist[13]),ever_soy=int(hist[1:].sum()),forest_endpoint_gain=int(forest[2]),forest_endpoint_loss=int(forest[1]),soy_entries=entries))
    pd.DataFrame(map_stats).to_csv(out/'map_validation.csv',index=False)
    f=freq.groupby('soy_years')[['pixels','fixed_nonwater_pixels']].sum()
    ever=int(f.loc[1:,'pixels'].sum());always=int(f.loc[13,'pixels']);rotation=int(f.loc[[6,7],'pixels'].sum())
    cs=c.groupby('year')[['valid_pixels','nonwater_pixels','all_years_valid','fixed_nonwater','polygon_pixels']].sum()
    cs.to_csv(out/'coverage_summary.csv')
    forest=fr.groupby(['to_year','direction']).pixels.sum().unstack(fill_value=0);forest['net']=forest.gain-forest.loss;forest.to_csv(out/'forest_annual_flows.csv')
    f2019=fr[(fr.to_year==2019)&fr.direction.eq('gain')].groupby('other_code').pixels.sum().sort_values(ascending=False)
    f2019.rename_axis('cdl_code').to_csv(out/'forest_2019_gain_sources.csv')
    net_hub=fr.assign(signed=np.where(fr.direction.eq('gain'),fr.pixels,-fr.pixels)).groupby(['to_year','hub_id']).signed.sum().reset_index()
    net_hub.to_csv(out/'forest_annual_net_by_hub.csv',index=False)
    soy=sy.groupby(['to_year','direction']).pixels.sum().unstack(fill_value=0);soy['net']=soy.gain-soy.loss;soy.to_csv(out/'soy_annual_flows.csv')
    origins=ep[(ep.to_code==5)&(ep.from_code!=5)].copy();origins['category']=origins.from_code.map(group);origin=origins.groupby('category').pixels.sum().sort_values(ascending=False)
    origin.to_csv(out/'soy_2025_not_2013_sources.csv')
    # Peak cohort predecessor classes, with only hubs having a prior year.
    previous=pk[pk.year==pk.peak_year-1].copy();previous['category']=previous.cdl_code.map(group);prev=previous.groupby('category').pixels.sum().sort_values(ascending=False)
    prev.to_csv(out/'peak_soy_previous_year_sources.csv')
    missing_peak=len(set(ids)-set(previous.hub_id));corn_share=100*origin.get('Corn',0)/origin.sum()
    plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white'})
    figures=[]
    def save(fig,name):
        fig.tight_layout();fig.savefig(out/(name+'.png'),dpi=160,bbox_inches='tight');plt.close(fig);figures.append((name,out/(name+'.png')))
    fig,ax=plt.subplots(figsize=(9,4));ax.bar(f.index,f.pixels*ACRES/1e6,color='#176C93');ax.set(xlabel='Years classified as pure soybeans, out of 13',ylabel='Million acres',title='Soybean persistence on complete 2013–2025 coverage');ax.set_xticks(range(14));save(fig,'soy_persistence')
    fig,ax=plt.subplots(figsize=(9,4));ax.plot(soy.index,soy.gain*ACRES/1e6,label='Nonsoy to soy',color='#176C93');ax.plot(soy.index,soy.loss*ACRES/1e6,label='Soy to nonsoy',color='#D47A18');ax.plot(soy.index,soy.net*ACRES/1e6,label='Net soy change',color='#163749');ax.axhline(0,color='gray',lw=.6);ax.set(ylabel='Million acres',xlabel='Destination year',title='Large annual turnover, much smaller net changes');ax.legend();save(fig,'soy_annual_turnover')
    fig,ax=plt.subplots(figsize=(9,4));ax.bar(forest.index-.2,forest.gain*ACRES/1e6,.4,label='Forest gains',color='#176C93');ax.bar(forest.index+.2,-forest.loss*ACRES/1e6,.4,label='Forest losses',color='#D47A18');ax.plot(forest.index,forest.net*ACRES/1e6,color='#163749',marker='o',label='Net');ax.axhline(0,color='gray',lw=.6);ax.set(ylabel='Million acres',xlabel='Destination year',title='Forest label changes vary sharply by year');ax.legend();save(fig,'forest_annual_turnover')
    fig,ax=plt.subplots(figsize=(9,4));top=f2019.head(7).sort_values();ax.barh([label(k) for k in top.index],100*top/f2019.sum(),color='#176C93');ax.set(xlabel='Percent of gross new forest labels in 2019',title='2019 forest gains mainly came from shrub and grass labels');save(fig,'forest_2019_sources')
    ff=an[an.cdl_code.isin(FOREST)].groupby(['year','cdl_code']).pixels.sum().unstack(fill_value=0)
    fig,ax=plt.subplots(figsize=(9,4))
    for code in FOREST:ax.plot(ff.index,100*ff[code]/cs.valid_pixels,label=label(code))
    ax.set(ylabel='Percent of annual valid pixels, including water',xlabel='Year',title='Forest subtype labels change around source-update years');ax.legend();save(fig,'forest_subtypes')
    fig,axs=plt.subplots(1,2,figsize=(11,4.5))
    for ax,vals,title in [(axs[0],origin,'Soy in 2025, nonsoy in 2013'),(axs[1],prev,'Peak-year soy: previous-year labels')]:
        vals=vals.sort_values();ax.barh(vals.index,100*vals/vals.sum(),color='#176C93');ax.set(xlabel='Percent of cohort',title=title)
    save(fig,'soy_cohort_origins')
    # Compact maps retain full-resolution georeferenced source artifacts.
    with PdfPages(out/'Inner_Ring_Pixel_History_Atlas.pdf') as pdf:
        for start in range(0,len(ids),3):
            fig,axs=plt.subplots(3,2,figsize=(10,11))
            for k,hub in enumerate(ids[start:start+3]):
                image=mosaics[hub]
                axs[k,0].imshow(np.ma.masked_equal(image[0],255),vmin=0,vmax=13,cmap='YlGn');axs[k,0].set_title(f'Hub {hub}: soybean years (0–13)')
                cmap=ListedColormap(['#eeeeee','#D47A18','#176C93'])
                axs[k,1].imshow(np.ma.masked_equal(image[2],255),cmap=cmap,norm=BoundaryNorm([-.5,.5,1.5,2.5],3));axs[k,1].set_title(f'Hub {hub}: forest endpoints')
                for ax in axs[k]:ax.axis('off')
            for k in range(len(ids[start:start+3]),3):
                for ax in axs[k]:ax.axis('off')
            fig.suptitle('2013–2025, exclusive 0–25 miles\nForest: orange loss, blue gain, gray unchanged. Blank: incomplete coverage.\nDisplay at 120 m; source maps and counts use 30 m.',fontsize=11)
            fig.tight_layout(rect=[0,0,1,.93]);pdf.savefig(fig);plt.close(fig)
    fig,axs=plt.subplots(2,3,figsize=(11,7))
    for k,hub in enumerate([1,51,59]):
        img=mosaics[hub];axs[0,k].imshow(np.ma.masked_equal(img[0],255),vmin=0,vmax=13,cmap='YlGn');axs[0,k].set_title(f'Hub {hub}: soybean years')
        axs[1,k].imshow(np.ma.masked_equal(img[2],255),cmap=ListedColormap(['#eeeeee','#D47A18','#176C93']),norm=BoundaryNorm([-.5,.5,1.5,2.5],3));axs[1,k].set_title('Forest: orange loss / blue gain')
        for ax in axs[:,k]:ax.axis('off')
    save(fig,'example_history_maps')
    report=f'''# Inner-ring pixel history audit

Completed October 14, 2026. Descriptive spatial analysis, exclusive 0–25 miles, 2013–2025. No econometric estimates. Workflow 38515721688 completed successfully.

## Coverage and validation

All 57 nonempty catchments have 13 years and 12 adjacent-year transition tables. The 58th candidate has no nonempty exclusive inner catchment. Annual class totals equal coverage counts. Endpoint transitions and persistence sum to complete-series coverage. Peak-cohort sizes are constant across observed years. All 496 georeferenced tiles passed CRS, 30 m resolution, band, persistence, soybean-entry and endpoint-forest count checks.

Complete-series support: {int(complete.sum()):,} pixels ({complete.sum()*ACRES:,.0f} acres). Fixed nonwater support: {int(fixed.sum()):,} pixels ({fixed.sum()*ACRES:,.0f} acres). Annual valid coverage increases in 2025; complete-series histories exclude newly observed pixels. Pairwise annual changes and complete-period histories therefore have different supports. Water is retained as a transition category, not silently treated as new land.

## Persistent soybeans versus rotation

{ever:,} pixels were pure soybeans at least once on complete-series support. Only {always:,} were soybeans in every year ({100*always/ever:.2f}% of ever-soy pixels, {always*ACRES:,.0f} acres). {100*rotation/ever:.2f}% of ever-soy pixels were soybeans in six or seven of the 13 years. This is compatible with rotations; an always-soy criterion is not a sensible measure of a permanent soybean-growing region. Rotation cannot be conclusively diagnosed from frequency alone.

Pixels soybean in 2025 but nonsoy in 2013 came principally from corn ({corn_share:.2f}% of that endpoint cohort). This is an endpoint classification comparison, not proof of permanent expansion or first-ever soybean cultivation. The retrospective figure also shows the prior-year labels of peak-year soybean cohorts, using each hub's own peak year. {missing_peak} hubs peak in 2013 and have no preceding year in this dataset. Pure soy is class 5; double-cropped soybean categories are retained separately.

## Forest: where did new labels come from?

In 2019 there were {int(forest.loc[2019,'gain']):,} gross forest-gain pixels and {int(forest.loc[2019,'loss']):,} forest-loss pixels on pairwise common support. Net gain: {int(forest.loc[2019,'net']):,} pixels ({forest.loc[2019,'net']*ACRES:,.0f} acres). The largest origins are shrub/scrub ({100*f2019.get(152,0)/f2019.sum():.2f}%), grass/pasture ({100*f2019.get(176,0)/f2019.sum():.2f}%), woody wetlands ({100*f2019.get(190,0)/f2019.sum():.2f}%) and developed open space ({100*f2019.get(121,0)/f2019.sum():.2f}%). Soybeans account for only {100*f2019.get(5,0)/f2019.sum():.2f}% of gross forest gains.

Forest labels show net losses in 2021 and 2025, not uninterrupted forest growth. The annual subtype figure shows a pronounced shift toward evergreen/mixed forest in 2019. Earlier USDA metadata checks documented updated NLCD ancillary inputs, making classifier/source changes a plausible explanation for part of these jumps. These tables do not quantify how much is physical land change. Independent imagery or a consistent NLCD time series is necessary before claiming afforestation, deforestation or clearing.

Top 2019 net forest-gain hubs and largest 2025 loss hubs are retained in forest_annual_net_by_hub.csv. The atlas maps every catchment. Display images use 120 m nearest-neighbor mosaics for readability; all validation and tables use the original 30 m maps. Endpoint maps show 2013 versus 2025, not cumulative clearing across all years.

## Other pathways and the external comparison

Other LCFS pathways could affect soybean through substitution among oils, competing acreage, and wider commodity prices. The sign can be positive or negative. It is a future sensitivity check, not a demonstrated explanation for our smaller estimate. Avoid counting the same refinery capacity multiple times across feedstock approvals. Capacity is potential demand; actual soybean-based fuel volume is a different treatment. Constant utilization/feedstock proportions alone do not mechanically change a percentage elasticity. Miao, Li and Khanna also differ in period, geography, outcomes and identification. Common national price effects can be absorbed by our year fixed effects.

## Sources and reproducibility

- Raw counts: output/pixel_history_inner, generated by code/88_audit_inner_ring_pixel_history.py.
- Workflow: https://github.com/pliedo/lcfs-soybean-land-use/actions/runs/38515721688
- Forest-input evidence: doc/forest-classification-evidence.md; USDA Iowa metadata 2018–2021.
- Reproduce this report and figures with code/89_summarize_inner_pixel_history.py and the per-hub workflow map artifacts.
- Fuel comparison: https://onlinelibrary.wiley.com/doi/10.1002/aepp.70005

The regression composition figure and this spatial transition audit answer different questions. Neither labels individual transitions as policy-caused.
'''
    (out/'REPORT.md').write_text(report)
    styles=getSampleStyleSheet();styles['Normal'].fontSize=10;styles['Normal'].leading=14
    doc=SimpleDocTemplate(str(out/'Inner_Ring_Pixel_History_Report.pdf'),pagesize=(612,792),rightMargin=42,leftMargin=42,topMargin=42,bottomMargin=42)
    story=[]
    for paragraph in report.split('\n\n'):
        if paragraph.startswith('# '):style=styles['Title'];paragraph=paragraph[2:]
        elif paragraph.startswith('## '):style=styles['Heading2'];paragraph=paragraph[3:]
        else:style=styles['Normal']
        story.append(Paragraph(paragraph.replace('&','&amp;').replace('–','-').replace('\n','<br/>'),style));story.append(Spacer(1,7))
    for name,path in figures:
        story.append(PageBreak());story.append(Paragraph(name.replace('_',' ').title(),styles['Heading1']))
        from PIL import Image as PILImage
        im=PILImage.open(path);w,h=im.size;story.append(Image(str(path),width=528,height=528*h/w))
        story.append(Spacer(1,12));story.append(Paragraph('Descriptive CDL labels. No causal attribution. Supports and definitions are described in the report.',styles['Normal']))
    doc.build(story)
    print(json.dumps(dict(hubs=len(ids),tiles=sum(r['tiles'] for r in map_stats),complete_pixels=int(complete.sum()),always_soy=always,ever_soy=ever,always_share_ever=100*always/ever,corn_endpoint_origin_percent=corn_share,report=str(out/'Inner_Ring_Pixel_History_Report.pdf'))))

if __name__=='__main__':main()
