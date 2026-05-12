# CSV to JSON Data Pipeline (Upwork Project)

This repository contains a small data pipeline that reads multiple CSV files from a folder, cleans and standardizes them, merges them into a single dataset, and exports the result to JSON along with a validation report.

## Upwork Project

I am seeking a skilled freelancer to clean multiple CSV files, transform the data, and merge them into a single master JSON file for database insertion. The ideal candidate will have experience in data handling and scripting, ensuring accuracy and efficiency in the process. Attention to detail and the ability to manage large datasets are essential.

## Objective

- Convert a folder of CSV files into a single consolidated JSON output.
- Standardize column naming across different CSV schemas (aliases to canonical field names).
- Clean common data quality issues (null placeholders, whitespace, duplicates, inconsistent casing).
- Produce a simple validation report (null counts/percentages and warnings) to quickly assess output quality.

## Functionality

The pipeline script:

- Loads all `*.csv` files from an input directory.
- Detects file encoding (uses `chardet` if installed) and tries common delimiters (`,`, `;`, tab, `|`).
- Cleans each file:
  - Normalizes column names (lowercase, trimmed, snake_case-like)
  - Drops fully empty rows/columns
  - Trims whitespace in text columns
  - Converts common “fake nulls” (e.g., `N/A`, `null`, `-`) to real nulls
  - Removes duplicate rows within each file
  - Converts numeric-looking text columns to numeric
  - Parses likely date columns based on column name hints
- Transforms to a canonical schema:
  - Renames known column aliases to standardized column names
  - Normalizes fields like `gender`, `country`, and `email`
  - Adds `_source` to track which input file each row came from
  - Converts datetime values to ISO-like strings for JSON output
- Merges all files into one master dataset:
  - Ensures duplicate column names are suffixed so concatenation works
  - Optionally deduplicates across files using `email` and/or `id` (when present)
- Writes two outputs:
  - `master_output.json` (final merged records)
  - `master_output.validation.json` (data quality summary + warnings)

## How We Achieve This

The pipeline is implemented in [csv_pipeline.py](csv_pipeline.py):

1. **Ingestion**: `load_csv()` detects encoding and delimiter, then loads each CSV into a DataFrame.
2. **Cleaning**: `clean()` standardizes column names, trims values, replaces null placeholders, drops empties, deduplicates, and performs basic type inference.
3. **Transformation**: `transform()` maps known aliases to canonical fields and normalizes common fields (email/gender/country).
4. **Merge**: `merge_frames()` concatenates all transformed DataFrames and removes cross-file duplicates.
5. **Validation**: `build_validation_report()` calculates null counts/percentages and generates warnings for columns with high null rates.
6. **Export**: `write_json()` outputs the consolidated dataset as JSON.

## Project Structure

- [csv_pipeline.py](csv_pipeline.py): Main CSV → JSON pipeline.
- [generate_demo_csvs.py](generate_demo_csvs.py): Generates realistic-but-messy demo CSVs for testing.
- `data/`: Example input CSV files.
- `master_output.json`: Example output JSON (already generated).
- `master_output.validation.json`: Example validation report (already generated).

## Requirements

- Python 3.x
- Packages:
  - `pandas`
  - `numpy`
  - `chardet` (optional but recommended for better encoding detection)

Install dependencies:

```bash
pip install pandas numpy chardet
```

## Usage

Generate demo CSVs (optional):

```bash
python generate_demo_csvs.py
```

Run the pipeline:

```bash
python csv_pipeline.py --input ./data --output master_output.json
```

### Command-line Arguments

- `--input`: Folder containing the CSV files to process (pipeline reads `*.csv`).
- `--output`: Output JSON filename (a validation file is generated alongside it as `*.validation.json`).

## Outputs

- **Merged JSON**: A list of records written to the output file (default: `master_output.json`).
- **Validation report**: A JSON report written next to the output file (example: `master_output.validation.json`) containing:
  - row/column counts
  - list of columns
  - null counts and percentages per column
  - per-source row counts (`_source`)
  - warnings for columns with high null percentages

