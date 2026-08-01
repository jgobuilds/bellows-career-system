# Intake Artifact — Career Profile Collection

Optional reusable front door for Phase 1 collection. A single-page interactive artifact that gathers raw material and metric answers, then exports a structured `personal/career-profile.md` the user saves and reuses. The artifact organizes input; the structuring judgment still happens in the skill workflow.

## What it does
1. **Paste-in resumes** — one or more large text areas ("Paste every resume/CV you have — more is better"). Don't rely on file-upload/parsing inside the artifact.
2. **LinkedIn + extras** — optional areas for LinkedIn About/experience and brag-doc / review highlights.
3. **Snapshot fields** — name, current title/level, years, location, work authorization, links.
4. **Metric gaps** — after the user pastes material, surface `[NEED METRIC]` items as inline inputs so real numbers get filled in one place.
5. **Export** — a "Copy structured profile" button that emits clean Markdown matching `profile-schema.md`, which the user saves as `personal/career-profile.md`.

## Hard constraints
- **No browser storage** (localStorage/sessionStorage fail in artifacts). Keep state in React for the session; the user exports to persist.
- **No fabrication in the UI.** Metric fields are user-entered only. No "auto-embellish" or "add keywords" button — that would invite invention.
- **Single-file artifact.** Self-contained.
- The artifact gathers and structures; the nuanced work (theme tagging, inconsistency detection) is confirmed in the skill workflow.

## Brightside Data brand
Apply these standards (the profile is data/career work for this user):
- **Palette:** colorblind-friendly. Primary blues `#0072B2`, `#56B4E9`; accent oranges `#E69F00`, `#F6B64C`; greys `#6B7280`, `#374151`. Clean white/near-white background.
- **Type:** geometric sans-serif — Manrope, Inter, Outfit, or Sora. Strong hierarchy.
- **Feel:** modern, optimistic, professional. Generous whitespace, minimalist. Complexity → clarity.
- **Visual motifs (subtle):** upward momentum, paths forward, sunburst/segment shapes to show a career building up. A small progress indicator as sections complete fits the "momentum" idea.
- **Avoid:** AI clichés, dark/cyberpunk aesthetics, generic arrows, heavy gradients, traditional consulting-firm look.

Keep it accessible: high contrast, single-column, keyboard-navigable, readable labels.

## Make the honest path the easy path
Real inputs in, structured profile out, metric gaps flagged for the user to fill with true numbers. The UI should never make fabrication convenient.
