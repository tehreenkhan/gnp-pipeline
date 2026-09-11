# GNP Foundation — Case-for-Change Evidence Pipeline

**How to run it (one line, from inside this folder):**
```
pip install -r requirements.txt && streamlit run app.py
```
Then open the local URL Streamlit prints (default `http://localhost:8501`).

No API keys, no paid services. Everything — parsing, theming, quote
verification, fact-pack checks, and Q&A — runs locally and deterministically,
and works cold: you do NOT need to run any other script first. `streamlit
run app.py` alone builds everything it needs on first launch.

**Command-line version (no browser needed), to sanity-check it runs end to end:**
```
python run_pipeline_cli.py
```

## What's in this folder

| File | Purpose |
|---|---|
| `interviews/*.txt` | The 5 raw interview files (unmodified, as supplied). |
| `parse_interviews.py` | Parses every bullet into a structured record: `{file, speaker, section, line_no, text, verbatim_quotes}`. Exposes `build_and_save_corpus()`, which both the CLI and the Q&A engine's fallback call. |
| `evidence_matrix.py` | The curated theme → quote mapping. Every quote here is checked, not trusted, by `verify_quotes.py`. |
| `verify_quotes.py` | Independently re-extracts every quoted string from the raw files (ground truth), then checks every quote used in the evidence matrix is an exact substring of its claimed source. |
| `factpack.py` | Loads `GNP_fact_pack.xlsx` and runs two checks: (1) the sheet's stated "Median — all programs" row does not reconcile with the true median/mean of its own five program-level figures, in any of the three fiscal years — flagged, not repeated as a headline stat; (2) flags the Community Health FY2025 = 312-day outlier (3.1x that program's own 3-year median). Surfaces the fact pack's own "not audited" disclosure prominently. |
| `qa_engine.py` | Grounded Q&A (TF-IDF + word-overlap gate, no LLM in the answer path). **`load_corpus()` uses try/except, not just a file-existence check** — if `corpus.json` is missing, corrupted, or stale, it transparently rebuilds the corpus in memory from the interview files and re-saves it. This is what makes `streamlit run app.py` work as the very first command you run, with no setup step in between. |
| `app.py` | The Streamlit UI — four tabs. Checks for `interviews/` and `GNP_fact_pack.xlsx` on startup and shows an in-app fix-it message (not a raw traceback) if either is missing. |
| `run_pipeline_cli.py` | Runs the whole pipeline end-to-end from the terminal, no UI. |

## Design choices worth knowing about

- **Verification is a second, independent extraction, not a checklist.**
- **The fact pack's "not audited" disclosure is treated as an instruction, not a formality** — two reconciliation checks exist specifically because of that line.
- **Retrieval, not generation, answers questions** — No generative answer synthesis in the answer path; responses are returned from source-grounded records.
- **Interview 4 (Head of Org Effectiveness) has zero quoted statements in the source** — no fabricated quote fills that gap.
- **Every module resolves paths relative to its own file location**, and `qa_engine.py` specifically never depends on a prior script having been run — it is self-sufficient by design.
