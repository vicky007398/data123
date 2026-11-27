import streamlit as st
import pandas as pd
import subprocess
import json
import os
from collections import Counter
from html import escape
from pathlib import Path
from contextlib import closing
import plotly.express as px
from datetime import date, datetime, time, timedelta

st.set_page_config(page_title="Data123 | MES Intelligence", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""<style>
[data-testid=stHeader]{height:1.8rem;background:transparent}
[data-testid=stToolbar]{visibility:visible}
[data-testid=stDeployButton]{display:none}
[data-testid=stSidebarCollapsedControl],[data-testid=collapsedControl]{visibility:visible!important;display:flex!important}
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


.el-board{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px;margin-bottom:2px}
.el-kpi{border:1px solid #cbd5e1;border-radius:8px;min-width:0;overflow:hidden;box-sizing:border-box;background:#f8fafc;color:#172b45;padding:0 7px 5px}
.el-shift{background:#2563eb;color:white;font-weight:700;font-size:12px;padding:4px 6px;margin:0 -7px 3px;display:flex;flex-wrap:wrap;justify-content:space-between;gap:2px}
.el-shift small{font-size:9px;font-weight:400}
.el-kpi:nth-child(2) .el-shift{background:#0f766e}
.el-kpi:nth-child(3) .el-shift{background:#7c3aed}
.el-stat{display:flex;align-items:baseline;justify-content:space-between;gap:4px;flex-wrap:wrap;padding:2px 0;font-size:11px;line-height:1.3}
.el-stat b{font-size:14px;overflow-wrap:anywhere}.el-ok{color:#15803d}.el-ng{color:#b91c1c}
.el-body{display:grid;grid-template-columns:minmax(0,0.9fr) minmax(0,1.2fr);gap:8px;align-items:start}
.defect-list{min-width:0;border-left:1px solid #cbd5e1;padding-left:7px}
.defect-head,.defect-row{display:flex;justify-content:space-between;align-items:baseline;gap:4px;font-size:10px;line-height:1.25;padding:2px 0}
.defect-head{font-weight:700;color:#123052;border-bottom:1px solid #cbd5e1}.defect-head small{font-size:9px}
.defect-row span{min-width:0;overflow-wrap:anywhere}.defect-row b{flex-shrink:0;color:#b91c1c}
@media(max-width:1050px){.el-body{grid-template-columns:1fr}.defect-list{border-left:0;padding-left:0}}
.el-title{font-size:13px;font-weight:650;margin:2px 0 4px;padding:3px 7px;border-radius:5px;background:#123052;color:white}
@media(max-width:760px){.el-board{grid-template-columns:1fr}.shift-strip{grid-template-columns:1fr}}

    

[data-testid=stMarkdownContainer] .shift-table-wrap{width:100%;overflow-x:auto;margin:0 0 5px}
[data-testid=stMarkdownContainer] table.shift-table{display:table;width:100%;min-width:0;table-layout:fixed;border-collapse:collapse;margin:0;font-size:10px;line-height:1.25;color:#172b45;background:#fff}
[data-testid=stMarkdownContainer] .shift-table th,[data-testid=stMarkdownContainer] .shift-table td{border:1px solid #b9c7d8;padding:3px 4px;white-space:normal;overflow-wrap:anywhere;vertical-align:middle}
[data-testid=stMarkdownContainer] .shift-table thead th{color:white;text-align:center;font-weight:700;font-size:10px}
[data-testid=stMarkdownContainer] .shift-table tbody td:nth-child(2n){text-align:right;font-weight:700}
[data-testid=stMarkdownContainer] .shift-table tbody td:nth-child(2n+1){}
[data-testid=stMarkdownContainer] .shift-table tbody tr:nth-child(even){background:#f1f5f9}
[data-testid=stMarkdownContainer] .shift-table .defect-heading th{background:#dbe6f3;color:#123052;text-align:left}
[data-testid=stMarkdownContainer] .shift-table .el-ok{color:#15803d}
[data-testid=stMarkdownContainer] .shift-table .el-ng{color:#b91c1c}

.hour-board{display:grid;gap:4px;padding-bottom:5px;min-width:0}
.hour-row{display:grid;grid-template-columns:24px repeat(8,minmax(0,1fr));gap:3px;align-items:stretch;--shift:#2563eb;--tint:#eff6ff}
.hour-b{--shift:#0f766e;--tint:#ecfdf5}.hour-c{--shift:#7c3aed;--tint:#f5f3ff}
.hour-shift{display:flex;align-items:center;justify-content:center;background:var(--shift);color:white;font-size:12px;font-weight:700;border-radius:4px}
.hour-cell{min-width:0;border:1px solid var(--shift);border-radius:4px;background:var(--tint);color:#172b45;text-align:center;overflow-wrap:anywhere}
.hour-cell small{display:block;font-size:10px;line-height:1.3;background:var(--shift);color:white;padding:2px 0}
.hour-cell b{display:block;font-size:14px;line-height:1.35;padding:3px 0}
@media(max-width:650px){.hour-row{grid-template-columns:20px repeat(8,minmax(0,1fr));gap:2px}.hour-cell small{font-size:8px}.hour-cell b{font-size:11px}}

[data-testid=stMarkdownContainer] .hour-table-wrap{overflow-x:auto;width:100%;padding-bottom:5px}
[data-testid=stMarkdownContainer] table.hour-table{display:table;width:100%;min-width:950px;table-layout:fixed;border-collapse:collapse;margin:0;font-size:11px;color:#172b45}
[data-testid=stMarkdownContainer] .hour-table th,[data-testid=stMarkdownContainer] .hour-table td{border:1px solid #b9c7d8;padding:4px 2px;text-align:center;white-space:nowrap}
[data-testid=stMarkdownContainer] .hour-table thead th{font-size:10px;font-weight:700}
[data-testid=stMarkdownContainer] .hour-table thead tr:first-child th{color:white;background:#123052}
[data-testid=stMarkdownContainer] .hour-table thead tr:first-child .shift-a{background:#2563eb}
[data-testid=stMarkdownContainer] .hour-table thead tr:first-child .shift-b{background:#0f766e}
[data-testid=stMarkdownContainer] .hour-table thead tr:first-child .shift-c{background:#7c3aed}
[data-testid=stMarkdownContainer] .hour-table th[rowspan], [data-testid=stMarkdownContainer] .hour-table tbody th{width:95px}
[data-testid=stMarkdownContainer] .hour-table tbody th{background:#e2e8f0;text-align:left;padding-left:7px}
[data-testid=stMarkdownContainer] .hour-table td{font-weight:700;font-size:12px}
[data-testid=stMarkdownContainer] .hour-table .h-0{background:#eff6ff;color:#1d4ed8}
[data-testid=stMarkdownContainer] .hour-table .h-1{background:#ecfdf5;color:#0f766e}
[data-testid=stMarkdownContainer] .hour-table .h-2{background:#f5f3ff;color:#7c3aed}

[data-testid=stMarkdownContainer] .power-wrap{width:100%;overflow-x:auto}
[data-testid=stMarkdownContainer] table.power-table{display:table;width:100%;min-width:570px;table-layout:fixed;border-collapse:collapse;margin:0;color:#172b45;font-size:11px}
[data-testid=stMarkdownContainer] .power-table th,[data-testid=stMarkdownContainer] .power-table td{border:1px solid #b9c7d8;padding:4px 5px;text-align:center;white-space:nowrap}
[data-testid=stMarkdownContainer] .power-table thead th{background:#123052;color:white}
[data-testid=stMarkdownContainer] .power-table tbody th{text-align:left;color:white}
.power-r0{background:#eff6ff}.power-r1{background:#ecfdf5}.power-r2{background:#f5f3ff}.power-r3{background:#e2e8f0;font-weight:700}
.power-r0 th{background:#2563eb}.power-r1 th{background:#0f766e}.power-r2 th{background:#7c3aed}.power-r3 th{background:#123052}
.power-total{font-weight:700}
[data-testid=stMarkdownContainer] .hour-table .shift-total{font-weight:800;border-left:2px solid #8395ab;border-right:2px solid #8395ab;background:#dbe6f3}
</style>""",unsafe_allow_html=True)
# Data123 V4.11
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
            stages={"Lamination":"LAM_DATE_IN","Sun simulator":"IV_TIME","FQC":"FQC_TIME","Pre-EL":"PRE_EL_TIME","Final EL":"EL_TIME"}
            levels={"Pre-EL":"PRE_EL_LEVEL","Final EL":"EL_LEVEL"}
            if "LOT_NUMBER" not in lookup:
                st.error("LOT_NUMBER not found"); return
            active={k:v for k,v in stages.items() if v in lookup and types[v] in ("datetime","datetime2","smalldatetime","datetimeoffset","date")}
            if not active:
                st.error("No supported timestamp columns found. Text dates need explicit parsing."); return
            defects={"Pre-EL":"PRE_EL_DEFECT","Final EL":"EL_DEFECT"}
            wanted=list(dict.fromkeys(["LOT_NUMBER",*active.values(),*levels.values(),*defects.values(),"PMAX","VOC","ISC","FF","IPM","VPM","CTM","TEMPERATURE","FQC_LEVEL"]))
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
        d=d[(d["_time"]>=start)&(d["_time"]<end)]
        level=levels.get(stage)
        if level in d.columns:
            d=d[d[level].astype("string").str.strip().str.upper().isin(["OK","NG"])]
            d["_status_order"]=d[level].astype("string").str.strip().str.upper()
            d=d.sort_values(["_time","_status_order"]).drop_duplicates("LOT_NUMBER",keep="first").drop(columns="_status_order")
        else:
            d=d.sort_values("_time").drop_duplicates("LOT_NUMBER",keep="first")
        d["hour"]=((d["_time"]-start).dt.total_seconds()//3600).astype(int)
        d["shift"]=d["hour"].map(lambda h:"ABC"[h//8])
        return d
    data={s:events(s) for s in stages if s!="Pre-EL"}
    # Recover completed lamination modules with no recorded entry timestamp.
    # Never infer a lamination hour from Pre-EL or another upstream process.
    if "Lamination" in active:
        try:
            q_lam=("SELECT T.LOT_NUMBER, MIN(T.EDIT_TIME) FROM "
                   +ident(schema)+".[WIP_TRANSACTION] T "
                   "WHERE T.STEP_NAME=N'层压' AND T.ACTIVITY='TRACKOUT' "
                   "AND T.EDIT_TIME>=? AND T.EDIT_TIME<? "
                   "AND (T.UNDO_FLAG IS NULL OR T.UNDO_FLAG=0) "
                   "AND NULLIF(LTRIM(RTRIM(T.LOT_NUMBER)), '') IS NOT NULL "
                   "AND NOT EXISTS (SELECT 1 FROM "+ident(schema)+"."+ident(table)+" C "
                   "WHERE C.LOT_NUMBER=T.LOT_NUMBER AND C."+ident(lookup[active["Lamination"]])+" IS NOT NULL) "
                   "GROUP BY T.LOT_NUMBER")
            with closing(connection()) as c:
                fallback_rows=c.cursor().execute(q_lam,start,end).fetchall()
            fallback=pd.DataFrame(fallback_rows,columns=["LOT_NUMBER","_time"])
            fallback["_time"]=pd.to_datetime(fallback["_time"],errors="coerce")
            fallback=fallback.dropna(subset=["_time"])
            if getattr(fallback["_time"].dt,"tz",None) is not None:
                fallback["_time"]=fallback["_time"].dt.tz_convert("Asia/Kolkata").dt.tz_localize(None)
            fallback=fallback[(fallback["_time"]>=start)&(fallback["_time"]<end)].copy()
            fallback["hour"]=((fallback["_time"]-start).dt.total_seconds()//3600).astype(int)
            fallback["shift"]=fallback["hour"].map(lambda h:"ABC"[h//8])
            lam=data["Lamination"]
            fallback=fallback[~fallback["LOT_NUMBER"].astype(str).str.strip().isin(lam["LOT_NUMBER"].astype(str).str.strip())]
            data["Lamination"]=pd.concat([lam,fallback],ignore_index=True)
        except Exception:
            st.warning("Lamination TRACKOUT fallback unavailable; Lam Count currently uses LAM_DATE_IN only.")


    # Count inspection attempts, not unique barcodes, for Pre-EL only.
    # TAKE_PHOTO is the observed activity carrying CUR_LEVEL OK/NG.
    pre_error=None
    try:
        q_pre=("SELECT DISTINCT TRANSACTION_KEY, LOT_NUMBER, EDIT_TIME, "
               "UPPER(LTRIM(RTRIM(CUR_LEVEL))) FROM "+ident(schema)+".[WIP_TRANSACTION] "
               "WHERE STEP_NAME='Pre_EL' AND ACTIVITY='TAKE_PHOTO' "
               "AND EDIT_TIME>=? AND EDIT_TIME<? "
               "AND UPPER(LTRIM(RTRIM(CUR_LEVEL))) IN ('OK','NG') "
               "AND NULLIF(LTRIM(RTRIM(LOT_NUMBER)), '') IS NOT NULL "
               "AND NULLIF(LTRIM(RTRIM(TRANSACTION_KEY)), '') IS NOT NULL "
               "AND (UNDO_FLAG IS NULL OR UNDO_FLAG=0)")
        with closing(connection()) as c:
            records=c.cursor().execute(q_pre,start,end).fetchall()
        pre=pd.DataFrame(records,columns=["TRANSACTION_KEY","LOT_NUMBER","_time","PRE_EL_LEVEL"])
        pre["_time"]=pd.to_datetime(pre["_time"],errors="coerce")
        pre=pre.dropna(subset=["_time"])
        if getattr(pre["_time"].dt,"tz",None) is not None:
            pre["_time"]=pre["_time"].dt.tz_convert("Asia/Kolkata").dt.tz_localize(None)
        pre=pre[(pre["_time"]>=start)&(pre["_time"]<end)]
        pre=pre.drop_duplicates()
        if pre["TRANSACTION_KEY"].duplicated().any():
            raise ValueError("Conflicting records for the same transaction key")
        pre["hour"]=((pre["_time"]-start).dt.total_seconds()//3600).astype(int)
        pre["shift"]=pre["hour"].map(lambda h:"ABC"[h//8])
        # Historical inspection attempts and current module defect descriptions are separate sources.
        data["Pre-EL"]=pre
    except Exception as e:
        pre_error=str(e).replace(password,"[redacted]")
        data["Pre-EL"]=pd.DataFrame()
    # Historical defect events: count each transaction once per defect type and shift.
    pre_defect_counts={}
    pre_defect_error=False
    try:
        q_def=("SELECT EDIT_TIME, TRANSACTION_KEY, REASON_CODE_NAME FROM "
               +ident(schema)+".[WIP_DEFECT] WHERE STEP_NAME='Pre_EL' "
               "AND EDIT_TIME>=? AND EDIT_TIME<? "
               "AND NULLIF(LTRIM(RTRIM(TRANSACTION_KEY)), '') IS NOT NULL "
               "AND NULLIF(LTRIM(RTRIM(REASON_CODE_NAME)), '') IS NOT NULL")
        with closing(connection()) as c:
            defect_records=c.cursor().execute(q_def,start,end).fetchall()
        seen=set()
        for stamp,key,name in defect_records:
            ts=pd.to_datetime(stamp,errors="coerce")
            if pd.isna(ts): continue
            if ts.tzinfo is not None:
                ts=ts.tz_convert("Asia/Kolkata").tz_localize(None)
            if not start<=ts<end: continue
            shift="ABC"[int((ts-start).total_seconds()//28800)]
            name=" ".join(str(name).split()).casefold()
            item=(shift,str(key).strip(),name)
            if item in seen: continue
            seen.add(item)
            pre_defect_counts.setdefault(shift,Counter())[name]+=1
    except Exception:
        pre_defect_error=True
    fqc=data["FQC"]
    st.markdown(f'<div class="live-head"><strong>Live Dashboard</strong><span>{day:%d %b %Y} · MES connected · Updated {datetime.now():%H:%M:%S} · V4.11</span></div>',unsafe_allow_html=True)
    rej={}
    now=datetime.now()
    pre_panel, final_panel = st.columns(2, gap="small")
    panels={"Pre-EL":pre_panel,"Final EL":final_panel}
    for stage,level in levels.items():
        d=data[stage]
        if level not in d:
            panels[stage].warning("Pre-EL transaction query unavailable: "+pre_error if stage=="Pre-EL" and pre_error else stage+" inspection status or timestamp unavailable")
            continue
        status=d[level].astype("string").str.strip().str.upper()
        valid=status.isin(["OK","NG"])
        mask=status.eq("NG").fillna(False)
        rej[stage]=(mask,valid,{"NG"})
        defect_col=defects[stage]
        defect_data=d
        shift_values=[]
        shift_defects=[]
        headers=[]
        for i,(shift,timing) in enumerate([("A","06:00–14:00"),("B","14:00–22:00"),("C","22:00–06:00")]):
            pick=d["shift"].eq(shift)
            ok=int((pick&status.eq("OK").fillna(False)).sum())
            ng=int((pick&mask).sum())
            total=ok+ng
            future=now < start+timedelta(hours=i*8)
            values=["—"]*4 if future else [f"{total:,}",f"{ok:,}",f"{ng:,}",f"{100*ng/total:.2f}%" if total else "—"]
            counts=Counter()
            if not future and stage=="Pre-EL":
                counts=pre_defect_counts.get(shift,Counter())
            elif not future and defect_col in defect_data.columns and level in defect_data.columns and "shift" in defect_data.columns:
                defect_pick=defect_data["shift"].eq(shift)&defect_data[level].astype("string").str.strip().str.upper().eq("NG").fillna(False)
                for raw in defect_data.loc[defect_pick,defect_col]:
                    names=set()
                    if pd.notna(raw):
                        for entry in str(raw).split(";"):
                            name=" ".join(entry.split(":",1)[0].strip().split()).casefold()
                            if name: names.add(name)
                    counts.update(names if stage=="Pre-EL" else (names or {"unspecified"}))
            ranked=sorted(counts.items(),key=lambda item:(-item[1],item[0]))[:5]
            if not future and stage=="Pre-EL" and pre_defect_error:
                ranked=[("Defect query unavailable","—")]
            elif not future and stage!="Pre-EL" and ng and defect_col not in defect_data.columns:
                ranked=[("Defect column unavailable","—")]
            shift_values.append(values)
            shift_defects.append([(escape(name.title()),f"{qty:,}" if isinstance(qty,int) else str(qty)) for name,qty in ranked]+([("","")] if stage=="Pre-EL" and not future else [("—","—")])*(5-len(ranked)))
            headers.append(f'<th colspan="2" class="shift-{shift.lower()}">{shift} SHIFT · {timing}</th>')
        rows=[]
        for j,label in enumerate(["Total Modules","OK Modules","NG Modules","NG %"]):
            cls=["","el-ok","el-ng","el-ng"][j]
            rows.append("<tr>"+"".join(f'<td>{label}</td><td class="qty {cls}">{vals[j]}</td>' for vals in shift_values)+"</tr>")
        rows.append("<tr class='defect-heading'>"+("<th>Top 5 Defects</th><th>Qty</th>"*3)+"</tr>")
        for j in range(5):
            rows.append("<tr>"+"".join(f'<td>{items[j][0]}</td><td class="qty">{items[j][1]}</td>' for items in shift_defects)+"</tr>")
        panels[stage].markdown('<div class="el-title">'+escape(stage+(" | Test attempts incl. rework" if stage=="Pre-EL" else ""))+'</div><div class="shift-table-wrap"><table class="shift-table"><colgroup><col style="width:23%"><col style="width:10.33%"><col style="width:23%"><col style="width:10.33%"><col style="width:23%"><col style="width:10.33%"></colgroup><thead><tr>'+''.join(headers)+'</tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>',unsafe_allow_html=True)
    def compact(fig,height=165):
        fig.update_layout(height=height,margin=dict(l=36,r=12,t=34,b=27),font=dict(size=10),title_font_size=12,title_y=0.96,xaxis_title=None,yaxis_title=None)
        fig.update_xaxes(tickangle=0,nticks=8,automargin=True)
        fig.update_yaxes(automargin=True,gridcolor='rgba(128,145,165,.16)')
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',showlegend=False)
        return fig
    hours=[f"{(i+6)%24:02d}:00" for i in range(24)]
    hourly_rows=[]
    for stage,label in [("Lamination","Lam Count"),("Sun simulator","Sun Count")]:
        d=data[stage]
        counts=d.groupby("hour").size().reindex(range(24),fill_value=0) if stage in active else None
        cells=[]
        for h in range(24):
            value="—" if counts is None or now < start+timedelta(hours=h) else f"{int(counts.loc[h]):,}"
            cells.append(f'<td class="h-{h//8}">{value}</td>')
            if h%8==7:
                first=h-7
                total="—" if counts is None or now < start+timedelta(hours=first) else f"{int(sum(counts.loc[k] for k in range(first,h+1) if now>=start+timedelta(hours=k))):,}"
                cells.append(f'<td class="h-{h//8} shift-total">{total}</td>')
        hourly_rows.append(f'<tr><th scope="row">{label}</th>'+''.join(cells)+'</tr>')
    axis=''.join(f'<th class="h-{h//8}">{(h+6)%24}-{(h+7)%24}</th>'+ (f'<th class="h-{h//8} shift-total">Total</th>' if h%8==7 else "") for h in range(24))
    st.markdown('<div class="el-title">Hourly Production | Modules</div><div class="hour-table-wrap"><table class="hour-table"><thead><tr><th rowspan="2">Process</th><th colspan="9" class="shift-a">A SHIFT</th><th colspan="9" class="shift-b">B SHIFT</th><th colspan="9" class="shift-c">C SHIFT</th></tr><tr>'+axis+'</tr></thead><tbody>'+''.join(hourly_rows)+'</tbody></table></div>',unsafe_allow_html=True)
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
    st.markdown("**Sun Simulator | Critical Parameters (Average Values)**")
    params=[p for p in ["PMAX","VOC","ISC","FF","IPM","VPM"] if p in iv]
    if params:
        iv_cards=[]
        units={"PMAX":" W","VOC":" V","ISC":" A","FF":"%","IPM":" A","VPM":" V","CTM":"","TEMPERATURE":" °C"}
        for p in params:
            iv[p]=pd.to_numeric(iv[p],errors="coerce")
            label={"PMAX":"Pmax","VOC":"Voc","ISC":"Isc","FF":"FF","IPM":"Ipm","VPM":"Vpm"}[p]
            val=(f"{iv[p].mean():.3f}" if p=="CTM" else f"{iv[p].mean():.2f}")+units[p] if iv[p].notna().any() else "N/A"
            iv_cards.append(f'<div class="mini-kpi"><small>{escape(label)}</small><b>{escape(val)}</b></div>')
        st.markdown('<div class="mini-kpis">'+''.join(iv_cards)+'</div>',unsafe_allow_html=True)
        if "PMAX" in iv:
            labels=["<600","600–605","605–610","610–615","615–620","620–625","625–630",">=630"]
            bins=pd.cut(iv["PMAX"],[-float("inf"),600,605,610,615,620,625,630,float("inf")],right=False,labels=labels)
            distribution=pd.crosstab(bins,iv["shift"]).reindex(index=labels,columns=["A","B","C"],fill_value=0)
            distribution["Total"]=distribution.sum(axis=1)
            future=[now < start+timedelta(hours=i*8) for i in range(3)]
            st.markdown('<div class="el-title">Live Power Distribution | Modules by wattage</div>',unsafe_allow_html=True)
            areas=st.columns(4,gap="small")
            ymax=100
            for i,(label,color) in enumerate(zip(["A Shift","B Shift","C Shift","Total"],["#2563eb","#0f766e","#7c3aed","#123052"])):
                counts=distribution.iloc[:,i]
                pending=i<3 and future[i]
                title=label
                percentages=(counts/counts.sum()*100).tolist() if counts.sum() else [0.0]*len(labels)
                fig=px.bar(x=labels,y=[None]*len(labels) if pending else percentages,title=title,labels={"x":"Watts","y":"Distribution (%)"})
                fig.update_traces(marker_color=color,marker_line_width=0,text=["—"]*len(labels) if pending else [f"{v:.1f}%" for v in percentages],textposition="outside",cliponaxis=False,textfont_size=10)
                fig=compact(fig,height=205)
                fig.update_layout(bargap=.08,margin=dict(l=30,r=8,t=30,b=65))
                fig.update_xaxes(tickmode="array",tickvals=labels,ticktext=labels,tickangle=-90,tickfont_size=9)
                fig.update_yaxes(range=[0,115],rangemode="tozero",ticksuffix="%",tickvals=[0,25,50,75,100])
                fig.update_traces(customdata=counts.tolist(),hovertemplate="%{x} W<br>Distribution: %{y:.2f}%<br>Modules: %{customdata}<extra></extra>")
                if pending or not counts.sum():
                    fig.add_annotation(text="Shift not started —" if pending else "No valid Pmax data —",xref="paper",yref="paper",x=.5,y=.5,showarrow=False)
                areas[i].plotly_chart(fig,use_container_width=True,config={"displayModeBar":False},key=f"power_hist_{i}")
    with st.expander("Shift summary",expanded=False):
        st.dataframe(pd.DataFrame(summary,columns=["Parameter","A","B","C","Total"]),hide_index=True,use_container_width=True)
    with st.expander("Module data | selected production day",expanded=False):
        serial=st.text_input("Filter module serial number")
        view=df[df["LOT_NUMBER"].astype(str).str.contains(serial,regex=False)] if serial else df
        st.dataframe(view,hide_index=True,use_container_width=True)
        st.download_button("Export selected data (CSV)",view.to_csv(index=False),"modules.csv","text/csv")

dashboard()
