# 🆘 ReliefMatch Local

ReliefMatch Local is a **local-first disaster-relief decision-support dashboard** that converts structured or de-identified disaster requests into normalized needs, assigns transparent priority levels, matches needs with available synthetic/resource records, and proposes a simple delivery sequence.

## Important safety boundary

This application **does not independently verify disaster reports**. Software validation is not field verification. It does not verify identities, addresses, road safety, weather, security conditions, or whether a request is genuine. It must not be used as an autonomous dispatch or emergency-command system.

## Features

- 🆘 Request normalization
- 🚨 Transparent Critical / High / Normal priority rules
- 📦 Supply and volunteer matching
- 📍 Configurable distance constraint
- 🚚 Suggested delivery sequence
- 📊 Interactive priority analytics
- 📄 JSON report export
- 📊 CSV input
- 🧪 Synthetic demo data
- 🔒 Local processing without cloud AI APIs
- 🧪 Automated tests

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
streamlit run app.py
```

## Request CSV

```csv
request_id,message,location
REQ-001,"URGENT: Shelter North has no drinking water for 40 people.",Shelter North
```

## Resource CSV

```csv
resource_id,resource_name,resource_type,category,available_quantity,location,distance_km
RES-001,Water Supply Unit,Supply,water,80,Depot North,6
```

Supported categories include water, food, medicine, blanket, shelter, hygiene, power, and clothing.

## Architecture

```text
Disaster request
      ↓
Need normalization
      ↓
Transparent priority rules
      ↓
Resource compatibility + quantity + distance
      ↓
Suggested delivery sequence
      ↓
Human / official verification
      ↓
Authorized dispatch
```

## Privacy

The dashboard is designed for local processing. Use synthetic or de-identified data and avoid unnecessary personal information.

## Responsible use

Use official emergency-management channels and trained responders for real incidents. Treat every generated match and priority as decision support requiring human verification.
