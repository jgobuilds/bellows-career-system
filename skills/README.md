# Generated — do not edit these files

Every `*.skill` in this folder is **built** by
[`tools/build_skills.py`](../tools/build_skills.py) from the sources in
[`.claude/skills/`](../.claude/skills). The arrow only ever points one way:

```
.claude/skills/<name>/   →   skills/<name>.skill
      source                    distributable
```

**To change a skill, edit `.claude/skills/<name>/`, then run:**

```bash
python tools/build_skills.py
```

## Why the packages exist at all

If you use **Claude Code** or **Cowork**, you never need them. The sources in
`.claude/skills/` load automatically when you work in this repo, and that is what
the agent actually reads.

They exist for **Claude Desktop**, which cannot read a skill directory — it takes
packaged skills only, through *Settings → Capabilities → add skill*. They are
committed rather than published separately because a Desktop user may have arrived
here by downloading the ZIP without Git, and a source ZIP does not carry release
assets. Making them fetch a second download to install the thing they already have
is a worse trade than a little diff noise.

## Why editing an archive is the failure worth preventing

A stale zip looks completely fine from the outside. Nothing about it reads as wrong
until someone installs it and gets a version of a skill that no longer exists in
this repo — and by then the mismatch is invisible on both ends.

So the repo checks it rather than trusting it:

```bash
python tools/build_skills.py --check    # reports drift, changes nothing
```

`tests/test_skill_bundles.py` runs the same comparison in CI. Four things have to
hold: every package has a source, every source gets packaged, no package has
drifted from its source, and every source carries a `SKILL.md`.

Line endings are pinned to LF in `.gitattributes` and the comparison normalises
them anyway, so a checkout on any platform gets the same answer. That is not
theoretical — the first version of this setup failed its own check on a fresh
clone, because the packages were built from a CRLF working tree while git stored
LF.
