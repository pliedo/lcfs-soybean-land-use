"""Add facility geography to the completed descriptive report; no raster rerun."""
from pathlib import Path
import argparse,subprocess
import pandas as pd,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from PIL import Image as PILImage

def main():
    a=argparse.ArgumentParser();a.add_argument('--out',default='output/pixel_history_inner/report');a.add_argument('--inventory',default='data/raw/soy_crushing_facilities.xlsx');args=a.parse_args();out=Path(args.out)
    h=pd.read_excel(args.inventory).rename(columns={'number':'hub_id','Company':'company','Adress':'address','lon':'latitude','lat':'longitude'})[['hub_id','company','address','latitude','longitude']]
    net=pd.read_csv(out/'forest_annual_net_by_hub.csv').merge(h,on='hub_id',validate='many_to_one');net.to_csv(out/'forest_net_change_locations.csv',index=False)
    top=net[net.to_year.eq(2019)].nlargest(5,'signed');top['net_gain_acres']=top.signed*900/4046.8564224;top[['hub_id','company','address','net_gain_acres']].to_csv(out/'forest_2019_top_locations.csv',index=False)
    fig,axs=plt.subplots(1,2,figsize=(11,5),sharex=True,sharey=True);scale=max(abs(net[net.to_year.isin([2019,2025])].signed))*900/4046.8564224/1000
    for ax,year in zip(axs,[2019,2025]):
        x=net[net.to_year.eq(year)].copy();v=x.signed*900/4046.8564224/1000
        im=ax.scatter(x.longitude,x.latitude,c=v,cmap='RdBu',vmin=-scale,vmax=scale,s=35,edgecolors='white',linewidths=.4)
        for _,r in x.reindex(x.signed.abs().nlargest(3).index).iterrows():ax.annotate(str(int(r.hub_id)),(r.longitude,r.latitude),xytext=(4,4),textcoords='offset points',fontsize=8)
        ax.set(title=f'Net forest-label change, {year}',xlabel='Longitude',xlim=(-101,-75),ylim=(28,48));ax.grid(alpha=.15)
    axs[0].set_ylabel('Latitude');fig.subplots_adjust(right=.88,wspace=.15);bar=fig.colorbar(im,cax=fig.add_axes([.91,.2,.015,.6]));bar.set_label('Thousand acres (gain positive)')
    fig.savefig(out/'forest_change_geography.png',dpi=160,bbox_inches='tight');plt.close(fig)
    report=(out/'REPORT.md').read_text();insert='\n\n## Locations of the largest forest-label changes\n\nThe largest 2019 net gains occur around the inventory sites in Cofield, NC (hub 59), Fayetteville, NC (58), Valdosta, GA (57), Gainesville, GA (48), and Guntersville, AL (35). The five together account for '+f'{100*top.signed.sum()/net[net.to_year.eq(2019)].signed.sum():.2f}'+'% of pooled net gains. This concentration in southeastern catchments complements the subtype/source-update evidence, but it does not establish the share of changes caused by classification. Facility names and addresses come from the legacy inventory and do not resolve all site-role questions. The geographic figure labels the three largest absolute changes in each year by hub ID.\n\n'
    report=report.replace('## Other pathways and the external comparison',insert+'## Other pathways and the external comparison')
    (out/'REPORT.md').write_text(report)
    styles=getSampleStyleSheet();styles['Normal'].fontSize=10;styles['Normal'].leading=14;story=[]
    for p in report.split('\n\n'):
        if p.startswith('# '):style=styles['Title'];p=p[2:]
        elif p.startswith('## '):style=styles['Heading2'];p=p[3:]
        else:style=styles['Normal']
        story.extend([Paragraph(p.replace('&','&amp;').replace('–','-').replace('\n','<br/>'),style),Spacer(1,7)])
    for name in ['soy_persistence','soy_annual_turnover','forest_annual_turnover','forest_2019_sources','forest_subtypes','soy_cohort_origins','forest_change_geography','example_history_maps']:
        path=out/(name+'.png');im=PILImage.open(path);w,h=im.size;story.extend([PageBreak(),Paragraph(name.replace('_',' ').title(),styles['Heading1']),Image(str(path),width=528,height=528*h/w),Spacer(1,12),Paragraph('Descriptive CDL labels. No causal attribution. All source counts use 30 m pixels.',styles['Normal'])])
    pdf=out/'Inner_Ring_Pixel_History_Report.pdf';SimpleDocTemplate(str(pdf),pagesize=(612,792),rightMargin=42,leftMargin=42,topMargin=42,bottomMargin=42).build(story)
    temp=pdf.with_suffix('.portable.pdf');subprocess.run(['gs','-q','-dBATCH','-dNOPAUSE','-sDEVICE=pdfwrite','-dCompatibilityLevel=1.4','-dASCII85EncodePages=true','-sOutputFile='+str(temp),str(pdf)],check=True);temp.replace(pdf)
    print('Located forest transitions and rebuilt report.')

if __name__=='__main__':main()
