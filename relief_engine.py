from __future__ import annotations
import re
import pandas as pd

CATEGORY_KEYWORDS={
    "water":["water","drinking","hydration","bottled"],
    "food":["food","meal","rice","bread","ration","groceries"],
    "medicine":["medicine","medication","medical","first aid","tablet","insulin"],
    "blanket":["blanket","blankets","bedding"],
    "shelter":["tent","tarpaulin","shelter","cover"],
    "hygiene":["hygiene","soap","sanitary","diaper","toiletry"],
    "power":["battery","power bank","generator","charging","torch","flashlight"],
    "clothing":["clothes","clothing","shoes"],
}

def infer_need(message:str)->str:
    s=str(message).lower()
    for cat,words in CATEGORY_KEYWORDS.items():
        if any(w in s for w in words):
            return cat
    return "other"

def priority_for(message:str, need:str)->str:
    s=str(message).lower()
    critical_terms=["urgent","critical","trapped","injured","medical emergency","no water","no medicine","children without water"]
    high_terms=["immediate","shortage","running out","evacuated","elderly","infants"]
    if any(t in s for t in critical_terms) or need in {"medicine","water"} and any(t in s for t in ["no ","without ","zero "]):
        return "Critical"
    if any(t in s for t in high_terms) or need in {"water","medicine","shelter"}:
        return "High"
    return "Normal"

def quantity_from_message(message:str)->float:
    m=re.search(r'(\d+(?:\.\d+)?)\s*(?:units?|people|families|bottles?|blankets?|kits?|packs?)?',str(message).lower())
    return float(m.group(1)) if m else 1.0

def analyze_requests(df:pd.DataFrame)->pd.DataFrame:
    required={"request_id","message","location"}
    if not required.issubset(df.columns):
        raise ValueError("Requests CSV must contain: request_id, message, location")
    out=df.copy()
    out["need"]=out["message"].map(infer_need)
    out["priority"]=out.apply(lambda r:priority_for(r["message"],r["need"]),axis=1)
    out["quantity_needed"]=out["message"].map(quantity_from_message)
    rank={"Critical":1,"High":2,"Normal":3}
    out["priority_rank"]=out["priority"].map(rank)
    return out

def match_resources(requests:pd.DataFrame,resources:pd.DataFrame,max_distance:float)->pd.DataFrame:
    required={"resource_id","resource_name","resource_type","category","available_quantity","location","distance_km"}
    if not required.issubset(resources.columns):
        raise ValueError("Resources CSV must contain: resource_id, resource_name, resource_type, category, available_quantity, location, distance_km")
    rows=[]
    for _,r in requests.iterrows():
        candidates=resources[
            (resources["category"].astype(str).str.lower()==str(r["need"]).lower()) &
            (pd.to_numeric(resources["available_quantity"],errors="coerce").fillna(0)>=float(r["quantity_needed"])) &
            (pd.to_numeric(resources["distance_km"],errors="coerce").fillna(10**9)<=max_distance)
        ].copy()
        if candidates.empty: continue
        candidates["distance_num"]=pd.to_numeric(candidates["distance_km"],errors="coerce")
        best=candidates.sort_values("distance_num").iloc[0]
        rows.append({
            "request_id":r["request_id"],"location":r["location"],"need":r["need"],
            "quantity_needed":r["quantity_needed"],"priority":r["priority"],"priority_rank":r["priority_rank"],
            "resource_name":best["resource_name"],"resource_type":best["resource_type"],
            "resource_location":best["location"],"available_quantity":best["available_quantity"],
            "distance_km":best["distance_km"]
        })
    return pd.DataFrame(rows)
