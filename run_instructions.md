# Run Instructions

```bash
cd ReliefMatch_Local
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pytest -q
streamlit run app.py
```
