# Airbnb Data Pipeline (NYC)

A beginner/intermediate Python project to practice:
- pandas cleaning
- CLI scripting with argparse
- terminal workflows
- Git + GitHub

## Structure
- `data/` : raw dataset (ignored by git)
- `src/` : pipeline code
- `output/` : generated artifacts (ignored by git)

## Run
```bash
pip install -r requirements.txt
python src/clean_airbnb_data.py --input data/airbnb_raw.csv --output output/airbnb_clean.csv