#!/usr/bin/env python3
"""Validate the fortiskill plugin/marketplace layout.

Checks that .claude-plugin/marketplace.json and plugin.json parse and carry the
required fields, and that every skills/<name>/SKILL.md has YAML frontmatter whose
`name` matches its folder and whose `description` is present and within the
1024-character limit. Run from anywhere: python3 scripts/validate_plugin.py
"""
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
errors = []


def err(msg):
    errors.append(msg)


def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        err(f"{path.relative_to(ROOT)}: missing")
    except json.JSONDecodeError as e:
        err(f"{path.relative_to(ROOT)}: invalid JSON ({e})")
    return None


def check_manifests():
    market = load_json(ROOT / ".claude-plugin" / "marketplace.json")
    plugin = load_json(ROOT / ".claude-plugin" / "plugin.json")
    if market is not None:
        for key in ("name", "owner", "plugins"):
            if key not in market:
                err(f"marketplace.json: missing '{key}'")
        for i, p in enumerate(market.get("plugins", [])):
            for key in ("name", "source"):
                if key not in p:
                    err(f"marketplace.json: plugins[{i}] missing '{key}'")
    if plugin is not None:
        if not NAME_RE.match(plugin.get("name", "")):
            err("plugin.json: 'name' missing or not kebab-case")
        if market is not None and plugin.get("name") not in {
            p.get("name") for p in market.get("plugins", [])
        }:
            err("plugin.json: name not listed in marketplace.json plugins")


def check_skills():
    skill_dirs = sorted(d for d in (ROOT / "skills").iterdir() if d.is_dir())
    if not skill_dirs:
        err("skills/: no skill folders found")
    for d in skill_dirs:
        rel = d.relative_to(ROOT)
        skill_md = d / "SKILL.md"
        if not skill_md.is_file():
            err(f"{rel}: missing SKILL.md")
            continue
        m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", skill_md.read_text(encoding="utf-8"), re.S)
        if not m:
            err(f"{rel}/SKILL.md: missing YAML frontmatter")
            continue
        try:
            fm = yaml.safe_load(m.group(1)) or {}
        except yaml.YAMLError as e:
            err(f"{rel}/SKILL.md: invalid frontmatter YAML ({e})")
            continue
        name, desc = fm.get("name"), fm.get("description")
        if name != d.name:
            err(f"{rel}/SKILL.md: name '{name}' does not match folder '{d.name}'")
        if not isinstance(desc, str) or not desc.strip():
            err(f"{rel}/SKILL.md: description missing")
        elif len(desc) > 1024:
            err(f"{rel}/SKILL.md: description is {len(desc)} chars (max 1024)")
        for cache in d.rglob("__pycache__"):
            err(f"{cache.relative_to(ROOT)}: committed bytecode cache")
        print(f"ok  {rel}")


check_manifests()
check_skills()
if errors:
    print("\n".join(f"ERROR {e}" for e in errors), file=sys.stderr)
    sys.exit(1)
print("plugin layout valid")
