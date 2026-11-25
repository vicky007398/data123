import streamlit as st
import pandas as pd
import subprocess
import json
import os
from html import escape
from pathlib import Path
from contextlib import closing
import plotly.express as px
from datetime import date, datetime, time, timedelta

st.set_page_config(page_title="Data123 | MES Intelligence", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""<style>
[data-testid=stHeader]{height:1.8rem;background:transparent}
[data-testid=stToolbar]{display:none}
.block-container{padding-top:.65rem!important;padding-bottom:.5rem!important;padding-left:1.4rem!important;padding-right:1.4rem!important;max-width:100%!important}
[data-testid=stAppViewContainer] .main .block-container{padding-top:.65rem!important}
[data-testid=stMainBlockContainer] > [data-testid=stVerticalBlock]{gap:.4rem}
[data-testid=stMainBlockContainer] > [data-testid=stVerticalBlock] > [data-testid=stElementContainer]:has(style):not(:has(.live-head)){display:none}
[data-testid=stHeader]{height:1.4rem}
[data-testid=stMarkdownContainer] .el-board{row-gap:5px}
[data-testid=stMarkdownContainer] p{margin-bottom:0}
[data-testid=stMarkdownContainer] .live-head,[data-testid=stMarkdownContainer] .shift-strip,[data-testid=stMarkdownContainer] .mini-kpis,[data-testid=stMarkdownContainer] .el-board{position:relative;display:flow-root;box-sizing:border-box}
[data-testid=stMarkdownContainer] .shift-strip,[data-testid=stMarkdownContainer] .el-board{display:grid}
[data-testid=stMarkdownContainer] .mini-kpis,[data-testid=stMarkdownContainer] .live-head{display:flex}
[data-testid=stMarkdownContainer] .live-head{margin-bottom:4px}
[data-testid=stMarkdownContainer] .shift-strip{margin-bottom:3px}
[data-testid=stMarkdownContainer] .el-board{padding-bottom:5px}
[data-testid=stMarkdownContainer] .mini-kpis{padding-bottom:5px}
[data-testid=stPlotlyChart]{margin-top:0}
[data-testid=stMarkdownContainer] .el-kpi,[data-testid=stMarkdownContainer] .mini-kpi{height:auto;line-height:1.35;align-self:stretch}
[data-testid=stMetricValue]{font-size:1.15rem!important}
[data-testid=stMetricLabel] p{font-size:.72rem!important}
[data-testid=stMetricValue] > div{white-space:normal!important;overflow:visible!important;text-overflow:clip!important}
[data-testid=stHeading] h2,[data-testid=stHeading] h3{font-size:1rem!important;padding:0!important}
.live-head{display:flex;flex-wrap:wrap;gap:6px;justify-content:space-between;align-items:center;background:#123052;color:#fff;border-radius:9px;padding:6px 12px;margin-bottom:2px}.shift-strip{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px}.shift-strip div{border-radius:6px;padding:4px 8px;color:white;font-size:11px;text-align:center;overflow-wrap:anywhere}.shift-a{background:#2563eb}.shift-b{background:#0f766e}.shift-c{background:#7c3aed}
.live-head strong{font-size:21px;letter-spacing:-.3px}.live-head span{font-size:11px;opacity:.8}
.mini-kpis{display:flex;gap:6px;flex-wrap:wrap}.mini-kpi{flex:1 1 82px;min-width:0;box-sizing:border-box;border:1px solid #b9cce0;border-left:4px solid #2563eb;background:#eff6ff;color:#16314f;border-radius:8px;padding:4px 8px}.mini-kpi:nth-child(4n+2){border-left-color:#0f766e;background:#ecfdf5}.mini-kpi:nth-child(4n+3){border-left-color:#7c3aed;background:#f5f3ff}.mini-kpi:nth-child(4n+4){border-left-color:#d97706;background:#fffbeb}
.mini-kpi small{font-size:10px;display:block;opacity:.8}.mini-kpi b{font-size:clamp(12px,1.05vw,16px);overflow-wrap:anywhere}

    .el-board{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:5px;margin-bottom:2px}
    .el-kpi{grid-column:span 2;border:1px solid #cbd5e1;border-left:3px solid #2563eb;background:#eff6ff;color:#172b45;border-radius:8px;padding:4px 7px;min-width:0;overflow-wrap:anywhere;box-sizing:border-box}.el-kpi:nth-child(1){background:#fff7ed;border-left-color:#ea580c}.el-kpi:nth-child(2){background:#fef2f2;border-left-color:#dc2626}.el-kpi:nth-child(4){background:#ecfdf5;border-left-color:#0f766e}.el-kpi:nth-child(5){background:#f5f3ff;border-left-color:#7c3aed}
    .el-kpi:nth-child(-n+2){grid-column:span 3}.el-label{font-size:10px;opacity:.8}.el-value{font-size:clamp(13px,1.25vw,17px);font-weight:700;line-height:1.15}
    .el-sub{font-size:10px;opacity:.8;line-height:1.15}.el-title{font-size:13px;font-weight:650;margin:2px 0 4px;padding:3px 7px;border-radius:5px;background:#123052;color:white}.el-sub{overflow-wrap:anywhere}@media(max-width:650px){.el-board{grid-template-columns:repeat(2,minmax(0,1fr))}.el-kpi,.el-kpi:nth-child(-n+2){grid-column:span 1}.shift-strip{grid-template-columns:1fr}}
    
</style>""",unsafe_allow_html=True)
# Data123 V2.6
defaults = {}
try:
    defaults = json.loads(Path(__file__).with_name("connection.local.json").read_text(encoding="utf-8"))
except (OSError, ValueError):
    pass
host=defaults.get("host","")
port=int(defaults.get("port",1433))
db=defaults.get("database","")
user=defaults.get("username","")
password=os.environ.get("DATA123_DB_PASSWORD") or defaults.get("password","")
trust=defaults.get("trust_server_certificate",False) is True
schema=defaults.get("schema","")
table=defaults.get("table","")
if not all((host,db,user,password,schema,table)):
    st.error("Local connection configuration is incomplete. Set connection.local.json and the local password before starting Data123.")
    st.stop()
PS_QUERY = r"""
$ErrorActionPreference = 'Stop'
try {
    $req = [Console]::In.ReadToEnd() | ConvertFrom-Json
    $b = New-Object System.Data.SqlClient.SqlConnectionStringBuilder
    $b['Data Source'] = $req.host + ',' + $req.port
    $b['Initial Catalog'] = $req.database
    $b['User ID'] = $req.user
    $b['Password'] = $req.password
    $b['Encrypt'] = $true
    $b['TrustServerCertificate'] = [bool]$req.trust
    $b['Connect Timeout'] = 8
    $b['Persist Security Info'] = $false
    $c = New-Object System.Data.SqlClient.SqlConnection
    $c.ConnectionString = $b.get_ConnectionString()
    try {
        $c.Open()
        $cmd = $c.CreateCommand()
        $cmd.CommandTimeout = 25
        $cmd.CommandText = $req.query
        for ($i=0; $i -lt $req.params.Count; $i++) {
            $p = $req.params[$i]
            if ($p.kind -eq 'datetime') {
                $param = $cmd.Parameters.Add('@p'+$i,[System.Data.SqlDbType]::DateTime2)
                $param.Value = [datetime]::Parse($p.value,[Globalization.CultureInfo]::InvariantCulture)
            } else {
                $param = $cmd.Parameters.Add('@p'+$i,[System.Data.SqlDbType]::NVarChar,4000)
                $param.Value = [string]$p.value
            }
        }
        $reader = $cmd.ExecuteReader()
        $rows = New-Object 'System.Collections.Generic.List[object]'
        try {
            while ($reader.Read()) {
                $row = New-Object 'object[]' $reader.FieldCount
                for ($j=0; $j -lt $reader.FieldCount; $j++) {
                    if ($reader.IsDBNull($j)) { $row[$j] = $null }
                    else {
                        $v = $reader.GetValue($j)
                        if ($v -is [datetime] -or $v -is [datetimeoffset]) { $row[$j] = $v.ToString('o') }
                        elseif ($v -is [guid]) { $row[$j] = $v.ToString() }
                        else { $row[$j] = $v }
                    }
                }
                $rows.Add($row)
            }
        } finally { $reader.Dispose(); $cmd.Dispose() }
        $out = @{ok=$true;rows=$rows.ToArray()}
    } finally { $c.Dispose() }
} catch {
    $e=$_.Exception
    while ($e.InnerException) { $e=$e.InnerException }
    $msg=$e.Message
    if ($req.password) { $msg=$msg.Replace([string]$req.password,'[redacted]') }
    $out=@{ok=$false;error=$msg}
}
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
[Console]::Write(($out | ConvertTo-Json -Depth 8 -Compress))
"""
class SqlClientCursor:
    def execute(self, query, *params):
        if not query.lstrip().upper().startswith("SELECT "):
            raise ValueError("Only SELECT queries are allowed")
        if len(params)==1 and isinstance(params[0], (list,tuple)):
            params=params[0]
        # Queries originate only from the application, with quoted identifiers.
        if query.count("?") != len(params):
            raise ValueError("SQL parameter count mismatch")
        parts=query.split("?")
        query="".join(part + (f"@p{i}" if i<len(params) else "") for i,part in enumerate(parts))
        payload={"host":host,"port":str(int(port)),"database":db,"user":user,"password":password,"trust":trust,"query":query,"params":[{"kind":"datetime" if isinstance(p,datetime) else "text","value":p.isoformat() if isinstance(p,datetime) else str(p)} for p in params]}
        result=subprocess.run(["powershell.exe","-NoProfile","-NonInteractive","-Command",PS_QUERY],input=json.dumps(payload,ensure_ascii=True),capture_output=True,encoding="utf-8",timeout=65,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        if result.returncode or not result.stdout.strip():
            raise RuntimeError("Windows SqlClient bridge failed; check PowerShell policy with IT")
        output=json.loads(result.stdout)
        if not output.get("ok"):
            raise RuntimeError(output.get("error","SQL Server connection failed"))
        self.rows=output["rows"]
        return self
    def fetchall(self): return self.rows
    def fetchmany(self,n): return self.rows[:n]
    def close(self): pass
class SqlClientConnection:
    def cursor(self): return SqlClientCursor()
    def close(self): pass
def connection(): return SqlClientConnection()
def ident(n): return "["+n.replace("]","]]")+"]"
st.sidebar.caption("Automatic MES connection | SELECT-only")
production_today=(datetime.now()-timedelta(hours=6)).date()
first_day=production_today.replace(day=1)
day=st.sidebar.date_input("Production day",production_today,min_value=first_day,max_value=production_today,key=f"production_day_{first_day:%Y%m}")
start=datetime.combine(day,time(6))
end=start+timedelta(days=1)
auto=st.sidebar.checkbox("Auto refresh (60 seconds)",True)
st.sidebar.caption("Production day: 06:00 to next day 06:00. Database timestamps assumed plant-local.")
@st.fragment(run_every="60s" if auto else None)
def dashboard():
    current_production_day=(datetime.now()-timedelta(hours=6)).date()
    if current_production_day.replace(day=1)!=first_day:
        st.rerun()
    try:
        with closing(connection()) as c:
            cols=c.cursor().execute("SELECT COLUMN_NAME,DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=? AND TABLE_NAME=?",schema,table).fetchall()
            lookup={n.upper():n for n,t in cols}
            types={n.upper():t for n,t in cols}
            stages={"Lamination":"LAM_DATE_IN","Sun simulator":"IV_TIME","FQC":"FQC_TIME","Pre-EL":"PRE_EL_TIME","Mid-EL":"MID_EL_TIME","Final EL":"EL_TIME"}
            levels={"Pre-EL":"PRE_EL_LEVEL","Mid-EL":"MID_EL_LEVEL","Final EL":"EL_LEVEL"}
            if "LOT_NUMBER" not in lookup:
                st.error("LOT_NUMBER not found"); return
            active={k:v for k,v in stages.items() if v in lookup and types[v] in ("datetime","datetime2","smalldatetime","datetimeoffset","date")}
            if not active:
                st.error("No supported timestamp columns found. Text dates need explicit parsing."); return
            wanted=list(dict.fromkeys(["LOT_NUMBER",*active.values(),*levels.values(),"PMAX","VOC","ISC","FF","IPM","VPM","CTM","TEMPERATURE","FQC_LEVEL"]))
            wanted=[x for x in wanted if x in lookup]
            predicates=[f"({ident(lookup[v])} >= ? AND {ident(lookup[v])} < ?)" for v in active.values()]
            q="SELECT TOP (100001) "+",".join(ident(lookup[x]) for x in wanted)+" FROM "+ident(schema)+"."+ident(table)+" WHERE "+" OR ".join(predicates)
            with closing(c.cursor()) as cur:
                cur.execute(q,[p for _ in predicates for p in (start,end)])
                rows=[tuple(row) for row in cur.fetchmany(100001)]
            if len(rows)>100000:
                st.error("Safety limit exceeded; use a narrower query or server-side aggregation."); return
        df=pd.DataFrame(rows,columns=wanted)
    except Exception as e:
        st.error("Query failed: "+type(e).__name__+" | "+str(e.args[0] if e.args else "unknown")); return
    def events(stage):
        col=active.get(stage)
        if not col: return pd.DataFrame()
        d=df.copy()
        d["_time"]=pd.to_datetime(d[col],errors="coerce")
        if getattr(d["_time"].dt,"tz",None) is not None:
            d["_time"]=d["_time"].dt.tz_convert("Asia/Kolkata").dt.tz_localize(None)
        d=d.dropna(subset=["LOT_NUMBER","_time"])
        d=d[d["LOT_NUMBER"].astype(str).str.strip().ne("")]
        d=d[(d["_time"]>=start)&(d["_time"]<end)].sort_values("_time").drop_duplicates("LOT_NUMBER",keep="first")
        d["hour"]=((d["_time"]-start).dt.total_seconds()//3600).astype(int)
        d["shift"]=d["hour"].map(lambda h:"ABC"[h//8])
        return d
    data={s:events(s) for s in stages}
    fqc=data["FQC"]
    st.markdown(f'<div class="live-head"><strong>Live Dashboard</strong><span>{day:%d %b %Y} · MES connected · Updated {datetime.now():%H:%M:%S} · V2.6</span></div>',unsafe_allow_html=True)
    st.markdown('<div class="shift-strip"><div class="shift-a">A SHIFT · 06:00–14:00</div><div class="shift-b">B SHIFT · 14:00–22:00</div><div class="shift-c">C SHIFT · 22:00–06:00 (+1)</div></div>',unsafe_allow_html=True)
    rej={}
    month_start=datetime.combine(first_day,time(6))
    pre_panel, final_panel = st.columns(2)
    panels = {"Pre-EL": pre_panel, "Final EL": final_panel}
    for stage,level in levels.items():
        d=data[stage]
        if level not in d:
            if stage in panels:
                panels[stage].markdown("**"+stage+" rejection**")
                panels[stage].warning("Inspection status or timestamp unavailable")
            continue
        codes=sorted(d[level].dropna().astype(str).str.strip().str.upper().unique().tolist())
        codes=[x for x in codes if x]
        # A single server-side query returns grouped first-event statuses for MTD.
        # Use daily unique module counts, consistent with shift totals.
        mtd={}
        try:
            if stage=="Mid-EL":
                raise LookupError("daily only")
            ts=ident(lookup[active[stage]])
            lv=ident(lookup[level])
            lot=ident(lookup["LOT_NUMBER"])
            source=ident(schema)+"."+ident(table)
            q_mtd=("SELECT status, COUNT_BIG(*) FROM (SELECT UPPER(LTRIM(RTRIM(CONVERT(nvarchar(200),"+lv+")))) AS status, "
                   "ROW_NUMBER() OVER (PARTITION BY "+lot+", CONVERT(date,DATEADD(hour,-6,"+ts+")) ORDER BY "+ts+", CONVERT(nvarchar(200),"+lv+")) AS rn "
                   "FROM "+source+" WHERE "+ts+">=? AND "+ts+"<? AND "+lot+" IS NOT NULL AND LTRIM(RTRIM(CONVERT(nvarchar(200),"+lot+")))<>''"
                   ") AS x WHERE rn=1 AND status IS NOT NULL AND status<>'' GROUP BY status")
            with closing(connection()) as c:
                mtd=dict(c.cursor().execute(q_mtd,month_start,end).fetchall())
        except Exception as e:
            mtd=None
            if stage!="Mid-EL": st.warning(stage+" MTD unavailable: "+str(e).replace(password,"[redacted]"))
        available=sorted(set(codes)|set(mtd or {}))
        configured=defaults.get("rejection_codes",{}).get(stage,[])
        configured=[str(x).strip().upper() for x in configured]
        with st.sidebar.expander(stage+" status mapping"):
            chosen=st.multiselect("Rejection codes",available,default=[x for x in configured if x in available],key=stage+"_codes")
            accepted=st.multiselect("Accepted / other non-rejection codes",available,default=[x for x in available if x=="OK" and x not in chosen],key=stage+"_accepted")
            st.caption("Confirm codes against MES. Unmapped statuses are excluded.")
        chosen=set(chosen)
        accepted=set(accepted)-chosen
        mapped=chosen|accepted
        status=d[level].astype("string").str.strip().str.upper()
        valid=status.isin(mapped)
        mask=status.isin(chosen)
        rej[stage]=(mask,valid,chosen)
        if stage=="Mid-EL":
            continue
        def tile(label,n,total,unknown=0,ready=True):
            value=f"{100*n/total:.2f}%" if ready and total else "—"
            details=f"{n:,} rejected / {total:,} mapped" if ready else "Confirm status mapping"
            if ready and unknown: details+=f" · {unknown:,} unmapped"
            return f'<div class="el-kpi"><div class="el-label">{escape(label)}</div><div class="el-value">{value}</div><div class="el-sub">{escape(details)}</div></div>'
        ready=bool(chosen) and bool(accepted)
        tiles=[]
        if mtd is None:
            tiles.append(tile("MTD",0,0,ready=False))
        else:
            tiles.append(tile("MTD",sum(int(v) for k,v in mtd.items() if k in chosen),sum(int(v) for k,v in mtd.items() if k in mapped),sum(int(v) for k,v in mtd.items() if k not in mapped),ready))
        for shift in [None,"A","B","C"]:
            pick=d["shift"].eq(shift) if shift else pd.Series(True,index=d.index)
            tiles.append(tile("Day total" if shift is None else "Shift "+shift,int((pick&mask).sum()),int((pick&valid).sum()),int((pick&~valid).sum()),ready))
        panels[stage].markdown('<div class="el-title">'+escape(stage)+' rejection</div><div class="el-board">'+''.join(tiles)+'</div>',unsafe_allow_html=True)
    lead_text="N/A"
    if "PRE_EL_TIME" in fqc:
        pre=pd.to_datetime(fqc["PRE_EL_TIME"],errors="coerce")
        if getattr(pre.dt,"tz",None) is not None: pre=pre.dt.tz_convert("Asia/Kolkata").dt.tz_localize(None)
        lead=(fqc["_time"]-pre).dt.total_seconds()/3600
        lead=lead.where(lead>=0)
        if lead.notna().any(): lead_text=f"{lead.mean():.2f} h"
    overview=[("FQC production",f"{len(fqc):,}" if "FQC" in active else "N/A"),("Lamination",f"{len(data['Lamination']):,}" if "Lamination" in active else "N/A"),("Sun simulator",f"{len(data['Sun simulator']):,}" if "Sun simulator" in active else "N/A"),("Pre-EL to FQC",lead_text)]
    st.markdown('<div class="mini-kpis">'+''.join(f'<div class="mini-kpi"><small>{escape(k)}</small><b>{escape(v)}</b></div>' for k,v in overview)+'</div>',unsafe_allow_html=True)
    def compact(fig,height=165):
        fig.update_layout(height=height,margin=dict(l=36,r=12,t=34,b=27),font=dict(size=10),title_font_size=12,title_y=0.96,xaxis_title=None,yaxis_title=None)
        fig.update_xaxes(tickangle=0,nticks=8,automargin=True)
        fig.update_yaxes(automargin=True,gridcolor='rgba(128,145,165,.16)')
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',showlegend=False)
        return fig
    hours=[f"{(i+6)%24:02d}:00" for i in range(24)]
    a,b=st.columns(2)
    for area,stage in [(a,"Lamination"),(b,"Sun simulator")]:
        d=data[stage]
        if stage not in active: area.warning(stage+" timestamp unavailable"); continue
        counts=d.groupby("hour").size().reindex(range(24),fill_value=0)
        fig=px.bar(x=hours,y=counts,title=stage+" hourly count"+(" (entry)" if stage=="Lamination" else ""),labels={"x":"Hour","y":"Unique modules"})
        fig.update_traces(marker_color=["#2563eb"]*8+["#0f766e"]*8+["#7c3aed"]*8,marker_line_width=0)
        area.plotly_chart(compact(fig),use_container_width=True,config={"displayModeBar":False})
    summary=[]
    def add(label,d,mask=None,denom=None):
        if "shift" not in d: return
        vals=[]
        for shift in ["A","B","C",None]:
            pick=d["shift"].eq(shift) if shift else pd.Series(True,index=d.index)
            n=int((pick&mask).sum()) if mask is not None else int(pick.sum())
            if denom is not None:
                total=int((pick&denom).sum()); vals.append(round(100*n/total,2) if total else None)
            else: vals.append(n)
        summary.append([label,*vals])
    for stage,d in data.items():
        add(stage,d)
        if stage in rej and rej[stage][2]:
            mask,valid,_=rej[stage]; add(stage+" rejection qty",d,mask); add(stage+" rejection %",d,mask,valid)
    iv=data["Sun simulator"]
    st.markdown("**Sun simulator | Critical parameters**")
    params=[p for p in ["PMAX","VOC","ISC","FF","IPM","VPM","CTM","TEMPERATURE"] if p in iv]
    if params:
        iv_cards=[]
        units={"PMAX":" W","VOC":" V","ISC":" A","FF":"%","IPM":" A","VPM":" V","CTM":"","TEMPERATURE":" °C"}
        for p in params:
            iv[p]=pd.to_numeric(iv[p],errors="coerce")
            label="TEMP" if p=="TEMPERATURE" else p
            val=(f"{iv[p].mean():.3f}" if p=="CTM" else f"{iv[p].mean():.2f}")+units[p] if iv[p].notna().any() else "N/A"
            iv_cards.append(f'<div class="mini-kpi"><small>{escape(label)}</small><b>{escape(val)}</b></div>')
        st.markdown('<div class="mini-kpis">'+''.join(iv_cards)+'</div>',unsafe_allow_html=True)
        p=st.sidebar.selectbox("24-hour trend parameter",params)
        trend=iv.groupby("hour")[p].mean().reindex(range(24))
        trend_col, power_col=st.columns(2)
        trend_col.plotly_chart(compact(px.line(x=hours,y=trend,markers=True,title=p+" | 24-hour trend",labels={"x":"Hour","y":p},color_discrete_sequence=["#0f9488"])),use_container_width=True,config={"displayModeBar":False})
        if "PMAX" in iv:
            labels=["<600","600–605","605–610","610–615","615–620","620–625","625–630",">=630"]
            bins=pd.cut(iv["PMAX"],[-float("inf"),600,605,610,615,620,625,630,float("inf")],right=False,labels=labels)
            power_col.plotly_chart(compact(px.bar(x=labels,y=bins.value_counts(sort=False).reindex(labels,fill_value=0),title="Live power distribution",labels={"x":"Watts","y":"Modules"},color_discrete_sequence=["#7c3aed"])),use_container_width=True,config={"displayModeBar":False})
    with st.expander("Shift summary",expanded=False):
        st.dataframe(pd.DataFrame(summary,columns=["Parameter","A","B","C","Total"]),hide_index=True,use_container_width=True)
    with st.expander("Module data | selected production day",expanded=False):
        serial=st.text_input("Filter module serial number")
        view=df[df["LOT_NUMBER"].astype(str).str.contains(serial,regex=False)] if serial else df
        st.dataframe(view,hide_index=True,use_container_width=True)
        st.download_button("Export selected data (CSV)",view.to_csv(index=False),"modules.csv","text/csv")

dashboard()
