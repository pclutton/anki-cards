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

3. **Add your API key and vault path**

   Copy `.env.example` to `.env`, then fill in both lines:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   OBSIDIAN_VAULT=C:\Users\you\Documents\MyVault
   ```
   Get a key at [console.anthropic.com](https://console.anthropic.com/). The vault path is what
   lets the script find the diagrams your notes refer to — no quotes around it.

The `Source Material/`, `Topics Requested/` and `Card Decks/` folders are created automatically the first time you run the script.

## Daily use

**The normal routine:** drag this week's notes into `Source Material/`, then run:

```
uv run make_cards.py --all --deck "Anatomy S2"
```

Every `.md` and `.pdf` in the folder becomes its own deck — `Anatomy S2::Week 2 Gas Exchange`,
`Anatomy S2::Week 3 Immunity`, and so on. The whole batch is priced once before anything is
spent, and if one file fails the rest still run.

Drag in the **notes only**. Diagrams stay in your vault and are found automatically, provided
`OBSIDIAN_VAULT` is set in `.env` — see [Using Obsidian notes](#using-obsidian-notes). You never
need to copy images anywhere.

**One lecture:**
```
uv run make_cards.py "Week 2 Gas Exchange.md" --deck "Anatomy S2"
```

**Specific files, not the whole folder:**
```
uv run make_cards.py "Week 1 Cells.md" "Week 2 Gas Exchange.md" --deck "Anatomy S2"
```

**Straight from the vault**, without copying anything in, also works:
```
uv run make_cards.py "C:\Users\you\MyVault\Lectures\*.md" --deck "Anatomy S2"
```
(`--all` only looks in `Source Material/`, so use a wildcard for a folder elsewhere.)

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

**Use the `.md` file — don't export to PDF first.** Drag a copy of the note itself into
`Source Material/`. Exporting to PDF loses two things that matter:

- `==Highlighted==` text, which the script treats as high priority and gives its own cards. PDFs
  carry no highlight information at all, so this is destroyed by the export.
- The link between a diagram and the point in your notes where it appears.

### Tell it where your vault is (one-time)

If you drag notes into `Source Material/` — the normal routine — the script needs to know where
your vault is, so it can find the diagrams your notes refer to. Add a second line to `.env`
alongside your API key:

```
ANTHROPIC_API_KEY=sk-ant-...
OBSIDIAN_VAULT=C:\Users\you\Documents\MyVault
```

**No quotes around the path.** `"C:\temp\notes"` in quotes is read as a tab character and
silently stops working. Spaces in the path are fine without quotes.

Do this once and forget it. Without it, your notes still produce cards — but every diagram is
silently missing, which is easy not to notice.

### How images are found

Embedded images (`![[diagram.png]]` or `![](path/diagram.png)`) are looked up by name across your
whole vault, so attachments kept in a separate folder are found without copying anything.

If a note is still *inside* the vault when you run it, the vault is detected automatically from
the `.obsidian` folder and `OBSIDIAN_VAULT` isn't consulted — so the setting is safe to leave on
whichever way you work.

If an image can't be found, the script says so and carries on rather than failing — check the
vault path is right and that a synced folder has finished syncing.

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

A topic request tells Claude what to focus on in a lecture. Create a `.md` file in
`Topics Requested/`:

```markdown
## Special Emphasis
- The role of acetyl-CoA
- Products per turn of the cycle
- Regulation points
```

`## Special Emphasis` sections get more cards, exam-style phrasing, and an `exam-priority` tag.

**Name it after the source file and it's picked up automatically.** A topic request called
`Week 4 Metabolism.md` is applied to `Week 4 Metabolism.md` (or `.pdf`) without you doing
anything — so `--all` works even when each lecture has its own focus:

```
uv run make_cards.py --all --deck "Anatomy S2"
```

`--inbox` shows you which sources have a topic request paired, and which requests have no
matching source.

To apply one topic file to *every* file in a run instead, pass it explicitly — this overrides
any paired files:

```
uv run make_cards.py --all --topic "exam-revision.md"
```

A topic file on its own, with no source, generates cards from Claude's general knowledge.

## Folder structure

```
anki-cards/
  make_cards.py          <- the main script
  STYLE.md               <- the shared style guide (don't edit; updates overwrite it)
  STYLE.local.md         <- your own tweaks go here (never committed)
  Source Material/       <- notes or PDFs, if you don't point at your vault
  Topics Requested/      <- topic .md files; name one after a source to pair it
  Card Decks/            <- finished .apkg files (double-click to import)
  .env                   <- your API key, and optionally OBSIDIAN_VAULT
```
