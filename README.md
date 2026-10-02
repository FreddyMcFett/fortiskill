# FortiSkill: Fortinet Claude Skills

Claude-Skills für die tägliche Fortinet-Presales-Arbeit (DACH), als Claude-Plugin mit
Auto-Update. Privates Team-Projekt, kein offizielles Fortinet-Produkt; Fortinet,
FortiGate, FortiOS usw. sind Marken der Fortinet, Inc.

> **Dieses Repo ist öffentlich.** Alles, was gepusht wird, auch auf einen PR-Branch, ist
> sofort öffentlich. Jeder PR läuft deshalb durch den [Compliance-Check](#compliance-check-release-gate).

## Installation (einmalig pro Person)

### Claude Code (CLI, VS Code, JetBrains)

```text
/plugin marketplace add FreddyMcFett/fortiskill
/plugin install fortiskill@fortiskill
```

oder im Terminal:

```bash
claude plugin marketplace add FreddyMcFett/fortiskill
claude plugin install fortiskill@fortiskill
```

**Auto-Update einschalten** (wichtig, für Dritt-Marketplaces ist es standardmässig
aus): `/plugin` → Tab **Marketplaces** → `fortiskill` → **Enable auto-update**.
Danach zieht Claude Code beim Start die neueste Version. Manuell geht es jederzeit mit
`claude plugin marketplace update fortiskill` bzw.
`claude plugin update fortiskill@fortiskill`.

### claude.ai und Claude Desktop

**Customize → Plugins → Add → Add marketplace** → `FreddyMcFett/fortiskill`
eingeben, dann das Plugin `fortiskill` installieren und auf der Marketplace-Seite
**Sync automatically** einschalten.

Auf einem Team-/Enterprise-Plan kann ein Org-Admin den Marketplace stattdessen unter
**Organization settings → Plugins & skills** für alle Mitglieder einrichten.

> **Wichtig, falls du die Skills schon anders installiert hast** (einzeln hochgeladen
> oder über einen anderen Marketplace): Die alten Kopien (`fortinet-engineer`,
> `fortinet-bom`, `fortinet-pptx`, `fortinet-kb-article`, `faz-log-forge`) entfernen,
> unter Customize → Skills/Plugins bzw. mit `claude plugin list` /
> `claude plugin uninstall <plugin>` und `claude plugin marketplace remove <name>`.
> Sonst existiert jeder Skill doppelt und Claude nimmt eventuell die alte Kopie.

### Warum Updates automatisch ankommen

`.claude-plugin/plugin.json` hat bewusst **kein** `version`-Feld. Claude verwendet dann
den Git-Commit-SHA als Version, d. h. **jeder Merge auf `main` ist eine neue Version**
und wird beim nächsten Auto-Update verteilt. Würde man ein `version`-Feld setzen, kämen
Änderungen nur noch an, wenn diese Nummer hochgezählt wird. `claude plugin validate`
meldet das fehlende Feld deshalb als (erwartete) Warnung.

## Die Skills

| Skill | Zweck |
|---|---|
| [`fortinet-engineer`](skills/fortinet-engineer/) | Senior-Level Fortinet-Engineering über das ganze Portfolio: Solution Architecture, Presales, Implementation, Troubleshooting, Automation, Sizing/Licensing, OT/ICS. Erzwingt Verifikation gegen docs.fortinet.com und explizite Confidence-Tags statt halluzinierter CLI-Befehle, SKUs und Durchsatzzahlen. |
| [`fortinet-pptx`](skills/fortinet-pptx/) | PowerPoint-Decks auf dem offiziellen Fortinet 16:9-Template im modernen Gradient-House-Style (Gradient-Cards, Icon-Badges, Soft Shadows), Icons von icons.fortinet.com, plus portabler QA-Renderer. |
| [`fortinet-bom`](skills/fortinet-bom/) | Fortinet Bill of Materials als Excel-Workbook: Engineering-BOM (verifizierte SKUs, Sektionen, Optionsblöcke, Live-Formeln), Kunden-Konfigurator (CAPEX/OPEX/TCO, Szenario-Dropdowns) und SFDC Quote-Lines-Import-CSV. Preise kommen ausschliesslich aus einer offiziellen Fortinet-Preisliste — nie geraten. |
| [`fortinet-kb-article`](skills/fortinet-kb-article/) | Fortinet Community Knowledge-Base-Artikel im offiziellen KCS-Stil, als editor-fertiges HTML. Erzwingt Verifikation jeder technischen Aussage gegen docs.fortinet.com/community.fortinet.com, den strikten Style Guide (keine Pronomen, keine Überschriften, 'select' statt 'click', RFC-5737-Beispielwerte) und liefert direkt einfügbares HTML aus den Community-Editor-Templates. |
| [`faz-log-forge`](skills/faz-log-forge/) | Synthetische, FortiOS-native FortiGate-Logs für FortiAnalyzer-Demos/PoCs (Assets, IoT/OT, Traffic, VoIP, Security Events, Security-Rating-Stream), inkl. Verifikations-Script gegen echte FortiOS 7.6/8.0-Logformate. |

Im Plugin heissen die Skills `fortiskill:<skill>` (z. B. `fortiskill:fortinet-bom`).

### fortinet-engineer


Der Kern-Skill. Deckt alle Rollen ab (Architect, Presales, Implementation,
Troubleshooting, Automation) und das volle Produktportfolio nach den drei Säulen
(Secure Networking, Unified SASE, Security Operations).

Die Nicht-Verhandelbaren:

- **Quellenhierarchie**: docs.fortinet.com → KB → Datasheets → Ordering Guides →
  Service Descriptions → Community (markiert) → Third-Party (markiert).
- **Anti-Halluzination**: keine CLI-Befehle, SKUs oder Performance-Zahlen ohne
  Verifikation bzw. ohne explizites `[unverified]`-Label.
- **Confidence-Tags** an jeder nicht-trivialen Aussage.
- **DACH-Kontext**: FADP, FINMA, NIS2, DORA, IEC 62443, Datenresidenz (Swiss/EU PoPs).

Kalibriert auf **FortiOS 7.6.6 GA** als Default-Annahme und den Portfolio-Stand nach
Accelerate 2026 (FortiOS 8.0 angekündigt).

### fortinet-pptx

Baut auf dem generischen `pptx`-Skill auf (Validierung, Thumbnails, OOXML-Mechanik) und
ergänzt die Fortinet-spezifischen Inputs:

- `assets/FTNT_PPT_16x9_Light_Template.pptx` — offizielles Fortinet-Template,
  37 Layouts, 55 Referenz-Slides (Slide 1 ist Fortinets eigene Farbreferenz).
- `references/brand-spec.md` — exakte Hex-Werte (Secure Red `DA291C`,
  FortiGuard Green `3CB17E`, …), Typografie- und Motiv-Regeln.
- House Style (seit September 2026): moderner Gradient-Style nach Fortinets aktuellen
  Corporate Sales Decks, gebaut mit den in `SKILL.md` eingebetteten Helfern
  `ftnt_deck.py` / `ftnt_modern.py` (`ModernDeck`). Icons ausschliesslich von
  icons.fortinet.com.
- `scripts/render_slides.py` — rendert Decks zu JPEGs für visuelles QA; findet
  `soffice` auch ausserhalb des PATH und fällt automatisch von `pdftoppm` auf
  PyMuPDF zurück.

**Voraussetzungen**: `pip install python-pptx cairosvg` für den Build und die
Icon-Rasterisierung; für das QA-Rendering LibreOffice (inkl. Impress) sowie
`poppler-utils` *oder* `pip install pymupdf`.

### fortinet-bom


Drei Liefertypen: Engineering-BOM (intern/Partner), Kunden-Konfigurator und
SFDC-Quote-Lines-Import-CSV (aus einer bestehenden Engineering-BOM abgeleitet, EMEA-Suffix,
Validierung via `scripts/sfdc_csv_check.py`). Grundregeln: keine erfundenen Preise, keine
erfundenen SKUs (Batch-Verifikation via `scripts/pricelist_lookup.py`), Lizenzlogik aus
Ordering Guides, Live-Excel-Formeln, Preisbasis immer im Header.

**Voraussetzungen**: eine Fortinet-Preisliste als xlsx (mit `DataSet`-Sheet) als
Preisquelle und `pip install openpyxl` für die Skripte.

### fortinet-kb-article

Schreibt, editiert und prüft Fortinet Community Knowledge-Base-Artikel (Technical
Tip / Troubleshooting Tip) im offiziellen KCS-Stil. Deckt vier Templates ab
(Default-Tabelle, tabellenlos, CLI-Commands, Technical Guide mit ToC),
erzwingt Quellenverifikation vor jeder technischen Aussage und liefert die
Artikel-Body als HTML, das direkt in die 'Edit HTML Source'-Ansicht des
Community-Editors eingefügt werden kann.

- `references/style-guide.md` — destillierter Style Guide (Sprache/Ton,
  Formatierung, Privacy/Beispielwerte, Links, Editor-HTML-Konventionen).
- `assets/template-table.html` / `assets/template-no-table.html` —
  Editor-Ausgangs-Templates für die beiden Standard-Artikeltypen.

### faz-log-forge

Generiert FortiOS-native Raw-Logs (`date=... time=... key=value ...`) für FortiGates,
die es nicht gibt, damit FortiAnalyzer-Dashboards, FortiView, Asset Identity Center,
IoT-/OT-View, Compromised Hosts und Security-Rating-Reports in Demos und PoCs echte
Daten zeigen. Feldnamen, Log-IDs und Quoting stammen aus echten FortiOS 7.6.6 / 8.0.0
Logs und FortiAnalyzer-Exports; nicht verifizierte Werte sind in den Referenzen markiert.

- `scripts/fazgen.py` — Generator (Fleets: enterprise, healthcare, ot-manufacturing,
  retail, smartbuilding; `--list-fleets`).
- `scripts/verify_logs.py` — Pflicht-Check nach jedem Lauf (Envelope-Felder,
  Zeit-Drift, Quoting, Feldnamen, Asset-Coverage, Security-Rating-Konsistenz).
- `scripts/rating.py`, `scripts/ingest_rating_export.py` — Security-Rating-Stream und
  Übernahme echter FortiAnalyzer-Exports.
- `references/faz-import.md` — `execute log import` auf dem FortiAnalyzer.

**Voraussetzungen**: nur Python 3 (Standardbibliothek).

## Änderungen beitragen (Team-Workflow)

1. Einmal pro Clone die Compliance-Hooks aktivieren: `git config core.hooksPath .githooks`
   (in Claude-Cloud-Sessions erledigt das der SessionStart-Hook).
2. Branch erstellen, Skill unter `skills/<skill>/` ändern (meist `SKILL.md` oder
   `references/*.md`).
3. Pull Request auf `main` öffnen. Die GitHub Action **Release check** hat zwei Jobs:
   - **Plugin validation** prüft Manifeste, Skill-Frontmatter (`name` = Ordnername,
     `description` ≤ 1024 Zeichen) und ruft die Python-Scripts mit `--help` auf.
     Lokal: `python3 scripts/validate_plugin.py` und optional `claude plugin validate .`.
   - **Compliance scan** blockiert Secrets, Personendaten, vertrauliche und interne
     Inhalte (siehe [Compliance-Check](#compliance-check-release-gate)).
4. Nach dem Merge auf `main` bekommen alle mit aktiviertem Auto-Update / Sync die neue
   Version automatisch beim nächsten Start bzw. Sync.

Ein neuer Skill = neuer Ordner `skills/<name>/` mit `SKILL.md` (Frontmatter `name`
identisch zum Ordnernamen). Er wird automatisch Teil des Plugins, es muss kein Manifest
angepasst werden.

## Compliance-Check (Release Gate)

`main` ist der Release-Kanal (jeder Merge geht per Auto-Update an alle) und das Repo ist
öffentlich. `scripts/compliance_scan.py` (nur Python-Standardbibliothek) prüft deshalb:

| Wo | Was |
|---|---|
| Jeder PR (CI) | kompletter Stand nach dem Merge, **jede Datei-Version jedes Commits im PR** (auch Inhalte, die im PR wieder gelöscht wurden), Commit-Messages, Commit-Autor-E-Mails, PR-Titel und -Beschreibung |
| Push auf `main` (CI) | kompletter Stand und die neuen Commits |
| Lokal, vor jedem Commit | gestagte Dateien (`pre-commit`) und die Commit-Message (`commit-msg`) |

Geprüfte Regeln (vollständige Liste: `python3 scripts/compliance_scan.py --list-rules`):

| Kategorie | Blockiert (Fehler) | Hinweis (Warnung) |
|---|---|---|
| Secrets | Private Keys, Lizenzdateien, GitHub-/AWS-/Anthropic-/OpenAI-/Google-/Slack-Tokens, Webhook-URLs, JWT, Passwörter in URLs, Bearer-Tokens, FortiOS-`ENC`-Secrets und Klartext-`set password/psksecret`, hart codierte Credentials | |
| Personendaten | E-Mail-Adressen (ausser `example.com` & Co.), Telefonnummern (international, CH), IBAN (Prüfziffer), AHV-Nummern (Prüfziffer), Kreditkarten (Luhn), echte MAC-Adressen | |
| Netz & Geräte | öffentliche IPv4 ausserhalb RFC 5737 (ausser bekannte Resolver), echte Fortinet-Seriennummern (DEMO-Serials erlaubt), FortiClient-EMS-Cloud-Tenants | |
| Vertraulichkeit | Klassifizierungsvermerke (DE/EN/FR/IT), TLP Red/Amber | Hinweise auf Geheimhaltungsmaterial, noch nicht öffentliche Infos |
| Intern | Links auf SharePoint/OneDrive, Salesforce, Teams, Confluence/Jira, Google Drive, Zoom/Webex, Miro …; persönliche oder projektbezogene Notizen, Verweise auf interne Richtlinien | Partner-Portal-Links |
| Kommerziell | Preise neben SKUs, Rabattsätze, Salesforce-Record-IDs | sonstige Währungsbeträge |
| Office / PDF / Bilder | Autoren- und Reviewer-Namen, Co-Authoring-Verlauf, Kommentare, Sensitivity Labels; Text in Folien/Notizen/Tabellen läuft durch alle obigen Regeln; PDF-Autor; EXIF-GPS und -Autor | |
| Dateitypen | Schlüssel/Zertifikate/Lizenzen/`.env`, pcap/HAR/Dumps, `.log`/`.conf`; Office-, Daten- und Archivdateien nur mit Policy-Eintrag | Binärdateien, die nicht gescannt werden können |
| Kunden-Denylist | Begriffe aus dem Repo-Secret `COMPLIANCE_DENYLIST`, auch in Dateinamen | |
| Commits | | private E-Mail-Adresse als Autor/Committer |

Gefundene Werte werden nie im Klartext ausgegeben (`ab…yz, 16 chars`), denn auch die
CI-Logs eines öffentlichen Repos sind öffentlich.

**Lokal ausführen**

```bash
python3 scripts/compliance_scan.py                          # ganzer Stand
python3 scripts/compliance_scan.py --staged                 # nur gestagte Änderungen
python3 scripts/compliance_scan.py --commits origin/main..HEAD
python3 scripts/compliance_scan.py --self-test              # Regeln gegen eingebaute Beispiele
python3 scripts/sanitize_office.py deck.pptx                # Personen-Metadaten aus Office-Dateien entfernen
```

**Ausnahmen** gibt es nur über `.compliance/policy.toml`: ein `[[allow]]`-Eintrag pro Fall
mit `rule`, `path`, optional `match` und `expires`, und immer mit `reason`. Einträge, die
nichts mehr treffen, meldet der Scan als veraltet. Die Datei ist per `.github/CODEOWNERS`
geschützt. Neue Office-Dateien zuerst mit `scripts/sanitize_office.py` bereinigen, dann
mit Begründung eintragen.

**Kunden-Denylist.** Kunden-, Projekt-, Personen- und Distributor-Namen lassen sich nicht
per Muster erkennen. Sie gehören in das Repository-Secret `COMPLIANCE_DENYLIST` (Settings →
Secrets and variables → Actions, ein Begriff pro Zeile) und für lokale Läufe in
`.compliance/denylist.local.txt` (per `.gitignore` ausgeschlossen). Für Claude-Cloud-Sessions
dieselbe Liste als Umgebungsvariable `COMPLIANCE_DENYLIST` in der Environment-Konfiguration
hinterlegen, damit der Commit-Hook sie auch dort kennt. PRs aus Forks bekommen keine
Secrets; dort läuft der Scan ohne Denylist.

**Wenn ein Fund „in commit …“ gemeldet wird**, ist der Inhalt bereits öffentlich, weil der
Branch gepusht ist. Dann: (1) Secret sofort widerrufen bzw. rotieren, (2) den Branch ohne
den Inhalt neu aufbauen und force-pushen oder den PR schliessen und einen neuen öffnen,
(3) bei Personendaten den GitHub Support bitten, gecachte Ansichten und die
`refs/pull/<n>`-Referenzen zu entfernen (siehe GitHub Docs „Removing sensitive data from a
repository“). PR-Refs bleiben sonst auch nach dem Löschen des Branches abrufbar.

**Einmalige Einrichtung (Repo-Admin)**

- Ruleset bzw. Branch Protection für `main`: Pull Request erforderlich, Required Status
  Checks `Compliance scan` und `Plugin validation`, optional „Require review from Code
  Owners“.
- Settings → Code security: Secret Scanning und **Push Protection** aktiviert lassen. Push
  Protection blockiert bekannte Token-Formate schon beim Push, also bevor sie öffentlich
  sind; der Compliance-Scan in der CI greift erst danach.
- Optional das Secret `COMPLIANCE_DENYLIST` anlegen (siehe oben).

## Repo-Struktur

```
.claude-plugin/
├── marketplace.json            # Marketplace "fortiskill" (dieses Repo)
└── plugin.json                 # Plugin "fortiskill" (Repo-Root, ohne version → Commit-SHA)
skills/
├── fortinet-engineer/
│   ├── SKILL.md                # Trigger, Workflow, Non-Negotiables
│   ├── references/             # 11 Referenzen (Portfolio, CLI, Sizing, OT, …)
│   └── assets/templates/       # BoM-, Discovery-, Runbook-Templates
├── fortinet-pptx/
│   ├── SKILL.md                # House Style + eingebettete Helper-Libraries
│   ├── assets/                 # Offizielles Fortinet-Template (16:9 Light)
│   ├── references/brand-spec.md
│   └── scripts/render_slides.py
├── fortinet-bom/
│   ├── SKILL.md
│   ├── references/             # Engineering-BOM-, Kunden-BOM-, SKU-, SFDC-Import-Spezifikationen
│   └── scripts/                # pricelist_lookup.py, sfdc_csv_check.py
├── fortinet-kb-article/
│   ├── SKILL.md
│   ├── references/style-guide.md
│   └── assets/                 # Editor-HTML-Templates (mit/ohne Tabelle)
└── faz-log-forge/
    ├── SKILL.md
    ├── references/             # Log-Anatomie, Log-Typen, Assets/IoT, Security Rating, FAZ-Import
    ├── data/                   # Device-/OUI-/Fleet-Kataloge, Security-Rating-Checks
    └── scripts/                # fazgen.py, verify_logs.py, rating.py, ingest_rating_export.py
scripts/
├── validate_plugin.py          # Layout-/Frontmatter-Validierung (lokal + CI)
├── compliance_scan.py          # Compliance-Scan (lokal, Git-Hooks, CI)
└── sanitize_office.py          # entfernt Personen-Metadaten aus Office-Dateien
.compliance/policy.toml         # begründete Ausnahmen + Settings des Compliance-Scans
.githooks/                      # pre-commit / commit-msg → compliance_scan.py
.github/
├── workflows/release-check.yml # CI für PRs und main: Compliance scan + Plugin validation
├── CODEOWNERS                  # Review-Pflicht für Compliance-Gate und CI
└── pull_request_template.md    # Compliance-Checkliste
```

## Wartungshinweise


- Die Skills sind bewusst versionsbewusst geschrieben: Bei einem neuen
  FortiOS-Major/GA-Wechsel zuerst `skills/fortinet-engineer/references/fortios-versions.md`
  und `product-portfolio.md` aktualisieren (Default-Version, Pillar-Zuordnung,
  neue Produkte).
- Bundle-Zusammensetzungen (ATP/UTP/ENT), FortiCare-Tiers und SKU-Muster ändern
  sich laufend — die Skills verweisen deshalb konsequent auf die jeweils aktuellen
  Ordering Guides statt Inhalte einzufrieren.
- Das PPTX-Template ist eine echte Fortinet-Quelldatei. Bei einem CI/CD-Refresh von
  Fortinet: Template ersetzen, mit `scripts/sanitize_office.py` bereinigen und
  `brand-spec.md` gegen Slide 1 des neuen Templates neu abgleichen.
