"""
run_pipeline_cli.py
End-to-end, no-UI run of the whole pipeline: parse -> evidence matrix ->
verification report -> fact-pack checks -> a couple of demo Q&A calls.

Usage:  python run_pipeline_cli.py   (run from inside the 'pipeline' folder)
"""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))

print("STEP 1/4 — Parsing interviews into a structured, traceable corpus\n" + "-"*60)
r1 = subprocess.run([sys.executable, os.path.join(HERE, "parse_interviews.py")])
if r1.returncode != 0:
    sys.exit(r1.returncode)

print("\nSTEP 2/4 — Building evidence matrix + verbatim verification report\n" + "-"*60)
r2 = subprocess.run([sys.executable, os.path.join(HERE, "verify_quotes.py")])
if r2.returncode != 0:
    sys.exit(r2.returncode)

print("\nSTEP 3/4 — Fact-pack checks (median reconciliation + outliers)\n" + "-"*60)
r3 = subprocess.run([sys.executable, os.path.join(HERE, "factpack.py")])
if r3.returncode != 0:
    sys.exit(r3.returncode)

print("\nSTEP 4/4 — Grounded Q&A demo\n" + "-"*60)
sys.path.insert(0, HERE)
from qa_engine import GroundedQA
qa = GroundedQA()
demo_qs = [
    "What did the CEO say about the org structure relying on one person at the top?",
    "Did the incumbent change vendor conclude anything about org structure?",
]
for q in demo_qs:
    print(f"\nQ: {q}")
    r = qa.answer(q)
    if not r["answer_found"]:
        print(f"  -> Not in the interviews. (top match score {r['top_score']})")
    else:
        for m in r["matches"]:
            print(f"  -> [{m['speaker']} | {m['file']}] {m['text']}")
