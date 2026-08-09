import pandas as pd
from relief_engine import analyze_requests, match_resources

def test_normalization_and_priority():
    df=pd.DataFrame([{"request_id":"R1","message":"URGENT: no drinking water for 20 people","location":"Camp"}])
    out=analyze_requests(df)
    assert out.iloc[0]["need"]=="water"
    assert out.iloc[0]["priority"]=="Critical"

def test_resource_matching():
    req=pd.DataFrame([{"request_id":"R1","message":"need 20 water units","location":"Camp"}])
    res=pd.DataFrame([{
        "resource_id":"S1","resource_name":"Water Depot","resource_type":"Supply",
        "category":"water","available_quantity":30,"location":"Depot","distance_km":5
    }])
    nr=analyze_requests(req)
    matches=match_resources(nr,res,25)
    assert len(matches)==1
    assert matches.iloc[0]["resource_name"]=="Water Depot"
