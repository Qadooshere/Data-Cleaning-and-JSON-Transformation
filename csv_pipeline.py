# csv_pipeline.py
# reads all CSVs from a folder, cleans + transforms each one,
# merges into a single dataframe, then dumps to JSON
#
# usage:
#   python csv_pipeline.py
#   python csv_pipeline.py --input ./my_folder --output result.json
#
# requirements: pip install pandas numpy chardet

import json
import argparse
import logging
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# column name aliases — maps whatever the source file calls things
# to the standard name we want in the output
COLUMN_MAP = {
    "firstname":    "first_name",
    "lastname":     "last_name",
    "fullname":     "full_name",
    "emailaddress": "email",
    "mail":         "email",
    "phone":        "phone_number",
    "mobile":       "phone_number",
    "tel":          "phone_number",
    "town":         "city",
    "nation":       "country",
    "wage":         "salary",
    "dept":         "department",
    "division":     "department",
    "dob":          "date_of_birth",
    "birthdate":    "date_of_birth",
    "sex":          "gender",
    "rating":       "score",
    "emp_id":       "id",
    "customer_id":  "id",
    "user_id":      "id",
}

# normalise gender to three values, everything else becomes NaN
GENDER_MAP = {
    "m": "male", "male": "male", "man": "male",
    "f": "female", "female": "female", "woman": "female",
    "other": "other", "nb": "other", "non-binary": "other",
}

# strings that actually mean "no value"
NULL_VALUES = ["", "N/A", "n/a", "NA", "null", "NULL", "None", "none", "-", "?"]

# column name substrings that suggest a date field
DATE_HINTS = ["date", "created", "updated", "timestamp", "dob", "born"]


def load_csv(path: Path) -> pd.DataFrame:
    # try chardet first, fall back to utf-8 if not installed
    encoding = "utf-8"
    try:
        import chardet
        with open(path, "rb") as f:
            detected = chardet.detect(f.read(100_000))
        encoding = detected.get("encoding") or "utf-8"
    except ImportError:
        pass

    # sniff delimiter — stop at first one that produces more than 1 column
    for sep in [",", ";", "\t", "|"]:
        try:
            df = pd.read_csv(path, encoding=encoding, sep=sep, low_memory=False)
            if df.shape[1] > 1:
                log.info(f"  {path.name}: {len(df)} rows, {df.shape[1]} cols (sep={repr(sep)}, enc={encoding})")
                return df
        except Exception:
            continue

    raise ValueError(f"couldn't parse {path.name} — tried , ; tab |")


def clean(df: pd.DataFrame, name: str) -> pd.DataFrame:
    before = len(df)

    # standardise column names
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(r"\s+", "_", regex=True)
        .str.replace(r"[^\w]", "", regex=True)
    )

    # drop rows/cols that are completely empty
    df.dropna(how="all", inplace=True)
    df.dropna(axis=1, how="all", inplace=True)

    # strip whitespace from text columns
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()

    # swap out fake nulls for real NaN
    df.replace(NULL_VALUES, np.nan, inplace=True)

    # duplicates
    dups = df.duplicated().sum()
    if dups:
        df.drop_duplicates(inplace=True)
        log.warning(f"  [{name}] dropped {dups} duplicate rows")

    # try to convert object columns to numeric if most values parse ok
    for col in df.columns:
        if df[col].dtype != object:
            continue
        converted = pd.to_numeric(df[col], errors="coerce")
        non_null = df[col].notna().sum()
        if non_null > 0 and converted.notna().sum() / non_null > 0.7:
            df[col] = converted

    # date columns — guess by column name
    for col in df.columns:
        if df[col].dtype == object and any(h in col for h in DATE_HINTS):
            df[col] = pd.to_datetime(df[col], errors="coerce", infer_datetime_format=True)

    log.info(f"  [{name}] cleaned: {before} -> {len(df)} rows")
    return df


def transform(df: pd.DataFrame, name: str) -> pd.DataFrame:
    # rename to canonical column names
    renames = {c: COLUMN_MAP[c] for c in df.columns if c in COLUMN_MAP}
    df.rename(columns=renames, inplace=True)

    # track which file each row came from — useful when debugging the output
    df["_source"] = name

    if "gender" in df.columns:
        df["gender"] = (
            df["gender"]
            .astype(str).str.lower().str.strip()
            .map(GENDER_MAP)
        )

    if "country" in df.columns:
        df["country"] = df["country"].astype(str).str.title().str.strip()

    if "email" in df.columns:
        df["email"] = df["email"].astype(str).str.lower().str.strip()

    # convert any datetime cols to strings so JSON serialisation doesn't choke
    for col in df.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns:
        df[col] = df[col].dt.strftime("%Y-%m-%dT%H:%M:%S")

    return df


def fix_duplicate_col_names(df: pd.DataFrame) -> pd.DataFrame:
    # pandas concat breaks if two frames have a column with the same name
    # (e.g. both have a "score" column). suffix duplicates so they're unique.
    seen = {}
    new_cols = []
    for col in df.columns:
        if col in seen:
            seen[col] += 1
            new_cols.append(f"{col}_{seen[col]}")
        else:
            seen[col] = 0
            new_cols.append(col)
    df.columns = new_cols
    return df


def merge_frames(frames: list) -> pd.DataFrame:
    frames = [fix_duplicate_col_names(df) for df in frames]
    master = pd.concat(frames, ignore_index=True, sort=False)

    # cross-file dedup — if the same email/id appears in multiple files, keep first
    key_cols = [c for c in ["email", "id"] if c in master.columns]
    if key_cols:
        before = len(master)
        master.drop_duplicates(subset=key_cols, keep="first", inplace=True)
        removed = before - len(master)
        if removed:
            log.warning(f"  cross-file dedup removed {removed} rows (keyed on {key_cols})")

    log.info(f"  merged: {len(master)} rows x {master.shape[1]} columns")
    return master


def build_validation_report(df: pd.DataFrame) -> dict:
    null_pct = (df.isnull().mean() * 100).round(2).to_dict()

    report = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "total_rows": len(df),
        "total_cols": df.shape[1],
        "columns": list(df.columns),
        "null_counts": df.isnull().sum().to_dict(),
        "null_pct": null_pct,
        "sources": df["_source"].value_counts().to_dict() if "_source" in df.columns else {},
        "warnings": [],
    }

    for col, pct in null_pct.items():
        if pct > 50:
            msg = f"'{col}' is {pct}% null"
            report["warnings"].append(msg)
            log.warning(f"  {msg}")

    if not report["warnings"]:
        log.info("  no issues found")

    return report


def write_json(df: pd.DataFrame, out_path: Path):
    records = df.where(df.notna(), other=None).to_dict(orient="records")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2, default=str)
    size_kb = out_path.stat().st_size / 1024
    log.info(f"  wrote {out_path} ({size_kb:.1f} KB)")


def run(input_dir, output_file):
    input_path = Path(input_dir)
    output_path = Path(output_file)

    csv_files = sorted(input_path.glob("*.csv"))
    if not csv_files:
        log.error(f"no CSV files found in '{input_path}'")
        return

    log.info(f"found {len(csv_files)} CSV file(s)")

    frames = []
    for f in csv_files:
        log.info(f"processing {f.name}")
        df = load_csv(f)
        df = clean(df, f.stem)
        df = transform(df, f.stem)
        frames.append(df)

    master = merge_frames(frames)

    report = build_validation_report(master)
    report_path = output_path.with_suffix(".validation.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    write_json(master, output_path)

    print(f"\noutput : {output_path}")
    print(f"report : {report_path}")
    print(f"rows   : {report['total_rows']}")
    print(f"cols   : {report['total_cols']}")
    if report["warnings"]:
        print(f"warnings:")
        for w in report["warnings"]:
            print(f"  - {w}")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="/data")
    parser.add_argument("--output", default="master_output.json")
    args = parser.parse_args()
    run(args.input, args.output)