# certificates

Generate "Certificate of Achievement" PDFs on demand, via GitHub Actions or locally.

## What's in here

- **`templates/certificate.html`** — The certificate layout (HTML/CSS). Cream
  background, gold double-border frame, navy/gold color scheme. Every piece of
  per-certificate content is a `{{PLACEHOLDER}}` token — nothing dynamic is
  hardcoded here.
- **`templates/config.json`** — All the fixed brand/program content plus the
  defaults used when a per-run value isn't supplied (see **Fixed vs. per-run
  content** below). This is the single place to edit "what's on every
  certificate" without touching any code.
- **`templates/assets/signature.png`** — The signatory's actual signature
  image, always the same, stamped on every certificate.
- **`scripts/generate.py`** — CLI script that loads `config.json`, fills in
  `certificate.html`'s placeholders with the recipient's details, and renders
  the result to a PDF using [WeasyPrint](https://weasyprint.org/) (pure
  HTML/CSS → PDF, no headless browser required).
- **`.github/workflows/generate-certificate.yml`** — A `workflow_dispatch`
  GitHub Actions workflow that runs `generate.py` and uploads the PDF as a
  build artifact (optionally committing it to the repo too).
- **`requirements.txt`** — Pinned Python dependencies (WeasyPrint).

## Fixed vs. per-run content

Some content is **always the same** — the Ready4Industry brand, the "AI for
Everyone" program name, the closing statement, the signatory, and the seal —
and is never exposed as an input. It only lives in `templates/config.json`
(and `templates/assets/signature.png`), edited via a normal commit/PR if it
ever needs to change.

Everything else is **per-run**: recipient name, date, cert ID, track letter/
name, duration, time commitment, mode, and the achievement highlights. These
can be passed as CLI flags or GitHub Actions inputs, and fall back to the
defaults in `config.json` when left blank.

## Generate a certificate via GitHub Actions

1. Go to the **Actions** tab of this repository.
2. Select the **Generate Certificate** workflow in the sidebar.
3. Click **Run workflow**.
4. Fill in the inputs:
   - **name** (required) — the recipient's full name.
   - **date** (optional) — completion date, e.g. `3rd July 2026`. Defaults to
     today.
   - **track_letter**, **track_full**, **duration**, **time_commitment**,
     **mode**, **cert_id** (optional) — override the defaults from
     `templates/config.json` for this one certificate.
   - **highlights_intro** (optional) — override the achievement highlights
     intro paragraph.
   - **highlight1_title** / **highlight1_desc** through **highlight5_title** /
     **highlight5_desc** (optional) — override individual achievement
     highlights. Each is its own field in the Actions form (GitHub Actions
     inputs are single-line, so a title/description pair per field keeps each
     highlight readable instead of one long delimited string). Leave a pair
     blank to keep that slot's default from `templates/config.json`.
   - **commit_to_repo** (optional, default `false`) — if checked, the
     generated PDF is committed into a `certificates/` folder on the branch
     the workflow runs on, in addition to being uploaded as an artifact.
5. Click **Run workflow** and wait for it to finish.
6. Open the completed run and download the PDF from the **Artifacts** section
   (or, if `commit_to_repo` was checked, find it under `certificates/` in the
   repo).

## Generate a certificate locally

```bash
pip install -r requirements.txt
python scripts/generate.py --name "Jane Doe"
```

The PDF is written to `output/<slugified-name>-certificate.pdf` by default.

Useful options:

```bash
python scripts/generate.py \
  --name "Jane Doe" \
  --date "3rd July 2026" \
  --cert-id "R4I-AFE-A-20260703-001" \
  --track-letter "B" \
  --track-full "AI for Product Teams" \
  --duration "3 days" \
  --time-commitment "2 hours per day" \
  --mode "Self-paced online" \
  --highlights-intro "Having completed this track, the candidate has..." \
  --highlight1-title "Prompt engineering" \
  --highlight1-desc "Crafting effective prompts." \
  --highlight2-title "Strategic AI use" \
  --highlight2-desc "Deploying AI tools daily." \
  --output "output/jane-doe.pdf"
```

Run `python scripts/generate.py --help` for the full list of flags. Only
`--name` is required; everything else falls back to today's date, an
auto-generated certificate ID, or the defaults in `templates/config.json`.

WeasyPrint needs a few system libraries (Pango, Cairo, GDK-Pixbuf) to render
fonts and layout correctly. On Debian/Ubuntu:

```bash
sudo apt-get install libpango-1.0-0 libpangocairo-1.0-0 libpangoft2-1.0-0 \
  libgdk-pixbuf2.0-0 libcairo2 libffi-dev fonts-liberation shared-mime-info
```

See the [WeasyPrint install docs](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation)
for macOS/Windows instructions.

## Customizing

- **Content that's always the same** (brand name/tagline, program name,
  closing statement, signatory name/role/signature image, seal) — edit
  `templates/config.json` (or replace `templates/assets/signature.png`). Not
  exposed as a CLI flag or workflow input by design.
- **Content that varies per cohort/run but should still have a sensible
  default** (track info, duration, time commitment, mode, highlights) — edit
  the defaults in `templates/config.json`, and/or override per-run via CLI
  flags or workflow inputs.
- **Layout, styling, or visual design** (colors, fonts, spacing, what
  sections exist) — edit `templates/certificate.html`. Placeholders are plain
  `{{TOKEN}}` strings substituted by `scripts/generate.py`; add a new one in
  both places if you need a new dynamic field.
- **Per-recipient details** (name, date, cert ID) — passed as CLI flags /
  workflow inputs, never edited directly in the template or config.
