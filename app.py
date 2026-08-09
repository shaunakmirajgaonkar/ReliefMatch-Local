import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from relief_engine import analyze_requests, match_resources

st.set_page_config(page_title="ReliefMatch Local", page_icon="🆘", layout="wide")

st.markdown("""
<style>
.stApp{background:#f7f9fc;color:#172033}
.block-container{max-width:1450px;padding-top:1.2rem;padding-bottom:3rem}
[data-testid="stSidebar"]{background:#fff;border-right:1px solid #dbe3ee}
[data-testid="stSidebar"] *{color:#172033!important}
.hero{padding:1.8rem 2rem;border-radius:24px;margin-bottom:1.2rem;
background:linear-gradient(135deg,#b91c1c,#ef4444 48%,#f59e0b);
box-shadow:0 14px 35px rgba(185,28,28,.18)}
.hero h1{color:#fff!important;margin:0;font-size:2.6rem;font-weight:850}
.hero p{color:#fff7ed!important;margin:.45rem 0 0;font-size:1rem}
.card{background:#fff;border:1px solid #dbe3ee;border-radius:17px;padding:1.1rem 1.2rem;
min-height:108px;box-shadow:0 5px 18px rgba(15,23,42,.05)}
.label{color:#64748b!important;font-size:.86rem;font-weight:650}
.value{color:#0f172a!important;font-size:1.65rem;font-weight:850;margin-top:.25rem}
.critical{background:#fff1f2;border:1px solid #fecdd3;border-left:5px solid #ef4444;
color:#9f1239!important;padding:.9rem 1rem;border-radius:12px;margin:.55rem 0}
.high{background:#fff7ed;border:1px solid #fed7aa;border-left:5px solid #f97316;
color:#9a3412!important;padding:.9rem 1rem;border-radius:12px;margin:.55rem 0}
.ok{background:#ecfdf5;border:1px solid #a7f3d0;border-left:5px solid #10b981;
color:#065f46!important;padding:.9rem 1rem;border-radius:12px;margin:.55rem 0}
.small{color:#64748b!important;font-size:.86rem}
h1,h2,h3,h4,p,label{color:#172033}
.stButton>button{border-radius:10px;font-weight:750;border:1px solid #b91c1c}
.stDownloadButton>button{border-radius:10px;font-weight:750;background:#b91c1c;color:#fff!important}
</style>
""", unsafe_allow_html=True)

def metric(label, value):
    st.markdown(f'<div class="card"><div class="label">{label}</div><div class="value">{value}</div></div>', unsafe_allow_html=True)

def render_results(requests_df, supplies_df, routes_df, analysis, key):
    c1,c2,c3,c4 = st.columns(4)
    with c1: metric("Requests", len(requests_df))
    with c2: metric("Critical Needs", int((requests_df["priority"]=="Critical").sum()))
    with c3: metric("Resources", len(supplies_df))
    with c4: metric("Matched Requests", int(analysis["matched_requests"]))

    st.markdown("## 🚨 Verified-Workflow Status")
    st.info("This dashboard uses rule-based validation and matching. It does not independently verify facts on the ground, identities, locations, or safety conditions. Human/official verification is required before dispatch.")

    st.markdown("## 📋 Normalized Disaster Needs")
    st.dataframe(requests_df, width="stretch", hide_index=True)

    st.markdown("## 🎯 Priority Distribution")
    counts=requests_df["priority"].value_counts().rename_axis("priority").reset_index(name="requests")
    fig=px.bar(counts,x="priority",y="requests",color="priority",title="Requests by Priority",
               template="plotly_white")
    fig.update_layout(height=380,margin=dict(l=10,r=10,t=55,b=10),showlegend=False)
    st.plotly_chart(fig,width="stretch",key=f"{key}_priority")

    st.markdown("## 📦 Supply & Volunteer Matching")
    if routes_df.empty:
        st.warning("No compatible resource match was found in the supplied demo inventory.")
    else:
        st.dataframe(routes_df,width="stretch",hide_index=True)

    st.markdown("## 🚚 Suggested Delivery Sequence")
    if routes_df.empty:
        st.markdown('<div class="high">No route suggestions are available until a compatible supply or volunteer resource is present.</div>', unsafe_allow_html=True)
    else:
        for i,row in routes_df.sort_values(["priority_rank","distance_km"]).reset_index(drop=True).iterrows():
            cls="critical" if row["priority"]=="Critical" else ("high" if row["priority"]=="High" else "ok")
            st.markdown(
                f'<div class="{cls}"><b>Stop {i+1}: {row["resource_name"]}</b> → {row["request_id"]} · '
                f'{row["need"]} · {row["quantity_needed"]} · {row["distance_km"]} km · '
                f'{row["resource_type"]}</div>', unsafe_allow_html=True)

    st.markdown("## 🧭 Matching Logic")
    for item in analysis["logic"]:
        st.markdown(f"• {item}")

    report={
        "tool":"ReliefMatch Local",
        "generated_at":datetime.now(timezone.utc).isoformat(),
        "request_count":len(requests_df),
        "critical_count":int((requests_df["priority"]=="Critical").sum()),
        "matched_requests":int(analysis["matched_requests"]),
        "normalized_requests":requests_df.to_dict(orient="records"),
        "resource_matches":routes_df.to_dict(orient="records"),
        "disclaimer":analysis["disclaimer"],
    }
    st.download_button("⬇️ Download Relief Matching Report (JSON)",
                       json.dumps(report,indent=2), "reliefmatch_report.json",
                       "application/json",key=f"{key}_download")

st.markdown("""
<div class="hero">
<h1>🆘 ReliefMatch Local</h1>
<p>Local-first disaster needs normalization, priority assessment, resource matching, and delivery planning.</p>
</div>
""",unsafe_allow_html=True)

st.sidebar.markdown("## ⚙️ Relief Settings")
st.sidebar.caption("● LOCAL DISASTER-RESPONSE INTELLIGENCE")
max_distance=st.sidebar.slider("Maximum matching distance (km)",1,100,25)
st.sidebar.warning("Use only as decision support. Official responders must verify requests, resources, routes, and safety before dispatch.")

tab1,tab2,tab3,tab4=st.tabs(["📝 Request Intake","📦 Resources","🧪 Demo Data","ℹ️ Methodology"])

with tab1:
    st.subheader("Convert a Disaster Message into a Structured Need")
    st.caption("Use synthetic or de-identified requests. Do not enter unnecessary personal or sensitive information.")
    text=st.text_area("Message / request",height=130,
                      placeholder="Example: Shelter B needs 40 drinking-water units and 10 blankets. 12 families are waiting.",
                      key="request_text")
    location=st.text_input("Location label",placeholder="Shelter B / Ward 4 / Relief Camp North",key="request_location")
    if st.button("🧭 Analyze & Normalize Request",type="primary",key="analyze_one"):
        if not text.strip():
            st.error("Enter a request message first.")
        else:
            req=analyze_requests(pd.DataFrame([{"request_id":"REQ-001","message":text,"location":location or "Unspecified"}]))
            resources=pd.read_csv(Path(__file__).parent/"sample_data"/"demo_resources.csv")
            routes=match_resources(req,resources,max_distance)
            render_results(req,resources,routes,{"matched_requests":routes["request_id"].nunique() if not routes.empty else 0,
                "logic":["Keyword/category mapping identifies likely need types.","Priority rules consider urgency terms and essential needs.","Resource matching considers category compatibility, available quantity, and distance.","Delivery ordering prioritizes critical needs before lower-priority needs."],
                "disclaimer":"Rule-based decision support only; requests and real-world conditions require human/official verification."},"single")

with tab2:
    st.subheader("Upload De-identified Requests and Resources")
    req_file=st.file_uploader("Requests CSV",type=["csv"],key="req_csv")
    res_file=st.file_uploader("Resources CSV",type=["csv"],key="res_csv")
    if req_file and res_file:
        req_raw=pd.read_csv(req_file); res_raw=pd.read_csv(res_file)
        st.success(f"Loaded {len(req_raw)} request(s) and {len(res_raw)} resource(s).")
        with st.expander("Preview uploaded requests"): st.dataframe(req_raw,width="stretch",hide_index=True)
        with st.expander("Preview uploaded resources"): st.dataframe(res_raw,width="stretch",hide_index=True)
        if st.button("🚚 Match Needs to Resources",type="primary",key="match_csv"):
            try:
                req=analyze_requests(req_raw)
                routes=match_resources(req,res_raw,max_distance)
                render_results(
                    req,res_raw,routes,
                    {"matched_requests":routes["request_id"].nunique() if not routes.empty else 0,
                     "logic":["Need categories are normalized from structured request fields/message text.",
                              "Priority is assigned by transparent rules.",
                              "Resources are matched by need category and available capacity.",
                              "Distance is used only as a configurable routing preference."],
                     "disclaimer":"Uploaded data is processed locally by this application. Matching is not field verification or dispatch authorization."},
                    "csv"
                )
            except Exception as exc:
                st.error(f"Invalid CSV data: {exc}")

with tab3:
    st.subheader("Synthetic Demonstration")
    req=pd.read_csv(Path(__file__).parent/"sample_data"/"demo_requests.csv")
    res=pd.read_csv(Path(__file__).parent/"sample_data"/"demo_resources.csv")
    st.dataframe(req,width="stretch",hide_index=True)
    if st.button("🚨 Run Demo Matching",type="primary",key="demo_match"):
        normalized=analyze_requests(req); routes=match_resources(normalized,res,max_distance)
        render_results(normalized,res,routes,{"matched_requests":routes["request_id"].nunique(),
            "logic":["Synthetic messages are converted into structured need categories.","Critical/high priorities are surfaced first.","Resource compatibility, quantity, and configurable distance are considered.","Suggested sequences are decision support, not autonomous dispatch."],
            "disclaimer":"All demonstration data is synthetic. Real requests must be verified by authorized responders."},"demo")

with tab4:
    st.subheader("Methodology & Safety")
    st.markdown("""
### What the system does
1. Normalizes incoming requests into a small set of need categories.
2. Assigns a transparent priority using rule-based indicators.
3. Matches needs against available supplies/volunteers.
4. Checks basic quantity and configurable distance constraints.
5. Produces a suggested delivery sequence.

### What it does not do
- It does not independently verify that a request is genuine.
- It does not verify identities, addresses, road conditions, weather, or security conditions.
- It does not authorize emergency dispatch.
- It does not replace incident-command systems or trained responders.
- It does not claim that a message has been "verified" merely because it passed software rules.

Use official emergency-management processes and human verification before acting on any suggested match.
""")
