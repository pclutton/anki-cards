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

**Generate cards from a PDF:**
```
uv run make_cards.py "Source Material/Week 3 - Genetics.pdf"
```
Or just the filename if it's already in `Source Material/`:
```
uv run make_cards.py "Week 3 - Genetics.pdf"
```

**With a topic focus file:**
```
uv run make_cards.py "Week 3 - Genetics.pdf" --topic "Topics Requested/krebs-cycle.md"
```

**Topic file only (no PDF — uses Claude's general knowledge):**
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

The finished `.apkg` file lands in `Card Decks/`. Double-click it — Anki imports it automatically.

Before calling the API the script prints an estimated cost, and afterwards the actual cost. A
40-page illustrated chapter runs to roughly **$0.70–0.90**; text-only is much less. Above $1 it
asks you to confirm — pass `-y` to skip that prompt.

## Customising card style

`STYLE.md` controls **everything** about how cards are written: how many, how they're split, which
card type is used, and where diagrams go. It's an ordinary text file — open it in VS Code and edit
it. Changes take effect on the next run.

It's worth reading once before your first real deck. The two things most worth tuning are the
**card count target** (currently ~90–120 per chapter) and the **worked examples** at the bottom —
the examples do more to shape the output than the rules above them, so adding one in your own
subject is the fastest way to improve results.

## Re-running a lecture

Re-running the same PDF and importing again **updates** existing cards rather than duplicating them —
so you can tweak `STYLE.md`, re-run, and your review history is preserved.

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
