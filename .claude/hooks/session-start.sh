#!/bin/bash
# SessionStart hook for the fortiskill repo.
#
# This repo IS the source for the Fortinet skills under skills/ (also shipped as the
# fortiskill plugin), but Claude Code loads skills from ~/.claude/skills,
# which is populated
# by syncing your account's uploaded skill library (CLAUDE_CODE_SYNC_SKILLS) --
# a separate copy, not this checkout. Editing SKILL.md here has no effect on the
# running session until the plugin is updated or the skill is re-uploaded (see README).
#
# To close that gap while working in this repo, mirror the repo's skill folders
# over the synced copies in ~/.claude/skills so the session always runs the
# checked-out version. This only affects this local session/container; it does
# not touch your account's skill library (still zip+upload for that, see README).
#
# The repo is public, so it also enables the compliance git hooks (.githooks/:
# scripts/compliance_scan.py on every commit) for this checkout.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

REPO_DIR="${CLAUDE_PROJECT_DIR:-/home/user/fortiskill}"
SKILLS_DIR="${HOME}/.claude/skills"
mkdir -p "$SKILLS_DIR"

for src in "$REPO_DIR"/skills/*/; do
  [ -f "$src/SKILL.md" ] || continue
  skill="$(basename "$src")"
  rm -rf "${SKILLS_DIR:?}/$skill"
  cp -r "$src" "$SKILLS_DIR/$skill"
done

git -C "$REPO_DIR" config core.hooksPath .githooks || true

# fortinet-bom scripts need openpyxl (pricelist_lookup.py, sfdc_csv_check.py --pricelist).
python3 -c "import openpyxl" 2>/dev/null || pip install --quiet --disable-pip-version-check openpyxl || true
