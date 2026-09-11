"""
qa_engine.py
Grounded Q&A over the interview corpus -- retrieval only, no generation.
Deliberately simple: TF-IDF over the bullet-level corpus + cosine similarity,
gated by a minimum informative-word overlap. No LLM call in the answer path,
so there is nothing for a model to "hallucinate" -- every answer is a
verbatim bullet (and, where one exists, the exact quoted sentence inside it)
traced to its file, speaker and line number. Below a similarity/overlap
threshold, the engine refuses to answer rather than guess.

VERSION MARKER: v3 (2026-09-10)

ROBUSTNESS NOTE (important): this module does NOT require corpus.json to
already exist, and does NOT require parse_interviews.py or run_pipeline_cli.py
to have been run first. `streamlit run app.py` works standalone, cold, on a
fresh checkout -- load_corpus() below uses try/except (not just an isfile
pre-check) around the file read, so there is no path where a missing
corpus.json produces a raw FileNotFoundError. If you see a FileNotFoundError
mentioning corpus.json, you are running an OLD copy of this file -- delete
your local pipeline folder entirely and re-extract the latest zip fresh.
"""
import json, os, re, sys

from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.metrics.pairwise import cosine_similarity

try:
    from nltk.stem import PorterStemmer
    _stemmer = PorterStemmer()
except Exception:
    _stemmer = None  # graceful fallback: no stemming, still works, just less fuzzy matching

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS_PATH = os.path.join(HERE, "corpus.json")

THRESHOLD = 0.20
MIN_OVERLAP = 2
TOP_K = 3

DOMAIN_STOPWORDS = {"gnp", "foundation", "org", "organization", "team", "teams"}
STOPWORDS = list(ENGLISH_STOP_WORDS.union(DOMAIN_STOPWORDS))

def _stem(w):
    return _stemmer.stem(w) if _stemmer else w

def tokenize(text):
    words = set(re.findall(r"[a-z']+", text.lower())) - set(STOPWORDS)
    return {_stem(w) for w in words}

def load_corpus():
    """Bulletproof loader: try reading corpus.json; on ANY failure (missing,
    corrupt, stale), fall back to building it fresh from the interview files
    directly. This function is designed to never raise FileNotFoundError."""
    try:
        with open(CORPUS_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass  # fall through to rebuild

    # Rebuild directly -- no dependency on any prior CLI step having been run.
    sys.path.insert(0, HERE)
    import parse_interviews
    try:
        return parse_interviews.build_and_save_corpus()
    except Exception:
        # Even if writing corpus.json fails (e.g. read-only folder), still
        # return the in-memory corpus so the app can run.
        return parse_interviews.build_corpus()

class GroundedQA:
    def __init__(self):
        self.corpus = load_corpus()
        self.texts = [r["text"] for r in self.corpus]
        self.token_sets = [tokenize(t) for t in self.texts]
        self.vectorizer = TfidfVectorizer(stop_words=STOPWORDS, ngram_range=(1, 2), min_df=1)
        self.matrix = self.vectorizer.fit_transform(self.texts)

    def answer(self, question: str):
        q_tokens = tokenize(question)
        q_vec = self.vectorizer.transform([question])
        sims = cosine_similarity(q_vec, self.matrix)[0]

        for i, toks in enumerate(self.token_sets):
            if len(q_tokens & toks) < MIN_OVERLAP:
                sims[i] = 0.0

        ranked = sims.argsort()[::-1][:TOP_K]
        top_score = sims[ranked[0]] if len(ranked) else 0.0

        if top_score < THRESHOLD:
            return {
                "answer_found": False,
                "message": "Not in the interviews.",
                "top_score": round(float(top_score), 3),
                "matches": [],
            }

        matches = []
        for idx in ranked:
            if sims[idx] < THRESHOLD:
                continue
            rec = self.corpus[idx]
            matches.append({
                "score": round(float(sims[idx]), 3),
                "speaker": rec["speaker"],
                "file": rec["file"],
                "section": rec["section"],
                "line_no": rec["line_no"],
                "text": rec["text"],
                "verbatim_quotes": rec["verbatim_quotes"],
            })
        return {"answer_found": True, "message": None, "top_score": round(float(top_score), 3), "matches": matches}


if __name__ == "__main__":
    qa = GroundedQA()
    test_questions = [
        "What did the CEO say about decision-making and hierarchy?",
        "Why is the grantee satisfaction score declining?",
        "What is GNP's annual operating budget?",
        "What did the incumbent change vendor conclude about org structure?",
        "How do staff feel about past change efforts?",
        "What is GNP's stock price?",
    ]
    for q in test_questions:
        print(f"\nQ: {q}")
        r = qa.answer(q)
        if not r["answer_found"]:
            print(f"  -> {r['message']}  (top_score={r['top_score']})")
        else:
            for m in r["matches"]:
                tag = f"[{m['speaker']} | {m['file']} | line {m['line_no']} | score {m['score']}]"
                print(f"  -> {tag}\n     {m['text']}")
