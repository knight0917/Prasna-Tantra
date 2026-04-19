# Prasna Tantra

A Python project for Prasna (horary) astrology built around:

- a Skyfield-based planetary engine
- Prasna Tantra-inspired house judgment rules
- Tajaka yoga detection
- sincerity and timing helpers
- a Streamlit UI and Python callable API

## What It Does

Given a query time and place, the app computes:

- Ascendant and planetary positions
- whole-sign houses
- Vedic aspects
- planetary avasthas
- Tajaka yogas such as `Ithasala`, `Easarapha`, `Nakta`, `Yamaya`, and `Kamboola`
- house-specific horary judgment for common topics like marriage, wealth, children, illness, career, property, travel, and loss
- a basic timing estimate

## Project Layout

- `app.py`: Streamlit app
- `src/engine.py`: astronomical engine
- `src/main.py`: orchestration entrypoints
- `src/query_engine.py`: public high-level API
- `src/house_judgment.py`: core horary judgment
- `src/house_rules.py`: topic-specific rules
- `src/tajaka_yogas.py`: Tajaka yoga detection
- `src/timing.py`: timing estimation
- `src/sincerity_check.py`: sincerity rules
- `src/question_parser.py`: simple NLP topic parser

## Setup

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If `de421.bsp` is not already in the project root, the Streamlit app will download it on first run.

## Run

CLI:

```powershell
python -m src.main --prasna
```

Streamlit UI:

```powershell
streamlit run app.py
```

Or use the helper batch file:

```powershell
.\run.bat
.\run.bat --ui
```

## Python Usage

```python
from src.query_engine import run_prasna_query_from_coords

result = run_prasna_query_from_coords(
    28.6139,
    77.2090,
    "2026-02-22",
    "10:00:00",
    "marriage",
)

print(result["summary"])
```

## Supported Topics

- `wealth`
- `marriage`
- `children`
- `illness`
- `career`
- `property`
- `siblings`
- `longevity`
- `father`
- `travel`
- `legal`
- `loss`

## Tests

Run the lightweight smoke tests with:

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

## Notes

- This project mixes classical horary rules with pragmatic engineering choices.
- Timing rules in Prasna texts are interpretive and should be treated as approximate.
- The current implementation uses a simplified whole-sign approach for house lordship and aspect handling.
