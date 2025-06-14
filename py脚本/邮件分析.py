import pandas as pd

# --- ⚙️ Configuration ---
# You can easily change your settings here
INPUT_FILE = "1.xlsx"
OUTPUT_FILE = "merged_output.xlsx"
# To merge the first 5 columns, set to: df.columns[:5]
# To merge specific columns by name, set to: ['ColumnName1', 'ColumnName2']
COLUMNS_TO_MERGE = None  # If None, it will default to the first 5 columns
NEW_COLUMN_NAME = '合并结果'
SEPARATOR = '-'

# --- 🚀 Main Script ---
print(f"🔄 Starting to process file: {INPUT_FILE}")

try:
    # 1. Read the Excel file
    df = pd.read_excel(INPUT_FILE, engine="openpyxl")
    print("✅ File read successfully.")

    # 2. Determine which columns to merge
    if COLUMNS_TO_MERGE is None:
        # Default to the first 5 columns if not specified
        merge_cols = df.columns[:5]
        print(f"ℹ️ No columns specified, defaulting to first 5: {list(merge_cols)}")
    else:
        merge_cols = COLUMNS_TO_MERGE
        print(f"ℹ️ Merging specified columns: {merge_cols}")

    # 3. Merge data using a high-performance vectorized method
    # This approach is significantly faster than using 'apply' row-by-row.

    # a. Stack the selected columns into a single series, which automatically drops empty (NaN) cells.
    stacked = df[merge_cols].stack()

    # b. Convert all values to strings and strip leading/trailing whitespace.
    stripped = stacked.astype(str).str.strip()

    # c. Filter out any remaining empty strings (e.g., cells that only contained spaces).
    non_empty = stripped[stripped != '']

    # d. Group by the original row index and join the values with the separator.
    merged_series = non_empty.groupby(level=0).agg(SEPARATOR.join)

    # 4. Add the merged result to a new column in the DataFrame
    df[NEW_COLUMN_NAME] = merged_series

    # For rows that had no data to merge, the result will be NaN. Fill these with an empty string.
    df[NEW_COLUMN_NAME].fillna('', inplace=True)
    print("✅ Data merged successfully.")

    # 5. Save the result to a new Excel file
    df.to_excel(OUTPUT_FILE, index=False)
    print(f"🎉 Process complete! Output saved to: {OUTPUT_FILE}")

except FileNotFoundError:
    print(f"❌ ERROR: Input file not found at '{INPUT_FILE}'")
except KeyError:
    print(f"❌ ERROR: One or more specified columns not found in the file. Please check COLUMNS_TO_MERGE.")
except Exception as e:
    print(f"❌ An unexpected error occurred: {e}")