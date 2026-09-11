"""
GNP Foundation — Case-for-Change Evidence Pipeline
Streamlit app. Run with:  streamlit run app.py
(Run it from *inside* the 'pipeline' folder — the one that directly contains
this file, the .py modules, GNP_fact_pack.xlsx, and the interviews/ subfolder.)

Four tabs, matching the four things the brief asks the pipeline to prove:
  1. Evidence Matrix   -- theme -> verbatim quotes + fact-pack support
  2. Verification       -- programmatic proof every quote is word-for-word
  3. Ask a Question      -- grounded retrieval Q&A, refuses when ungrounded
  4. Fact Pack           -- the raw numbers, data-quality flags, and the
                            "not audited" disclosure surfaced up front

VERSION MARKER: v3 (2026-09-10)
"""
import os
import re
import traceback

import streamlit as st
import pandas as pd

st.set_page_config(page_title="GNP Case-for-Change Evidence Pipeline", layout="wide")

HERE = os.path.dirname(os.path.abspath(__file__))

def _setup_error(details: str):
    st.error(
        "**Setup problem — the app can't find its data files.**\n\n"
        + details
        + "\n\n**Quick fix:**\n"
        "1. Delete your existing local `pipeline` folder entirely (this avoids mixing "
        "files from an older download with a newer one).\n"
        "2. Re-download and re-extract the latest pipeline zip fresh.\n"
        "3. `cd` into the extracted `pipeline` folder in a terminal.\n"
        "4. Confirm the files are there: `ls interviews` should list 5 `.txt` files, "
        "and `ls GNP_fact_pack.xlsx` should find the spreadsheet.\n"
        "5. Re-run from that folder: `streamlit run app.py`\n"
    )
    st.stop()

_interviews_dir = os.path.join(HERE, "interviews")
_factpack_path = os.path.join(HERE, "GNP_fact_pack.xlsx")

if not os.path.isdir(_interviews_dir):
    _setup_error(f"Expected an `interviews` folder at:\n\n`{_interviews_dir}`\n\nbut it does not exist.")

_expected_files = [
    "interview_1_President_and_CEO.txt",
    "interview_2_Chief_Operating_Officer.txt",
    "interview_3_Head_of_Learning.txt",
    "interview_4_Head_of_Org_Effectiveness.txt",
    "interview_5_Project_Manager.txt",
]
_missing = [f for f in _expected_files if not os.path.isfile(os.path.join(_interviews_dir, f))]
if _missing:
    _setup_error(
        f"The `interviews` folder exists at `{_interviews_dir}` but is missing:\n\n"
        + "\n".join(f"- `{m}`" for m in _missing)
    )

if not os.path.isfile(_factpack_path):
    _setup_error(f"Expected the fact pack at:\n\n`{_factpack_path}`\n\nbut it does not exist.")

try:
    from evidence_matrix import THEMES
    from verify_quotes import ground_truth_quotes, verify_matrix
    from qa_engine import GroundedQA
    from factpack import load_all, flag_anomalies, NOT_AUDITED_NOTICE
except Exception as e:
    st.error(
        "**Something went wrong loading the pipeline modules.**\n\n"
        f"Error: `{e}`\n\n"
        "Make sure you ran `pip install -r requirements.txt` in this same folder, "
        "then restart with `streamlit run app.py`. If the error mentions `corpus.json` "
        "specifically, delete your local `pipeline` folder and re-extract the latest "
        "zip fresh — you are likely running a stale copy of `qa_engine.py`.\n\n"
        f"```\n{traceback.format_exc()}\n```"
    )
    st.stop()

st.title("GNP Foundation — Case-for-Change Evidence Pipeline")
st.caption(
    "Built for the ADAPTOVATE take-home case. Ingests the 5 interview files end-to-end, "
    "builds a themed evidence matrix, proves every quote against source, and answers "
    "questions only when the interviews actually support the answer."
)

tab1, tab2, tab3, tab4 = st.tabs(
    ["📋 Evidence Matrix", "✅ Verbatim Verification", "❓ Ask a Question", "📊 Fact Pack"]
)

# ---------------------------------------------------------------- TAB 1 ----
with tab1:
    st.subheader("Three case-for-change themes, with every supporting quote")
    for theme in THEMES:
        with st.container(border=True):
            st.markdown(f"### {theme['id']} — {theme['name']}")
            st.write(theme["one_liner"])

            st.markdown("**Verbatim quotes (interview evidence):**")
            for q in theme["quotes"]:
                st.markdown(f"> \u201c{q['quote']}\u201d")
                st.caption(f"— {q['speaker']}, `{q['file']}`")

            if theme.get("supporting_paraphrase"):
                st.markdown("**Supporting notes (paraphrase, not verbatim — labeled as such):**")
                for p in theme["supporting_paraphrase"]:
                    st.markdown(f"- {p['note']} — *{p['speaker']}, `{p['file']}`*")

            if theme.get("fact_pack"):
                st.markdown("**Fact-pack support:**")
                for f in theme["fact_pack"]:
                    st.markdown(f"- {f}")

    st.divider()
    st.subheader("Quotes found in source but not used in the top-3 themes")
    st.caption("Disclosed for transparency — nothing found in the interviews is hidden.")
    gt = ground_truth_quotes()
    _, used_norm = verify_matrix(THEMES)

    def _norm(s):
        return re.sub(r"\s+", " ", s).strip()

    unused = [g for g in gt if (g["file"], _norm(g["quote"])) not in {(f, _norm(q)) for f, q in used_norm}]
    for u in unused:
        st.markdown(f"- \u201c{u['quote']}\u201d — `{u['file']}`")

# ---------------------------------------------------------------- TAB 2 ----
with tab2:
    st.subheader("Automated verbatim-verification report")
    matrix_results, used_norm = verify_matrix(THEMES)
    n_gt = len(gt)
    n_mapped = len(matrix_results)
    n_verified = sum(r["verified"] for r in matrix_results)
    n_failed = n_mapped - n_verified

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Verbatim quotes found in source", n_gt)
    c2.metric("Quotes used in the 3 themes", n_mapped)
    c3.metric("Verified word-for-word", n_verified)
    c4.metric("Verification failures", n_failed, delta=None)

    st.markdown(
        f"**Result: {n_mapped} quotes extracted · {n_verified} verified word-for-word · "
        f"{n_failed} failures.**"
    )

    df = pd.DataFrame(matrix_results)[["theme", "speaker", "file", "quote", "verified"]]
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.info(
        "Note: `interview_4_Head_of_Org_Effectiveness.txt` contains **zero** quoted "
        "(verbatim) statements in the source — only paraphrase. No verbatim quote was "
        "fabricated for this speaker; their input appears only under 'supporting "
        "paraphrase' in the Evidence Matrix tab, clearly labeled as such."
    )

# ---------------------------------------------------------------- TAB 3 ----
with tab3:
    st.subheader("Ask the interviews a question")
    st.caption(
        "Retrieval-only grounded Q&A — no generation in the answer path. Every answer is a "
        "verbatim bullet traced to file, speaker and line number. Below a similarity/overlap "
        "threshold, it refuses rather than guesses."
    )
    qa = GroundedQA()

    example_qs = [
        "— choose an example —",
        "What did the CEO say about the org structure relying on one person at the top?",
        "Did the incumbent change vendor conclude anything about org structure?",
        "Why did the peer mentoring program fail to launch?",
        "Is there a risk staff see this as the CEO's flavor of the year?",
        "What is GNP's annual operating budget?",
    ]
    choice = st.selectbox("Try an example, or type your own below:", example_qs)
    default_q = "" if choice == example_qs[0] else choice
    question = st.text_input("Your question:", value=default_q)

    if question:
        result = qa.answer(question)
        if not result["answer_found"]:
            st.error(f"**Not in the interviews.** (best match score: {result['top_score']})")
        else:
            st.success("Grounded in the interviews:")
            for m in result["matches"]:
                st.markdown(f"> {m['text']}")
                st.caption(
                    f"— {m['speaker']}, `{m['file']}`, line {m['line_no']} "
                    f"(section: {m['section']}, match score {m['score']})"
                )

# ---------------------------------------------------------------- TAB 4 ----
with tab4:
    st.subheader("Fact pack — as extracted")
    st.warning(NOT_AUDITED_NOTICE)

    sheets = load_all()
    for name, df in sheets.items():
        st.markdown(f"**{name}**")
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Automated data-quality flags")
    flags = flag_anomalies(sheets)
    if flags:
        for f in flags:
            st.error(f)
    else:
        st.write("No anomalies detected by the automated check.")
