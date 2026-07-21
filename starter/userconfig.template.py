"""
userconfig.template.py — TEMPLATE. Run `python setup.py` from the repo root and it
copies this to personal/userconfig.py for you; then edit your values below.
================================================================================
    (manual alternative: cp starter/userconfig.template.py personal/userconfig.py)

This is the ONE file you edit. All tools read these values through config.py (the
engine), which compiles the plain words below into matching rules and defines the
file paths. You never edit config.py. Your personal/ folder is gitignored, so your
real settings never enter the repo.

You write PLAIN WORDS here, not regex. config.terms_to_regex() compiles them.

>>> KNOWN LIMIT, READ THIS ONCE <<<
The triage scorer only ever sees a job's TITLE and LOCATION - never the JD body.
So HARD_GATES can only catch what's written in the title. Title-level gates are a
coarse first filter, NOT a safety net. The honest gate is the apply-pipeline score
in chat, which reads the whole JD.
"""

# =============================================================================
# 1. WHO YOU ARE
# =============================================================================
NAME = "Firstname Lastname"
LEGAL_NAME = "Firstname Lastname"  # document metadata + background checks
EMAIL = "you@example.com"
PHONE = "555.555.5555"
LINKEDIN = "linkedin.com/in/your-handle"
HOME_METRO = "Your City, ST"

# =============================================================================
# 2. TARGET TITLES  <- the single biggest lever on what the sweep finds
# =============================================================================
TARGET_TITLES = [
    "director data governance",
    "head of data",
    "director data platform",
    # ...list the exact titles you'd accept. Plain words, lowercase.
]

# =============================================================================
# 3. WHERE YOU'LL WORK
# =============================================================================
LOCATIONS = [
    (HOME_METRO, False),
    ("United States", True),  # remote
]
REMOTE_ONLY = False

# PLACES only. A work model ("remote", "hybrid") is NOT a location — keeping
# "hybrid" here would score "Hybrid - San Francisco Office" as commutable no
# matter where you live. Work-model words belong in GEO_REMOTE below.
GEO_GOOD = ["your city", "your state", "your metro suburbs"]
GEO_OK = ["a metro you'd commute to", "united states"]

# Work-model words. A remote role scores as home-range — but only when no
# GEO_EXCLUDE term also appears, since "Remote - India" is not remote to you.
GEO_REMOTE = ["remote", "anywhere", "nationwide", "remote us", "work from home"]

# Places you will NOT relocate to. Leave empty if you're open anywhere.
# List countries and metros; this is what stops off-geo roles scoring as Keep.
GEO_EXCLUDE = ["india", "united kingdom", "canada", "emea", "apac", "europe"]


# =============================================================================
# 3b. WORK AUTHORIZATION  (captured at onboarding - OPTIONAL, opt-in)
# =============================================================================
# The two questions application forms actually ask, plus the citizenship status
# that government postings turn on. Fill these in and the sweep will flag postings
# that state they do not sponsor, or that require U.S. citizenship.
#
# It FLAGS, it never drops - a misread here would bury a good role invisibly, so
# you always still see the posting, with the sentence that triggered the flag.
#
# SENSITIVE. Lives here in personal/ (gitignored) and is NEVER written into a
# resume or cover letter; see rule 1 in resume-style-rules. Volunteering status
# unprompted invites filtering before a human reads your record.
#
# Leave as None to switch the feature off entirely.
WORK_AUTH = None
# WORK_AUTH = {
#     "authorized_us": True,       # legally authorized to work in the US?
#     "needs_sponsorship": False,  # will you need sponsorship now or in the future?
#     "citizenship": "citizen",    # "citizen" | "permanent_resident" | "other"
# }

# =============================================================================
# 4. YOUR LANE  (words that mean "this is my kind of role")
# =============================================================================
LANE_STRONG = ["data governance", "data platform", "data strategy", "data enablement"]
LANE_MED = ["analytics", "business intelligence", "bi", "data", "insights", "reporting"]
LANE_ADJ = ["reliability", "platform", "architecture"]

# Optional: extra high-value terms for the resume-vs-JD keyword checker (ats_match.py).
# It ships with a data-leadership lexicon; add your field's terms here to extend it.
#   ATS_SKILL_LEXICON = {"kubernetes", "terraform", "spark", "kafka"}

# =============================================================================
# 5. YOUR LEVEL  (target level and up)
# =============================================================================
LEVEL_AT_OR_ABOVE = ["chief", "head of", "vice president", "vp", "avp", "director"]
LEVEL_BELOW = ["senior manager", "sr manager", "principal", "lead"]

# =============================================================================
# 6. DOMAIN BONUS (+1) - a tiebreaker, NEVER a gate.
# =============================================================================
DOMAIN_BONUS = ["your", "strongest", "industries"]

# =============================================================================
# 7. HARD GATES -> always Drop.  Write these HONESTLY: a gate you'd be lying to
#    clear saves you an application. Match how titles are actually written.
# =============================================================================
HARD_GATES = []

# =============================================================================
# 8. SOFT PENALTIES (-1) - adjacent lanes you'd consider but aren't your core.
# =============================================================================
PENALTY_LANES = {
    "example adjacent lane you'd consider but rank lower": ["some phrase", "another phrase"],
}

# =============================================================================
# 9. NOISE + OFF-CONTEXT -> always Drop  (obviously-wrong roles the boards surface)
# =============================================================================
NOISE = ["teacher", "nurse", "driver", "cashier", "recruiter", "payroll"]
OFF_CONTEXT = ["rfp", "corporate governance", "it governance", "cyber", "grc"]

# =============================================================================
# 10. TARGET COMPANIES - the highest-signal source you have. It compounds.
#     Resolve any company's ATS in 30 seconds by reading its careers URL:
#       job-boards.greenhouse.io/acme -> {"ats":"greenhouse","slug":"acme"}
#       jobs.lever.co/acme            -> {"ats":"lever","slug":"acme"}
#       jobs.ashbyhq.com/acme         -> {"ats":"ashby","slug":"acme"}
#       acme.wd1.myworkdayjobs.com/Careers ->
#           {"ats":"workday","tenant":"acme","wd":"wd1","site":"Careers"}
#     Wrong guesses 404 harmlessly - add speculatively.
# =============================================================================
COMPANIES = [
    {"ats": "greenhouse", "slug": "example-co", "industry": "example", "status": "verify"},
    # ...add your targets here.
]

# =============================================================================
# 11. SWEEP SETTINGS
# =============================================================================
MAX_AGE_DAYS = 60
BOARD_HOURS_OLD = 168
RESULTS_PER_SEARCH = 25
WORKDAY_QUERIES = ["data", "analytics"]

# =============================================================================
# 12. COMMUTE TIERS (dashboard commute chip) - relative to YOUR home metro.
#     The dashboard matches each role's location text against these in order,
#     first match wins. "match" is a regex (case-insensitive). tier "good" is
#     green, "ok" is amber. Remote is always good, Hybrid is ok (handled for you).
#     Example below is for someone based near a mid-size metro — edit to your own.
# =============================================================================
COMMUTE_TIERS = [
    {"match": "your city|your suburb|your state|\\bXX\\b", "label": "~local", "tier": "good"},
    {"match": "nearby big city", "label": "~1 hr", "tier": "ok"},
    {"match": "far big city", "label": "~2-3 hr", "tier": "ok"},
]

# =============================================================================
# 13. CURRENT ROLE + COMPENSATION  (captured at onboarding)
#     The negotiation skill reads your walk-away and target numbers from here; the
#     apply-pipeline/career-coach use them to flag step-downs and anchor the plan.
#     Your TARGET titles/lane/industry (sections 2, 4, 6) drive the sweep; these
#     anchor the money side. Fill them in honestly — all in annual base dollars.
# =============================================================================
CURRENT_ROLE = "Your Current Title"
CURRENT_COMP = {"base": 0, "bonus_pct": 0, "equity": ""}  # your current package
COMP_FLOOR = 0  # established-company floor — below this, a lateral isn't worth it
COMP_TARGET = [0, 0]  # target base range (plus bonus + equity)
COMP_HARD_FLOOR = 0  # absolute no-go below this
COMP_NOTES = ""  # any nuance (e.g., startup flex conditions, equity requirements)

# =============================================================================
# 14. COACH VOICE  (how the coaching sounds — see engine/coach-voice.md; delivery only)
#     "supportive" (default) · "tough-love" · "zen" · "humorous" · "analytical".
#     Pick what actually gets you moving. The Career Hub has a selector, or edit here.
# =============================================================================
COACH_VOICE = "supportive"
