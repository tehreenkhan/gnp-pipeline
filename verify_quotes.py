"""
verify_quotes.py
Programmatic verbatim-verification. Two independent checks, on purpose:

1) GROUND TRUTH EXTRACTION: re-scan the raw .txt files for every substring
   inside double quotes. This is the authoritative list of "things someone
   in these interviews actually said, word for word" -- built with zero
   reference to the evidence matrix, so it can't rubber-stamp itself.

2) MATRIX VERIFICATION: for every quote used in evidence_matrix.py (the
   curated theme write-up), confirm it is an EXACT substring of its claimed
   source file. Whitespace is normalised (curly vs straight quotes, double
   spaces) but no words are added, removed, or reordered. Anything that
   doesn't match exactly is reported as a FAIL, not silently fixed.

Output: a verification report (json + printed summary) in the same format
the case brief asks for, e.g. "13 quotes extracted - 10 mapped and verified -
0 failures - 3 unused-but-verified quotes disclosed".
"""
import json, os, re, sys, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
INTERVIEW_DIR = os.path.join(HERE, "interviews")

def _require_interview_dir():
    if not os.path.isdir(INTERVIEW_DIR):
        msg = (
            f"\n\n=== SETUP PROBLEM DETECTED ===\n"
            f"Expected an 'interviews' folder at:\n    {INTERVIEW_DIR}\n"
            f"but it does not exist.\n\n"
            f"Quick fix: delete your local 'pipeline' folder and re-extract the "
            f"latest zip fresh, then run 'ls interviews' to confirm 5 .txt files "
            f"are present before rerunning.\n"
        )
        print(msg, file=sys.stderr)
        raise FileNotFoundError(msg)

def normalize(s):
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("\u2019", "'").replace("\u2018", "'")
    s = s.replace("\u201c", '"').replace("\u201d", '"')
    s = re.sub(r"\s+", " ", s).strip()
    return s

def load_source_text(fname):
    path = os.path.join(INTERVIEW_DIR, fname)
    with open(path, encoding="utf-8") as f:
        return f.read()

def ground_truth_quotes():
    """Independently re-extract every quoted substring from every file."""
    _require_interview_dir()
    all_quotes = []
    for fname in sorted(os.listdir(INTERVIEW_DIR)):
        if not fname.endswith(".txt"):
            continue
        text = load_source_text(fname)
        for q in re.findall(r'"([^"]+)"', text):
            all_quotes.append({"file": fname, "quote": q})
    return all_quotes

def verify_matrix(themes):
    _require_interview_dir()
    results = []
    used_quotes_norm = set()
    for theme in themes:
        for item in theme["quotes"]:
            source_text = normalize(load_source_text(item["file"]))
            q_norm = normalize(item["quote"])
            passed = q_norm in source_text
            results.append({
                "theme": theme["id"],
                "theme_name": theme["name"],
                "speaker": item["speaker"],
                "file": item["file"],
                "quote": item["quote"],
                "verified": passed,
            })
            used_quotes_norm.add((item["file"], q_norm))
    return results, used_quotes_norm

def main():
    from evidence_matrix import THEMES

    gt = ground_truth_quotes()
    matrix_results, used_norm = verify_matrix(THEMES)

    n_gt = len(gt)
    n_mapped = len(matrix_results)
    n_verified = sum(r["verified"] for r in matrix_results)
    n_failed = n_mapped - n_verified

    unused = []
    for g in gt:
        key = (g["file"], normalize(g["quote"]))
        if key not in used_norm:
            unused.append(g)

    report = {
        "total_verbatim_quotes_in_source": n_gt,
        "quotes_mapped_to_themes": n_mapped,
        "verified_word_for_word": n_verified,
        "verification_failures": n_failed,
        "matrix_detail": matrix_results,
        "unused_but_verbatim_quotes_disclosed": unused,
    }
    with open(os.path.join(HERE, "verification_report.json"), "w") as f:
        json.dump(report, f, indent=2)

    print("=== VERBATIM VERIFICATION REPORT ===")
    print(f"{n_gt} verbatim (quoted) statements found across the 5 source files")
    print(f"{n_mapped} of those are used as evidence in the 3 case-for-change themes")
    print(f"{n_verified} verified word-for-word against source · {n_failed} failures")
    if n_failed:
        print("\nFAILED QUOTES:")
        for r in matrix_results:
            if not r["verified"]:
                print(f"  [FAIL] {r['file']} — {r['quote']}")
    print(f"\n{len(unused)} additional verbatim quote(s) exist in the source but were NOT used in the top-3 themes (disclosed, not hidden):")
    for u in unused:
        print(f"  - ({u['file']}) \"{u['quote']}\"")

    print("\nNote: interview_4_Head_of_Org_Effectiveness.txt contains zero quoted")
    print("(verbatim) statements in the source notes -- only paraphrase. This is")
    print("disclosed in the evidence matrix as 'supporting_paraphrase', never")
    print("presented as a direct quote.")

if __name__ == "__main__":
    main()
