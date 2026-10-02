---
name: fortinet-kb-article
description: Write, edit, or review Fortinet Community Knowledge Base (KB) articles in the official KCS style, delivered as editor-ready HTML. Use this skill whenever the user asks for a KB article, knowledge base article, Technical Tip, Troubleshooting Tip, KCS article, or community article — including turning a LinkedIn post, lab test, troubleshooting session, or config walkthrough into a KB article, converting existing notes into KB format, or checking an existing KB draft for style-guide compliance. Trigger even if the user only says 'make this a KB' or 'write this up for the community'.
---

# Fortinet Community KB Article Writer

Produce Fortinet Community Knowledge Base articles that pass editorial review on the first pass: correct template, correct style, verified technical content, and HTML that can be pasted directly into the KB editor's 'Edit HTML Source' view.

## Workflow

1. **Clarify scope (only if genuinely unclear).** Determine: topic, affected products/versions, whether the article is Internal Only or public, and whether the user has lab-tested results. Do not interrogate the user if the conversation already contains this.

2. **Verify every technical claim before writing.**
   - Fortinet features, GUI paths, CLI syntax: verify against https://docs.fortinet.com (version-specific — check the exact FortiOS/FortiSASE/product version) and https://community.fortinet.com.
   - Third-party/vendor features (e.g. SaaS tenant-restriction headers): verify against the vendor's official documentation and link it.
   - Never cite or link Reddit, blogs, or paid services in the article. If information originates from Reddit or a user's own testing and cannot be confirmed in official docs, phrase it as 'This behavior was verified in lab testing.' and tell the user in chat which claims rest only on their tests.
   - Use documentation-reserved example values: RFC 5737 subnets (192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24) for public IPs, example UUIDs from vendor docs, placeholder MACs like 11:11:11:11:11:11. Never include real serial numbers, real public IPs, usernames, tenant IDs, or customer names.

3. **Choose the template** (details in `references/style-guide.md`):
   - **Default table template** — Description/Scope/Solution in a table. Use unless a reason not to.
   - **No-table template** — same keywords without a table; use when wide screenshots will be added.
   - **CLI commands template** — for command-reference articles (Product/Feature/Subcategory + commands table).
   - **Technical Guide template** — only for long-form content (>= 1000 characters, >= 5 sections) with a Table of Contents using anchor links.

4. **Write the article** following ALL rules in `references/style-guide.md`. Read that file before writing — the rules are strict, non-obvious, and enforced by editors (no pronouns, no headings, no contractions, 'select' not 'click', bold GUI paths with '->', full product names, etc.).

5. **Deliver.**
   - Provide the title separately in chat (it goes in the KB title field, not the body). Titles MUST begin with 'Technical Tip' or 'Troubleshooting Tip'. 'Technical Note' is rejected.
   - Create the article body as an .html file starting from `assets/template-table.html` (or `assets/template-no-table.html`) and present it to the user. The HTML conventions in those templates match what the community editor produces — keep them (every text block in `<p>`, spacing via `<p>&nbsp;</p>`, code in `<pre><code>`, list items as `<li><p>…</p></li>`).
   - In chat, summarize: which claims are doc-verified (with source), which are lab-tested only, and any GUI paths that vary between product versions so the user can confirm against their tenant.

## Recommended Solution-section structure (for how-to articles)

Bold paragraph labels, never headings: intro paragraphs (what/why), **Requirements:** (bulleted — licensing, inspection mode, certificates, profile/policy prerequisites), **Step 1..N:** numbered instructions with GUI paths, config examples in code blocks with a screenshot placeholder after, per-step notes as bullets under the step, **Notes:** (limitations, alternatives on other Fortinet products with doc links), **Related documents:** (official doc links, link text = exact page title).

## Editing an existing draft

When the user pastes an existing article or asks for a review: check it against every rule in `references/style-guide.md`, fix violations, and list what was changed and why. When the user pastes back editor-normalized HTML of a previous draft, treat THAT as the new baseline — preserve their manual edits (paths, screenshots, wording) and apply only the requested changes on top.

## Hard content rules (summary — full list in references/style-guide.md)

- Never copy text from existing articles or official docs (duplicates are rejected); write original content and link instead.
- No questions or FAQ format anywhere in the article.
- No links to paid products/services.
- Description must open with 'This article describes/discusses/explains…'.
- Internal or customer information must never appear; if the article is not Internal Only, it must contain nothing internal.
