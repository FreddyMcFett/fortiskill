# Fortinet KB Article Style Guide (distilled from the Fortinet Community KB style conventions)

Apply every rule below. Editors reject articles for violations.

## Title
- Must begin with 'Technical Tip' or 'Troubleshooting Tip'. 'Technical Note' is NOT accepted.
- Goes in the KB title field, never inside the body.
- Include searchable product/feature names (e.g. product name + feature + outcome). People search for app/feature names, not categories.

## Templates
- **Default table template** (preferred): one table, rows Description / Scope / Solution, keyword in left cell bolded, content in right cell.
- **No-table template**: same three keywords as bold paragraphs, with a blank line between sections. Recommended when wide pictures will be added.
- **CLI commands template**: Product / Feature / Subcategory / Description of the command, plus a Commands | Description | Comments table.
- **Technical Guide template**: only for >= 1000 characters and >= 5 sections. Uses a Table of Contents with anchor links (see 'Section links' below). Do not use a ToC for short articles — use bold section labels and numbering instead.

## Language and tone
- Description's first sentence MUST be 'This article describes/discusses/explains…'.
- Never use pronouns referring to people: no 'I', 'you', 'we', 'he'. 'They' is allowed only for plural inanimate objects/concepts. Write impersonally: 'the organization', 'the user', 'administrators'.
- Use 'User' instead of 'Customer'.
- No contractions: 'does not', never 'doesn't'.
- Do not use 'please'. ('Please make sure to…' -> 'Make sure to…').
- Use 'select' instead of 'click' (exception: 'right-click').
- No informal filler phrases ('With that in mind', 'keep in mind'). Brevity preferred.
- No questions anywhere; no FAQ-style content.
- Every sentence ends with a period. Use commas to keep sentences readable.
- Use single quotes ' for emphasis/UI labels, never double quotes " (double quotes allowed only inside CLI commands).
- Write 'articles' / 'KB article', never bare 'KBs'.

## Product names and terms
- NEVER abbreviate products: FortiGate, FortiManager, FortiAnalyzer, FortiNAC, FortiSASE, FortiProxy — never FGT, FMG, FAZ.
- Canonical spellings: SD-WAN, SSL VPN, IP (caps only), IKE, IPsec.

## Formatting
- No heading elements (h1–h6). Use paragraph elements with bold for section labels.
- GUI paths: bold with '->' arrows, prefixed 'Go to'. Example: Go to **Security -> Traffic -> Security profiles**.
- Numbered lists (1. 2. 3. / a. b. c.) and bullets come from the editor toolbar (HTML: `<ol>`/`<ul>`), never manual '-' or '*' characters.
- Add blank space between sections and around images for readability; in HTML use `<p>&nbsp;</p>` spacers (the editor collapses margins).
- All images centered, with a blank line before and after.
- No trailing empty space at the end of Description or Solution sections.
- No table of contents for short articles.

## Commands and code
- All CLI commands, log output, code, HTML, XML, parameters go in code blocks (`<pre><code>` in HTML). Note: as of July 2026 'courier new' is broken in the editor — code blocks are mandatory.
- Never prefix commands with '#'.
- Write CLI keywords in full: 'diagnose', 'debug', 'disable' — never 'di', 'de', 'diag'.
- Indent config blocks: first level is an HTML indent, each further level 4 spaces; each nested 'config' gets an additional indent. Example:

```
config vpn ssl web portal
    edit "full-access"
        set mac-addr-check enable
        config mac-addr-check-rule
            edit "maclist"
                set mac-addr-list 11:11:11:11:11:11
            next
        end
    next
end
```

- No comments inside code blocks (users must be able to copy-paste). Put explanations as bullets after the block: 'In the configuration above, value1 should not exceed 3600.'

## Privacy and example values
- Hide serial numbers and real public IP addresses (note: 172.0.0.x and 192.0.0.x are PUBLIC ranges — do not mistake them for private).
- Use RFC 5737 documentation subnets for example public IPs: 192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24.
- Never include user-identifiable information: names, usernames, passwords, tenant IDs, customer names.
- Use vendor-documented example UUIDs and placeholder MACs (11:11:11:11:11:11).

## Links
- Hyperlink text = the exact title of the target page (SEO). Extra context (version, guide name) goes beside the link, not inside it. Example: See 'Getting started' for more information. / '…in the FortiSASE Administration Guide.'
- Links open in a new page.
- Never link to paid products/services or sites requiring payment.
- Never cite Reddit, personal blogs, or forums in the article body.

## Content policy
- No copy-paste from existing articles or docs — duplicates are deleted. Link to existing coverage instead of re-explaining it.
- Do not submit internal or customer information.
- Updates to existing articles must add substance (fix technical errors, outdated content, screenshots, clarity) — not cosmetic rewording alone.

## Section links (Technical Guide ToC)
The editor has no native anchor feature; anchors are added via 'Edit HTML Source':
1. Wrap the target text: `<a id="section1_link">Section 1.</a>`
2. Create a link whose URL is `#section1_link`.
Note: this option may not be available in the new Community — confirm it still works before using; otherwise avoid the ToC.

## Editor-HTML conventions (learned from real editor round-trips)
- Every text block sits in `<p>…</p>`; list items are `<li><p>…</p></li>`.
- Line breaks inside a cell: `<br>`; section spacing: `<p>&nbsp;</p>`.
- Tables: `<table><colgroup>…</colgroup><tbody><tr><td><p>…` (the editor adds min-width styles — harmless, keep them when re-editing pasted content).
- The editor rewrites pasted HTML (adds classes like 'text-fortinet-red underline' to links, normalizes attributes). When the user pastes back their current version, treat it as the baseline and edit on top of it rather than regenerating from the original draft.
- Screenshots become hosted `<img>` tags after upload; when drafting, place an HTML comment placeholder `<!-- screenshot: … -->` where an image belongs, or keep the user's existing `<img>` tags untouched.
