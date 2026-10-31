# Anki Card Generator

Generates Anki flashcard decks from PDF lecture notes using the Claude API.
One command reads your PDF, calls Claude, and produces an `.apkg` file ready to import into Anki.

## Prerequisites

- [Python 3.13+](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) — Python package manager
- [Anki desktop app](https://apps.ankiweb.net/) (2.1.50 or newer)
- An [Anthropic API key](https://console.anthropic.com/) (free tier works)

## Setup (first time only)

1. **Clone the repo**
   ```
   git clone https://github.com/pclutton/anki-cards
   cd anki-cards
   ```

2. **Install dependencies**
   ```
   uv sync
   ```

3. **Add your API key**

   Copy `.env.example` to `.env` and paste in your key:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```
   Get a free key at [console.anthropic.com](https://console.anthropic.com/).

The `Source Material/`, `Topics Requested/` and `Card Decks/` folders are created automatically the first time you run the script.

## Daily use

**Point it straight at an Obsidian note** — no exporting:
```
uv run make_cards.py "C:\Users\you\ObsidianVault\Lectures\Week 2 Gas Exchange.md"
```
Diagrams embedded with `![[image.png]]` are found automatically in your vault, so there's no
need to copy attachments anywhere.

**Or use a file you've dropped in `Source Material/`:**
```
uv run make_cards.py "Week 3 - Genetics.pdf"
```

**Several lectures at once — each gets its own deck:**
```
uv run make_cards.py "Week 2 Gas Exchange.md" "Week 3 Immunity.md"
```

**Everything waiting in `Source Material/`:**
```
uv run make_cards.py --all
```

**Group decks under a parent** (recommended — keeps Anki tidy):
```
uv run make_cards.py --all --deck "Anatomy S2"
```
That produces `Anatomy S2::Week 2 Gas Exchange`, `Anatomy S2::Week 3 Immunity`, and so on.

**With a topic focus file:**
```
uv run make_cards.py "Week 3 - Genetics.pdf" --topic "Topics Requested/krebs-cycle.md"
```

**Topic file only (no source — uses Claude's general knowledge):**
```
uv run make_cards.py --topic "Topics Requested/krebs-cycle.md"
```

**Text only — skip images (faster, lower cost):**
```
uv run make_cards.py "Week 3 - Genetics.pdf" --text-only
```

**Strip copy-protection from a PDF before processing:**
```
uv run make_cards.py --unprotect "locked-lecture.pdf"
```
This saves a clean copy to `Source Material/`.

**Check what's waiting to be processed:**
```
uv run make_cards.py --inbox
```

The finished `.apkg` files land in `Card Decks/`. Double-click one — Anki imports it automatically.

Before calling the API the script prices the whole batch and asks once; afterwards it prints what
each run actually cost. A text-heavy lecture is a few pence; an illustrated PDF chapter runs to
roughly **$0.40–0.50**. Above $1 for the batch it asks you to confirm — pass `-y` to skip that
prompt. If one file fails, the rest still run.

## Using Obsidian notes

**Pass the `.md` file directly — don't export to PDF first.** Exporting loses two things that
matter:

- `==Highlighted==` text, which the script treats as high priority and gives its own cards. PDFs
  carry no highlight information at all, so this is destroyed by the export.
- The link between a diagram and the point in your notes where it appears.

Embedded images (`![[diagram.png]]` or `![](path/diagram.png)`) are resolved by searching your
vault, so attachments stored in a separate folder are found without copying anything. The vault is
located by looking for the `.obsidian` folder above the note.

If an image can't be found, the script says so and carries on rather than failing — check the
vault is reachable from this machine (a synced folder needs to have finished syncing).

## Deck names

Each file becomes its own deck, named after the file. `Week 2 Gas Exchange.md` becomes a deck
called `Week 2 Gas Exchange`, or `Anatomy S2::Week 2 Gas Exchange` with `--deck "Anatomy S2"`.

Names come from the filename rather than being chosen per run, so **re-running a lecture updates
the same deck** instead of creating a near-duplicate beside it. Rename the file and you get a new
deck, so keep filenames stable.

## Customising card style

`STYLE.md` controls **everything** about how cards are written: how many, how lists and processes
are split, which card type is used, and where diagrams go. Read it once before your first real
deck — it's an ordinary text file.

**Put your own changes in `STYLE.local.md`, not in `STYLE.md`.** Copy the template to get started:

```
Copy-Item STYLE.local.example.md STYLE.local.md
```

Then edit `STYLE.local.md` and write only what you want *different* — it's added after the shared
guide, and wins wherever the two disagree. Changes take effect on the next run, and the script
tells you when it's picking the file up.

The reason for the split: `STYLE.md` is shared and gets rewritten by updates, so editing it
directly means `git pull` either overwrites your work or stops with a conflict. `STYLE.local.md`
is ignored by git, so it survives every update untouched.

The things most worth tuning are the **card budget** (currently 20–30 per lecture) and adding a
**worked example** from your own subject — examples shape the output more than rules do.

## Re-running a lecture

Re-running the same file and importing again **updates** existing cards rather than duplicating them —
so you can tweak `STYLE.local.md`, re-run, and your review history is preserved.

The one exception: cards are matched on their *question* text. If Claude rewords a question between
runs, that counts as a new card and the old one stays behind. If you re-run a lecture several times
it's worth checking the deck for strays with Anki's **Browse** window.

## Writing topic request files

Create a `.md` file in `Topics Requested/`. Example:

```markdown
## Deck
Anatomy S2::Krebs Cycle

## Source File
Week 4 - Metabolism.pdf

## Special Emphasis
- The role of acetyl-CoA
- Products per turn of the cycle
- Regulation points
```

`## Special Emphasis` sections get more cards, exam-style phrasing, and an `exam-priority` tag.
If `## Source File` is `(none)`, Claude generates from general knowledge.

## Folder structure

```
anki-cards/
  make_cards.py          <- the main script
  STYLE.md               <- edit this to change card style
  Source Material/       <- drop your PDFs here
  Topics Requested/      <- drop topic .md files here
  Card Decks/            <- finished .apkg files (double-click to import)
  .env                   <- your API key (never committed)
```
