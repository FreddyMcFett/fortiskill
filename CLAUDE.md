# fortiskill

Source repo for the user's personal Claude Skills used for daily Fortinet presales
engineering work (DACH / Switzerland). See `README.md` for the full skill descriptions.

**This repository is public.** Everything pushed, to any branch, is published
immediately and stays retrievable (PR refs survive branch deletion). Read the
Compliance section below before every commit.

## Repo = plugin + marketplace

This repo is a Claude plugin marketplace (`.claude-plugin/marketplace.json`) that
ships one plugin, `fortiskill`, whose root is the repo root
(`.claude-plugin/plugin.json`). Every folder under `skills/` with a `SKILL.md` is
auto-discovered as a skill of that plugin. Team members install it once
(`/plugin marketplace add FreddyMcFett/fortiskill`, then
`/plugin install fortiskill@fortiskill`, or Customize → Plugins on
claude.ai/Desktop) and get updates via auto-update / sync.

`plugin.json` intentionally has **no `version` field**: Claude then versions the
plugin by git commit SHA, so every merge to `main` reaches users. Do not add a
`version` (that would freeze updates until someone bumps it), and ignore the
resulting `claude plugin validate` warning. `main` is effectively the release
channel — only merge validated changes.

## Repo vs. this session's runtime

Inside a cloud session in this repo, skills still load from `~/.claude/skills`
(synced from the user's claude.ai library), not from this checkout.
`.claude/hooks/session-start.sh` (registered via `.claude/settings.json`) mirrors
every `skills/*/` folder over the copies in `~/.claude/skills` on SessionStart so
the checked-out version is what runs, sets `core.hooksPath` to `.githooks` (compliance
scan on every commit), and ensures `openpyxl` is installed for the BOM scripts. Do not
enable the plugin in this repo's `.claude/settings.json` — it would load every skill
twice next to the mirrored copies.

## Structure

Five independent skills under `skills/`, each a self-contained folder with
`SKILL.md` (trigger + instructions) plus `references/`, `scripts/`, `assets/`:

- `skills/fortinet-engineer/` — core Fortinet engineering skill (architecture,
  presales, troubleshooting, sizing, OT/ICS). Content-only (`SKILL.md` +
  `references/*.md`).
- `skills/fortinet-pptx/` — Fortinet-branded PowerPoint decks in the modern
  gradient house style. Has the real Fortinet 16:9 template (`assets/`), a brand
  spec, the `ftnt_deck.py` / `ftnt_modern.py` helpers embedded in `SKILL.md`, and
  `scripts/render_slides.py` for visual QA (needs `soffice`; falls back
  `pdftoppm` → PyMuPDF).
- `skills/fortinet-bom/` — Fortinet BOM/quote Excel workbooks. Has
  `scripts/pricelist_lookup.py` (SKU/price verification against a Fortinet price
  list xlsx, needs `openpyxl`) and `scripts/sfdc_csv_check.py` (Salesforce Quote
  Lines CSV validation).
- `skills/fortinet-kb-article/` — Fortinet Community KB articles in KCS style.
  Content-only (`SKILL.md` + `references/style-guide.md` + `assets/*.html`).
- `skills/faz-log-forge/` — synthetic FortiGate logs for FortiAnalyzer demos.
  Stdlib-only scripts (`fazgen.py`, `verify_logs.py`, `rating.py`,
  `ingest_rating_export.py`) plus `data/*.json` catalogs.

`scripts/validate_plugin.py` checks the manifests and every skill's frontmatter
(`name` must equal the folder name, `description` ≤ 1024 chars).
`scripts/compliance_scan.py` is the compliance gate (see below), and
`scripts/sanitize_office.py` strips personal metadata from Office files. CI
(`.github/workflows/release-check.yml`) runs two jobs on every PR and push to main:
**Compliance scan** (`--self-test`, then tree + every PR commit + PR title/body) and
**Plugin validation** (`validate_plugin.py` plus `--help` on each script). There is no
other build, lint, or test suite.

## Compliance (public repo)

- Before every commit: `python3 scripts/compliance_scan.py --staged` must report 0 errors
  (the pre-commit hook runs it when `core.hooksPath=.githooks`). Never push with errors:
  a pushed branch is already public, CI only reports after the fact.
- Never add customer, project, partner/distributor or person names (including the
  user's own name, nickname or user handles), real configs/logs, serial numbers, public
  IPs, MACs, tenant IDs, hostnames, prices, discounts, SFDC data, roadmap or other
  non-public material, internal links or notes from real engagements. Use RFC 5737 IPs,
  `example.com`, DEMO serials, `00:00:5e:00:53:xx` MACs and generic placeholder names.
- Never add `[[allow]]` entries to `.compliance/policy.toml`, change its settings, or
  weaken a rule in `compliance_scan.py` to get a green run without the user's explicit
  approval. Every entry needs a real reason.
- New or replaced Office files: run `scripts/sanitize_office.py` first, then ask the
  user before adding the file's policy entry.
- PR titles, PR descriptions and commit messages are scanned and public too: describe
  findings generically, never quote the sensitive value.
- When editing `compliance_scan.py`: keep it clean under its own scan (write phrase
  patterns with `{W}` gaps or a `[x]` character class, build self-test samples with
  `j()`), then run `--self-test` and a full scan.

## Editing conventions

- Keep the non-negotiables in `skills/fortinet-engineer/SKILL.md` (source hierarchy,
  anti-hallucination rules, confidence tags) intact — they're the point of the
  skill; don't soften them while doing unrelated edits.
- Never let prices or SKUs be invented — `fortinet-bom` always resolves them via
  `scripts/pricelist_lookup.py` against a real Fortinet price list, never from
  memory.
- On a FortiOS major/GA change, update
  `skills/fortinet-engineer/references/fortios-versions.md` and `product-portfolio.md`
  first (see README "Wartungshinweise").
- `skills/fortinet-pptx/assets/FTNT_PPT_16x9_Light_Template.pptx` is a real Fortinet
  source file — if Fortinet refreshes their CI/CD, replace it, sanitize it with
  `scripts/sanitize_office.py`, and re-diff `references/brand-spec.md` against slide 1
  of the new template.
- After changing a script under `scripts/`, run it directly to sanity-check
  (e.g. `python3 skills/fortinet-bom/scripts/pricelist_lookup.py --help`),
  `python3 scripts/validate_plugin.py` and `python3 scripts/compliance_scan.py`.
