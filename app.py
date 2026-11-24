import streamlit as st
import pandas as pd
import subprocess
import json
from contextlib import closing
import plotly.express as px
from datetime import date, datetime, time, timedelta

st.set_page_config(page_title="Data123 | MES Intelligence", layout="wide")
st.title("Data123 | MES Production Intelligence")
st.caption("Read-only internal MES analytics")
with st.sidebar:
    st.header("Database connection")
    host=st.text_input("Host")
    port=st.number_input("Port",1,65535,1433)
    db=st.text_input("Database")
    user=st.text_input("Read-only username")
    password=st.text_input("Password",type="password")
    st.caption("Windows .NET SqlClient — no ODBC driver needed")
    trust=st.checkbox("Trust server certificate (only if approved by IT)",False)
    connect=st.button("Connect / discover tables")
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
    $b['Trust Server Certificate'] = [bool]$req.trust
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
if connect:
    try:
        with closing(connection()) as c:
            st.session_state.tables=[tuple(row) for row in c.cursor().execute("SELECT TABLE_SCHEMA,TABLE_NAME FROM INFORMATION_SCHEMA.TABLES ORDER BY 1,2").fetchall()]
        st.sidebar.success("Connected (SELECT-only application; verify account permissions)")
    except Exception as e:
        st.sidebar.error("Connection failed: "+type(e).__name__+" | "+str(e.args[0] if e.args else "unknown"))
        st.session_state.pop("tables",None)
if not st.session_state.get("tables"):
    st.info("Enter local database credentials and connect to discover tables.")
    st.stop()
schema,table=st.sidebar.selectbox("MES table",st.session_state.tables,format_func=lambda x: ".".join(x))
day=st.sidebar.date_input("Production day",date.today())
start=datetime.combine(day,time(6))
end=start+timedelta(days=1)
auto=st.sidebar.checkbox("Auto refresh (60 seconds)",True)
st.sidebar.caption("Production day: 06:00 to next day 06:00. Database timestamps assumed plant-local.")
@st.fragment(run_every="60s" if auto else None)
def dashboard():
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
    st.metric("Unique FQC production",len(fqc) if "FQC" in active else "N/A")
    rej={}
    cards=st.columns(3)
    for card,(stage,level) in zip(cards,levels.items()):
        d=data[stage]
        if level not in d:
            card.metric(stage+" rejection","N/A"); continue
        codes=sorted(d[level].dropna().astype(str).unique().tolist())
        chosen=card.multiselect(stage+" rejection codes",codes,key=stage+"_codes")
        valid=d[level].notna()
        mask=d[level].astype(str).isin(chosen)&valid
        rej[stage]=(mask,valid,chosen)
        n=int(mask.sum()); total=int(valid.sum())
        card.metric(stage+" rejection",f"{n} / {total}" if chosen else "Select codes",f"{100*n/total:.2f}%" if chosen and total else None)
    hours=[f"{(i+6)%24:02d}:00" for i in range(24)]
    a,b=st.columns(2)
    for area,stage in [(a,"Lamination"),(b,"Sun simulator")]:
        d=data[stage]
        if stage not in active: area.warning(stage+" timestamp unavailable"); continue
        counts=d.groupby("hour").size().reindex(range(24),fill_value=0)
        area.plotly_chart(px.bar(x=hours,y=counts,title=stage+" hourly count"+(" (entry)" if stage=="Lamination" else ""),labels={"x":"Hour","y":"Unique modules"}),use_container_width=True)
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
    st.subheader("Shift summary")
    st.dataframe(pd.DataFrame(summary,columns=["Parameter","A","B","C","Total"]),hide_index=True,use_container_width=True)
    if "PRE_EL_TIME" in fqc:
        pre=pd.to_datetime(fqc["PRE_EL_TIME"],errors="coerce")
        if getattr(pre.dt,"tz",None) is not None: pre=pre.dt.tz_convert("Asia/Kolkata").dt.tz_localize(None)
        lead=(fqc["_time"]-pre).dt.total_seconds()/3600
        lead=lead.where(lead>=0)
        st.metric("Average Pre-EL to FQC elapsed time",f"{lead.mean():.2f} h" if lead.notna().any() else "N/A")
    iv=data["Sun simulator"]
    st.subheader("Sun simulator | Critical parameters")
    params=[p for p in ["PMAX","VOC","ISC","FF","IPM","VPM","CTM","TEMPERATURE"] if p in iv]
    if params:
        for c,p in zip(st.columns(len(params)),params):
            iv[p]=pd.to_numeric(iv[p],errors="coerce")
            c.metric(p,f"{iv[p].mean():.3f}" if iv[p].notna().any() else "N/A")
        p=st.selectbox("24-hour trend parameter",params)
        trend=iv.groupby("hour")[p].mean().reindex(range(24))
        st.plotly_chart(px.line(x=hours,y=trend,markers=True,labels={"x":"Hour","y":p}),use_container_width=True)
        if "PMAX" in iv:
            labels=["<600","600–605","605–610","610–615","615–620","620–625","625–630",">=630"]
            bins=pd.cut(iv["PMAX"],[-float("inf"),600,605,610,615,620,625,630,float("inf")],right=False,labels=labels)
            st.plotly_chart(px.bar(x=labels,y=bins.value_counts(sort=False).reindex(labels,fill_value=0),title="Live power distribution",labels={"x":"Watts","y":"Modules"}),use_container_width=True)
    st.subheader("Module data | selected production day")
    serial=st.text_input("Filter module serial number")
    view=df[df["LOT_NUMBER"].astype(str).str.contains(serial,regex=False)] if serial else df
    st.dataframe(view,hide_index=True,use_container_width=True)
    st.download_button("Export selected data (CSV)",view.to_csv(index=False),"modules.csv","text/csv")
dashboard()
