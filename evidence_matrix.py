"""
evidence_matrix.py
AI-assisted evidence pipeline with human-curated thematic judgment and automated provenance/QA.
This is the ONLY place a human (or an LLM assisting the human) writes down which quotes support 
which theme. Every "quote" field here is checked programmatically by verify_quotes.py against the
raw interview files before it is allowed to reach the deck or the app -- if a
quote does not match character-for-character, the pipeline fails loudly rather
than silently trusting the write-up.

Distinguishing verbatim vs paraphrase, on purpose:
Interview 4 (Head of Org Effectiveness) contains no quotation marks anywhere in
the source file -- the notetaker recorded paraphrase only. We therefore do NOT
fabricate a verbatim quote for that speaker. Where their paraphrased note is
useful context, it is listed separately under "supporting_paraphrase" and
labeled as such, never mixed into the verified-quote count.
"""

THEMES = [
    {
        "id": "T1",
        "name": "Decision rights are stuck at the top",
        "one_liner": "Nearly everything of consequence still needs to move through the CEO / Executive Council, so ordinary approvals compete with strategic ones and both slow down.",
        "quotes": [
            {
                "speaker": "President & CEO",
                "file": "interview_1_President_and_CEO.txt",
                "quote": "Our current structure relies too much on 'one person at the top having the answer'",
            },
            {
                "speaker": "President & CEO",
                "file": "interview_1_President_and_CEO.txt",
                "quote": "I started 30 years ago as a controller, so a lot of the bureaucracy is my responsibility",
            },
            {
                "speaker": "Project Manager",
                "file": "interview_5_Project_Manager.txt",
                "quote": "Right now there's a lot of back and forth before we can make a decision, the Family Health Team would have to work with the Geography, would have to loop in their supervisors, grant management department, legal team for advice — lots of touchpoints across the organization",
            },
        ],
        "supporting_paraphrase": [
            {
                "speaker": "Chief Operating Officer",
                "file": "interview_2_Chief_Operating_Officer.txt",
                "note": "CEO often has to sign off on something that has already been approved (e.g. vendor contracts or vacation approvals shouldn't go up to the CEO)",
            },
            {
                "speaker": "Head of Learning",
                "file": "interview_3_Head_of_Learning.txt",
                "note": "Barriers include Decision Making (at the EC level)",
            },
        ],
        "fact_pack": [
            "Average approval signatures required for a grant over $100k: 7",
            "Average days a decision waits for executive sign-off: 19",
            "Decisions escalated to Executive Council that are deferred at least one meeting cycle: 34%",
            "Items reaching the CEO's desk per month, including routine approvals (vendor contracts, vacations): ~85",
            "Executive Council meets every 2 weeks; Board meets monthly",
        ],
    },
    {
        "id": "T2",
        "name": "One brand, several foundations on the ground",
        "one_liner": "Program silos mean grantees experience GNP as disconnected teams rather than one foundation, and satisfaction is falling every cycle.",
        "quotes": [
            {
                "speaker": "Chief Operating Officer",
                "file": "interview_2_Chief_Operating_Officer.txt",
                "quote": "Health would show up in New Mexico and Education would show up in NM. So there wasn't a unified GNP foundation to the community there, there were multiple GNP Foundations",
            },
            {
                "speaker": "Chief Operating Officer",
                "file": "interview_2_Chief_Operating_Officer.txt",
                "quote": "How do we show up to our grantees to drive systemic change?",
            },
            {
                "speaker": "President & CEO",
                "file": "interview_1_President_and_CEO.txt",
                "quote": "The Community team won't speak to the Early Childhood Education Team",
            },
            {
                "speaker": "Head of Learning",
                "file": "interview_3_Head_of_Learning.txt",
                "quote": "How does the Foundation show up in these communities?",
            },
            {
                "speaker": "Head of Learning",
                "file": "interview_3_Head_of_Learning.txt",
                "quote": "The focusing on one's own domain is well intentioned but not helpful to delivering effectively as an organization — the collaborative approach to the strategy papers demonstrated what can happen when people work across teams",
            },
        ],
        "supporting_paraphrase": [
            {
                "speaker": "Head of Org Effectiveness",
                "file": "interview_4_Head_of_Org_Effectiveness.txt",
                "note": "Grantee messages include: processes are too convoluted; hard to build relationships with the Foundation; Foundation doesn't understand the community or issue area in which I work; grant strategies aren't clear -- not consistent between teams",
            },
        ],
        "fact_pack": [
            "Grantee satisfaction (top-2-box): 61% (2022) -> 54% (2024) -> 48% (2026)",
            "Grantee 'easy to work with': 55% (2022) -> 47% (2024) -> 41% (2026)",
            "Grantee 'would recommend working with GNP': 58% (2022) -> 49% (2024) -> 44% (2026)",
            "5 of 5 program areas took longer to disburse funds in FY25 than FY23 (see fact-pack note on the 'Median -- all programs' row)",
        ],
    },
    {
        "id": "T3",
        "name": "The org has been burned by change before, and knows it",
        "one_liner": "Staff are exhausted by past change efforts and unclear communication, which is the single biggest threat to this transformation landing -- not the structure question itself.",
        "quotes": [
            {
                "speaker": "President & CEO",
                "file": "interview_1_President_and_CEO.txt",
                "quote": "As an organization we are very resistant to change — no one wants to change what they do or how they do it. Inertia is a dominating force and it takes a lot for us to break out of old ways of working",
            },
            {
                "speaker": "Project Manager",
                "file": "interview_5_Project_Manager.txt",
                "quote": "Pretty soon 50 people start hearing about this project and in lieu of any clear communications, the rumor mill starts",
            },
        ],
        "supporting_paraphrase": [
            {
                "speaker": "Head of Org Effectiveness",
                "file": "interview_4_Head_of_Org_Effectiveness.txt",
                "note": "Roadblocks include: perceived notion that this might be CEO's flavor of the year",
            },
            {
                "speaker": "Head of Learning",
                "file": "interview_3_Head_of_Learning.txt",
                "note": "People are scarred by the 'lean down' back in 2009-10; it's the change communication that really impairs effectiveness",
            },
            {
                "speaker": "Chief Operating Officer",
                "file": "interview_2_Chief_Operating_Officer.txt",
                "note": "Readiness is 'thirds' -- a third committed to the need for change, a third willing and open, a third resistors needing a lot of work",
            },
        ],
        "fact_pack": [
            "Employee engagement (favourable): 68% (2022) -> 63% (2024) -> 59% (2026)",
            "Staff 'decisions are made at the right level': 41% (2022) -> 36% (2024) -> 31% (2026)",
            "Staff 'I understand how my role fits GNP's strategy': 57% (2022) -> 52% (2024) -> 49% (2026)",
            "Voluntary turnover, trailing 12 months: 14%",
            "Program officers with tenure <= 5 years: 90%",
        ],
    },
]

if __name__ == "__main__":
    import json, os
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "evidence_matrix.json"), "w") as f:
        json.dump(THEMES, f, indent=2)
    n_quotes = sum(len(t["quotes"]) for t in THEMES)
    print(f"Evidence matrix built: {len(THEMES)} themes, {n_quotes} verbatim quotes tagged for verification.")
