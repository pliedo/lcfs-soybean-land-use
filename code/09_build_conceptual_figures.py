"""Presentation schematics; illustrative functions are not estimated results."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
OUT=Path("output/figures/conceptual"); OUT.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({"font.size":15,"font.family":"DejaVu Sans"})
def save(fig,name):
    fig.savefig(OUT/(name+".png"),dpi=240,bbox_inches="tight")
    fig.savefig(OUT/(name+".pdf"),bbox_inches="tight")
    plt.close(fig)
def box(ax,x,y,w,h,text):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.015",facecolor="#E8F0F7",edgecolor="#285A83",linewidth=1.5))
    ax.text(x+w/2,y+h/2,text,ha="center",va="center",fontsize=16)
def arrow(ax,a,b,label=""):
    ax.annotate("",xy=b,xytext=a,arrowprops=dict(arrowstyle="-|>",color="#285A83",lw=2))
    if label: ax.text((a[0]+b[0])/2,(a[1]+b[1])/2+.035,label,ha="center",fontsize=12)
fig,ax=plt.subplots(figsize=(12.8,7.2));ax.set(xlim=(0,1),ylim=(0,1));ax.axis("off")
box(ax,.32,.76,.36,.14,"California LCFS\nRenewable-diesel incentives")
box(ax,.04,.40,.26,.16,"Renewable-diesel\nrefineries")
box(ax,.37,.40,.26,.16,"Soybean\ncrushers")
box(ax,.70,.40,.26,.16,"Soybean acres\nPlanting decisions")
arrow(ax,(.40,.76),(.17,.56),"Policy incentive")
arrow(ax,(.30,.48),(.37,.48),"Oil demand")
arrow(ax,(.63,.48),(.70,.48),"Soybean demand")
arrow(ax,(.70,.34),(.63,.34),"Soybeans")
arrow(ax,(.37,.34),(.30,.34),"Soybean oil")
ax.text(.5,.14,"Hypothesized demand channel; physical feedstocks flow toward refineries.",ha="center",fontsize=13,color="#4B5563")
save(fig,"industry_policy_channel")
fig,ax=plt.subplots(figsize=(12.8,7.2));ax.axis("off")
ax.text(.5,.90,"Geographic exposure and planting responses",ha="center",fontsize=23,fontweight="bold")
ax.text(.5,.69,r"$D_{it}=\sum_r w_{ir}S_{rt}$",ha="center",fontsize=29)
ax.text(.5,.55,"Refinery policy exposure × predetermined refinery–crusher weights",ha="center",fontsize=15)
ax.text(.5,.35,r"$y_{ibt}=\alpha_{ib}+\lambda_t+\sum_k\beta_k\,D_{it}\,\mathbf{1}\{b=k\}+\varepsilon_{ibt}$",ha="center",fontsize=23)
ax.text(.5,.18,"Outcome: soybean share in exclusive ring b around hub i\nHub × ring fixed effects; year fixed effects; effects may differ by ring",ha="center",fontsize=15)
ax.text(.5,.045,"Planned specification: identification requires credible shock timing and exposure; outer rings are not untreated controls.",ha="center",fontsize=10,color="#4B5563")
save(fig,"empirical_specification")
d=np.linspace(0,1500,301)
functions={"Inverse distance (50 km offset)":1/(d+50),"Inverse square (50 km offset)":1/(d+50)**2,"Exponential (300 km scale)":np.exp(-d/300),"Cutoff (500 km)":(d<=500).astype(float)}
fig,ax=plt.subplots(figsize=(12.8,7.2))
for label,v in functions.items():ax.plot(d,v/v[0],lw=2.5,label=label)
ax.set(xlabel="Refinery–crusher distance (km)",ylabel="Relative weight (weight at zero = 1)")
ax.spines[["top","right"]].set_visible(False);ax.grid(axis="y",alpha=.2);ax.legend(frameon=False)
fig.text(.5,.01,"Illustrative candidate functions and scales; these are not empirical robustness estimates.",ha="center",fontsize=11)
fig.tight_layout(rect=[0,.045,1,1]);save(fig,"candidate_distance_weight_functions")
