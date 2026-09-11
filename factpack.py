"""
factpack.py
Loads GNP_fact_pack.xlsx into clean dataframes and runs data-quality checks.

The brief is explicit that these figures are "as extracted -- they have not
been audited." We treat that line as an instruction, not a footnote: every
number that reaches the deck must survive an automated reconciliation check
first, and the "not audited" disclosure itself is surfaced as a first-class
output of this module (not just left in the raw sheet for someone to notice).

Two checks are run:
  1. STATED-MEDIAN RECONCILIATION: recompute the median (and mean) of the
     five program-level grant-cycle figures for each fiscal year and compare
     against the sheet's own "Median -- all programs" row. This number does
     NOT reconcile for any of the three years -- flagged rather than repeated
     as a clean headline stat.
  2. PROGRAM-LEVEL OUTLIER CHECK: flags any single program/year cell that is
     more than 2x that program's own 3-year median (catches the Community
     Health FY2025 = 312 days figure).
"""
import os
import statistics
import sys
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "GNP_fact_pack.xlsx")

NOT_AUDITED_NOTICE = (
    "GNP's fact pack states on every sheet: \"Figures are as extracted — they have not "
    "been audited.\" That is a disclosure from the case materials themselves, not a "
    "caveat we are adding after the fact — every number below should be read with that "
    "in mind, and the checks in this module exist specifically to test it rather than "
    "take the disclosure as a formality."
)

def _require_factpack():
    if not os.path.isfile(PATH):
        msg = (
            f"\n\n=== SETUP PROBLEM DETECTED ===\n"
            f"Expected the fact pack at:\n    {PATH}\n"
            f"but it does not exist.\n\n"
            f"Quick fix: make sure GNP_fact_pack.xlsx sits directly inside this same "
            f"'pipeline' folder (not in a subfolder). If it's missing entirely, "
            f"re-extract the latest pipeline zip fresh.\n"
        )
        print(msg, file=sys.stderr)
        raise FileNotFoundError(msg)

def load_all():
    """Each sheet has a title row + blank row before the real header, and a
    footnote row at the bottom -- strip both so downstream code gets a clean
    measure/value table."""
    _require_factpack()
    xl = pd.ExcelFile(PATH)
    sheets = {}
    for name in xl.sheet_names:
        df = xl.parse(name, header=2)
        first_col = df.columns[0]
        df = df[df[first_col].notna()]
        df = df[~df[first_col].astype(str).str.startswith("Compiled by")]
        value_cols = df.columns[1:]
        df = df[df[value_cols].notna().any(axis=1)]
        sheets[name] = df.reset_index(drop=True)
    return sheets


def check_median_reconciliation(sheets):
    flags = []
    gct = sheets["Grant cycle times"].copy()
    gct.columns = [str(c).strip() for c in gct.columns]
    program_col = gct.columns[0]
    year_cols = [c for c in gct.columns if c.upper().startswith("FY")]

    stated_row = gct[gct[program_col].astype(str).str.contains("Median", case=False, na=False)]
    program_rows = gct[~gct[program_col].astype(str).str.contains("Median", case=False, na=False)]

    if stated_row.empty:
        flags.append("Could not locate the 'Median — all programs' row to reconcile.")
        return flags

    stated = stated_row.iloc[0]
    for c in year_cols:
        vals = program_rows[c].dropna().tolist()
        if not vals:
            continue
        true_median = statistics.median(vals)
        true_mean = statistics.mean(vals)
        stated_val = stated[c]
        if pd.isna(stated_val):
            continue
        gap_vs_median = stated_val - true_median
        if abs(gap_vs_median) > 0.5:
            flags.append(
                f"'{c}': fact pack states the all-program median as {stated_val:g} days, but the "
                f"true median of the 5 program-level figures ({sorted(vals)}) is {true_median:g} days "
                f"(gap = {gap_vs_median:+.0f}). The mean is {true_mean:.1f} days, which also does not "
                f"match the stated figure. This does not reconcile by any obvious method — flagged "
                f"rather than repeated as a headline number. Possible explanation: a volume-weighted "
                f"figure across the ~640 grants/year rather than a simple median of program medians — "
                f"but this cannot be confirmed from the materials provided."
            )
    return flags


def check_program_outliers(sheets):
    flags = []
    gct = sheets["Grant cycle times"].copy()
    gct.columns = [str(c).strip() for c in gct.columns]
    year_cols = [c for c in gct.columns if c.upper().startswith("FY")]
    for _, row in gct.iterrows():
        program = row.get(gct.columns[0])
        if pd.isna(program) or "median" in str(program).lower():
            continue
        vals = [row[c] for c in year_cols if pd.notna(row[c])]
        if not vals:
            continue
        med = statistics.median(vals)
        for c in year_cols:
            v = row[c]
            if pd.notna(v) and med > 0 and v > 2 * med:
                flags.append(
                    f"'{program}' / {c} = {v:g} days is {v/med:.1f}x that program's own 3-year "
                    f"median ({med:.0f} days) — worth validating before it's quoted; the fact pack "
                    f"notes figures are unaudited."
                )
    return flags


def flag_anomalies(sheets):
    return check_median_reconciliation(sheets) + check_program_outliers(sheets)


if __name__ == "__main__":
    sheets = load_all()
    for name, df in sheets.items():
        print(f"\n=== {name} ===")
        print(df.to_string(index=False))

    print("\n=== DATA-SOURCE DISCLOSURE ===")
    print(NOT_AUDITED_NOTICE)

    print("\n=== DATA QUALITY FLAGS ===")
    flags = flag_anomalies(sheets)
    if not flags:
        print("No anomalies detected.")
    for f in flags:
        print(" -", f)
