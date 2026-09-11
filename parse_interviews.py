"""
parse_interviews.py
Parses the five raw GNP interview .txt files into a structured, line-addressable
corpus: one record per bullet, tagged with speaker, source file, section heading,
and line number. This structured corpus is the single source of truth used by
both the evidence matrix builder and the Q&A engine -- nothing downstream is
allowed to reference text that isn't traceable back to one of these records.

VERSION MARKER: v3 (2026-09-10) -- includes environment self-check and is the
version qa_engine.py's fallback calls if corpus.json is missing.
"""
import os, re, json, sys

HERE = os.path.dirname(os.path.abspath(__file__))
INTERVIEW_DIR = os.path.join(HERE, "interviews")

FILES = [
    ("interview_1_President_and_CEO.txt", "President & CEO"),
    ("interview_2_Chief_Operating_Officer.txt", "Chief Operating Officer"),
    ("interview_3_Head_of_Learning.txt", "Head of Learning"),
    ("interview_4_Head_of_Org_Effectiveness.txt", "Head of Org Effectiveness"),
    ("interview_5_Project_Manager.txt", "Project Manager"),
]

def check_environment():
    """Fail loudly, with a plain-English fix, instead of a raw traceback."""
    problems = []
    if not os.path.isdir(INTERVIEW_DIR):
        problems.append(
            f"Expected an 'interviews' folder at:\n    {INTERVIEW_DIR}\n"
            f"but it does not exist."
        )
    else:
        missing = [f for f, _ in FILES if not os.path.isfile(os.path.join(INTERVIEW_DIR, f))]
        if missing:
            problems.append(
                "The 'interviews' folder exists but is missing these expected files:\n    "
                + "\n    ".join(missing)
                + f"\n(Looked in: {INTERVIEW_DIR})"
            )
    if problems:
        msg = (
            "\n\n=== SETUP PROBLEM DETECTED ===\n"
            + "\n\n".join(problems)
            + "\n\nQuick fix:\n"
            "  1) Delete your existing local 'pipeline' folder entirely (to avoid mixing "
            "old and new files from different downloads).\n"
            "  2) Re-download and re-extract the latest pipeline zip fresh.\n"
            "  3) cd into the extracted 'pipeline' folder.\n"
            "  4) Run: ls interviews    -- you should see 5 .txt files listed.\n"
            "  5) Then run: streamlit run app.py\n"
        )
        print(msg, file=sys.stderr)
        raise FileNotFoundError(msg)

def parse_file(fname, speaker):
    path = os.path.join(INTERVIEW_DIR, fname)
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    records = []
    section = None
    for i, raw in enumerate(lines, start=1):
        line = raw.rstrip("\n")
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- "):
            bullet = stripped[2:].strip()
            quotes = re.findall(r'"([^"]+)"', bullet)
            records.append({
                "file": fname,
                "speaker": speaker,
                "section": section,
                "line_no": i,
                "text": bullet,
                "has_verbatim_quote": len(quotes) > 0,
                "verbatim_quotes": quotes,
            })
        elif stripped.isupper() or "|" in stripped:
            if "|" in stripped:
                continue  # title line, not a section
            section = stripped
    return records

def build_corpus():
    check_environment()
    corpus = []
    for fname, speaker in FILES:
        corpus.extend(parse_file(fname, speaker))
    return corpus

def build_and_save_corpus():
    """Build the corpus and persist it to corpus.json. Used both by the CLI
    entry point and by qa_engine.py's fallback so the file exists for next time."""
    corpus = build_corpus()
    out_path = os.path.join(HERE, "corpus.json")
    with open(out_path, "w") as f:
        json.dump(corpus, f, indent=2)
    return corpus

if __name__ == "__main__":
    corpus = build_and_save_corpus()
    print(f"Parsed {len(corpus)} bullet-level notes across {len(FILES)} files.")
    n_quotes = sum(len(r['verbatim_quotes']) for r in corpus)
    print(f"Found {n_quotes} verbatim (quoted) statements embedded in those notes.")
    print(f"Wrote corpus.json to: {os.path.join(HERE, 'corpus.json')}")
