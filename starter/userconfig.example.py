"""
userconfig.example.py — WORKED EXAMPLE, product marketing. Fictional.
================================================================================
This is the companion to `career-profile.example.md`: same fictional person,
Johnny Fakeuser, a mid-career **product marketing manager** in Denver.

It exists to prove a claim the README makes and the template quietly undermines:
**nothing in the scoring engine is specific to data or technology roles.** Every
term the scorer matches on is read from this file. Point it at a different field
and it searches that field.

Read this next to `userconfig.template.py` and notice what changes:

  - LANE_STRONG / LANE_MED / LANE_ADJ are marketing vocabulary, not data
    vocabulary.
  - LEVEL_AT_OR_ABOVE is INVERTED relative to a director-level search. Johnny is
    an individual contributor reaching for Senior, so "lead" and "principal" are
    levels ABOVE him. In a director-level config those same words mean "below".
    The list is relative to YOUR target, not to some universal seniority ladder.
  - NOISE and OFF_CONTEXT are completely different, because they are the
    dangerous lists: they DROP roles silently. The template ships a data
    searcher's versions ("recruiter", "payroll", "nurse", "rfp"). Copy those
    unedited into a recruiting, payroll, nursing, or proposal-management search
    and the system will discard exactly the jobs you are looking for, without
    telling you.

To use this as your starting point instead of the blank template:

    cp starter/userconfig.example.py personal/userconfig.py

then replace every value with your own. Nothing here is a default worth keeping.
"""

# =============================================================================
# 1. WHO YOU ARE
# =============================================================================
NAME = "Johnny Fakeuser"
LEGAL_NAME = "Johnny Quincy Fakeuser"  # document metadata + background checks
EMAIL = "johnny@example.com"
PHONE = "555.555.5555"
LINKEDIN = "linkedin.com/in/yourprofile"
HOME_METRO = "Denver, CO"

# =============================================================================
# 2. TARGET TITLES  <- the single biggest lever on what the sweep finds
# =============================================================================
TARGET_TITLES = [
    "senior product marketing manager",
    "product marketing manager",
    "lead product marketing manager",
    "principal product marketing manager",
    "technical product marketing",
    "platform product marketing",
]

# =============================================================================
# 3. WHERE YOU'LL WORK
# =============================================================================
LOCATIONS = [
    (HOME_METRO, False),
    ("United States", True),  # remote
]
REMOTE_ONLY = False

# PLACES only. A work model ("remote", "hybrid") is NOT a location.
GEO_GOOD = ["denver", "boulder", "lakewood", "aurora", "colorado", "co"]
GEO_OK = ["colorado springs", "fort collins", "united states"]

GEO_REMOTE = ["remote", "anywhere", "nationwide", "remote us", "work from home"]

# Johnny will not relocate, so everywhere else is out. Without this, "Remote -
# Bangalore" scores exactly like a job in Denver.
GEO_EXCLUDE = [
    "india",
    "united kingdom",
    "canada",
    "ireland",
    "germany",
    "poland",
    "brazil",
    "mexico",
    "philippines",
    "singapore",
    "australia",
    "emea",
    "apac",
    "latam",
    "europe",
    "san francisco",
    "bay area",
    "california",
    "seattle",
    "new york",
    "austin",
    "chicago",
    "boston",
    "atlanta",
]

# =============================================================================
# 3b. WORK AUTHORIZATION  (captured at onboarding - OPTIONAL, opt-in)
# =============================================================================
# Filled in here to show the shape. It only ever FLAGS postings; it is never
# written into a resume or cover letter. See rule 1 in resume-style-rules.
WORK_AUTH = {
    "authorized_us": True,  # legally authorized to work in the US?
    "needs_sponsorship": False,  # will you need sponsorship now or in the future?
    "citizenship": "citizen",  # "citizen" | "permanent_resident" | "other"
}

# =============================================================================
# 4. YOUR LANE  (words that mean "this is my kind of role")
# =============================================================================
LANE_STRONG = [
    "product marketing",
    "pmm",
    "positioning",
    "messaging",
    "go to market",
    "gtm",
    "product launch",
    "competitive intelligence",
    "pricing and packaging",
]
LANE_MED = [
    "technical marketing",
    "solutions marketing",
    "content marketing",
    "portfolio marketing",
    "product management",
]
LANE_ADJ = ["sales enablement", "developer relations", "developer advocacy", "evangelism"]

# =============================================================================
# 5. YOUR LEVEL  (target level and up)
#     NOTE the inversion vs a director-level config: Johnny is an IC reaching for
#     Senior, so "lead" and "principal" sit ABOVE him, not below.
# =============================================================================
# Rather than hand-typing the two lists, you can name ONE rung and let the career
# ladder generate them — it knows both tracks, so it gets "principal" and "lead"
# right for your target instead of your guessing:
#     TARGET_LEVEL = "director"   # rung keys: engine/career_ladder.py
#     LEVEL_REACH = 2             # optional cap on how far above target to reach
#     LEVEL_AT_OR_ABOVE = []      # leave BOTH lists empty to use the ladder
# Preview exactly what you'd get, with ambiguity warnings:
#     python engine/career_ladder.py director 2
# An explicit list always wins — if you typed one, it is used as-is.
LEVEL_AT_OR_ABOVE = ["senior", "sr", "lead", "staff", "principal"]
LEVEL_BELOW = ["associate", "junior", "jr", "coordinator", "specialist", "assistant"]

# =============================================================================
# 6. DOMAIN BONUS (+1) - a tiebreaker, NEVER a gate.
# =============================================================================
DOMAIN_BONUS = [
    "b2b saas",
    "saas",
    "developer tools",
    "devtools",
    "infrastructure",
    "security",
    "api",
    "platform",
]

# =============================================================================
# 7. HARD GATES -> always Drop.  From the profile's own "what you are NOT".
# =============================================================================
HARD_GATES = [
    "paid media",
    "paid social",
    "media buying",
    "performance marketing",
    "direct to consumer",
    "dtc",
    "brand ambassador",
]

# =============================================================================
# 8. SOFT PENALTIES (-1) - adjacent lanes you'd consider but aren't your core.
# =============================================================================
PENALTY_LANES = {
    "demand gen / growth — adjacent, but not the lane you want to be hired into": [
        "demand generation",
        "demand gen",
        "growth marketing",
        "field marketing",
        "lifecycle marketing",
    ],
}

# =============================================================================
# 9. NOISE + OFF-CONTEXT -> always Drop
#     THE DANGEROUS LISTS. These discard roles silently, so they must describe
#     YOUR search. A recruiter would delete "recruiter" from any noise list; a
#     proposal manager would delete "rfp". Johnny's versions below are wrong for
#     almost everyone else — which is the entire point.
# =============================================================================
NOISE = ["account executive", "sales development", "sdr", "bdr", "cashier", "driver"]
OFF_CONTEXT = ["event marketing", "trade show", "brand ambassador", "market research analyst"]

# =============================================================================
# 10. TARGET COMPANIES - the highest-signal source you have. It compounds.
# =============================================================================
COMPANIES = [
    {"ats": "greenhouse", "slug": "example-devtools", "industry": "devtools", "status": "verify"},
    {"ats": "lever", "slug": "example-saas", "industry": "b2b saas", "status": "verify"},
    # ...add your targets here.
]

# =============================================================================
# 11. SWEEP SETTINGS
# =============================================================================
MAX_AGE_DAYS = 60
BOARD_HOURS_OLD = 168
RESULTS_PER_SEARCH = 25
WORKDAY_QUERIES = ["marketing", "product marketing"]

# =============================================================================
# 12. COMMUTE TIERS (dashboard commute chip) - relative to YOUR home metro.
# =============================================================================
COMMUTE_TIERS = [
    {"match": "denver|boulder|lakewood|aurora|\\bCO\\b", "label": "~local", "tier": "good"},
    {"match": "colorado springs", "label": "~1 hr", "tier": "ok"},
    {"match": "fort collins", "label": "~1.5 hr", "tier": "ok"},
]

# =============================================================================
# 13. CURRENT ROLE + COMPENSATION  (captured at onboarding)
# =============================================================================
CURRENT_ROLE = "Product Marketing Manager"
CURRENT_COMP = {"base": 110000, "bonus_pct": 8, "equity": "modest ISO grant, 4-yr vest"}
COMP_FLOOR = 115000  # below this, a lateral move isn't worth it
COMP_TARGET = [120000, 150000]  # target base range (plus bonus + equity)
COMP_HARD_FLOOR = 105000  # absolute no-go below this
COMP_NOTES = "Would flex toward the floor for a Senior title plus real pricing ownership."

# =============================================================================
# 14. COACH VOICE  (delivery only — the substance never changes)
# =============================================================================
COACH_VOICE = "supportive"
