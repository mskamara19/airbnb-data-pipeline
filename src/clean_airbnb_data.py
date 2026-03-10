import argparse
import json 
import logging
from pathlib import Path

import numpy as np
import pandas as pd

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s"
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description="clean NYC Airbnb dataset and generate outputs."
    ) 
    parser.add_argument(
        "--input",
        required=True,
        help="Path to raw input CSV (e.g., data/airbnb_raw.csv)"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to cleaned output CSV (e.g., output/airbnb_clean.csv)"
    )
    parser.add_argument(
        "--summary",
        default="output/summary.json",
        help="Path to summary JSON (default: output/summary.json)"
    )   
    return parser.parse_args()

def clean_airbnb(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]
    # 1) Drop duplicate rows
    before = len(df)
    df = df.drop_duplicates()
    logging.info(f"Dropped duplicates: {before - len(df)}")

    # 2) Convert last_review to datetime
    if "last_review" in df.columns:
        df["last_review"] = pd.to_datetime(df["last_review"],errors="coerce")

    # 3) Clean price (dataset includes symbols/commas)
    if "price" in df.columns:
        df["price"] = (
            df["price"]
            .astype(str)
            .str.replace("$","",regex=False)
            .str.replace(",","",regex=False)
        )
        df["price"] = pd.to_numeric(df["price"], errors="coerce")
    # 4) Force numeric columns to numeric types
    numeric_col =[
        "minimum_nights",
        "number_of_reviews",
        "reviews_per_month",
        "calculated_host_listings_count",
        "availability_365",
    ]
    for col in numeric_col:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # 5) Simple sanity rules
    if "minimum nights" in df.columns:
        df.loc[df["minimum_nights"] < 1, "minimum_nights"] = np.nan

    if "price" in df.columns:
        df.loc[df["price"] <= 0, "price"] = np.nan

        # Remove extreme outliers (1st to 99th percentile)
        p01 = df["price"].quantile(0.01)
        p99 = df["price"].quantile(0.99)
        before = len(df)
        df = df[(df["price"].isna()) | ((df["price"] >= p01) & (df["price"] <= p99))]
        logging.info(f"Removed price outliers outside 1st-99th pct: {before - len(df)}")

    # 6) Fill reviews_per_month = 0 when number_of_reviews = 0
    if "reviews_per_month" in df.columns and "number_of_reviews" in df.columns:
        df.loc[
            (df["number_of_reviews"] == 0) & (df["reviews_per_month"].isna()),
            "reviews_per_month"
        ] = 0

    # 7) Drop rows missing critical fields
    critical = [c for c in ["id", "name", "host_id", "neighbourhood_group", "room_type"] if c in df.columns]
    before = len(df)
    df = df.dropna(subset=critical)
    logging.info(f"Dropped rows missing critical fields: {before - len(df)}")

    return df

def build_summary(df: pd.DataFrame) -> dict:
    summary = {
        "rows": int(len(df)),
        "columns": int(df.shape[1]),
    }
    if "price" in df.columns and df["price"].notna().any():
        summary["price"]= {
            "min": float(np.nanmin(df["price"])),
            "median": float(np.nanmedian(df["price"])),
            "mean": float(np.nanmean(df["price"])),
            "max": float(np.nanmax(df["price"])),

        }
    else:
        summary["price"] = None
    
    for col in ["neighbourhood_group", "room_type"]:
        if col in df.columns:
            summary[f"top_{col}"] = df[col].value_counts().head(10).to_dict()
    
    return summary

def main():
    setup_logging()
    args = parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    summary_path = Path(args.summary)

    # Ensure output folders exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    logging.info(f"Reading input: {input_path}")
    df_raw = pd.read_csv(input_path)

    logging.info("Cleaning data...")
    df_clean = clean_airbnb(df_raw)

    logging.info(f"Writing cleaned CSV: {output_path}")
    df_clean.to_csv(output_path, index=False)

    logging.info(f"Writing summary JSON: {summary_path}")
    summary = build_summary(df_clean)
    summary_path.write_text(json.dumps(summary, indent=2))

    logging.info("Done")

if __name__ == "__main__":
    main()