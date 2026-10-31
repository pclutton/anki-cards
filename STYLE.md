# Anki Card Style Guide

*This file controls how your flashcards are written. Edit it freely — changes take
effect on the next run. Everything about card quality is decided here.*

---

## How many cards

**20–30 cards per lecture. This is a hard budget, not a target to exceed.**

Two lectures a week at this rate is a sustainable review load. A hundred cards
from one lecture is not — it gets abandoned, and abandoned cards teach nothing.

Count **cards, not notes**. They are not the same thing:

| Note type | Cards produced |
|---|---|
| Basic | 1 |
| Basic (and reversed card) | **2** |
| Cloze with `c1`…`c5` | **5** |
| Cloze where every deletion is `c1` | **1** |

A cloze note with five separate deletion numbers costs five cards against the
budget. Budget in cards.

If the material will not fit in 30 cards, do not spill over. Choose what matters
most using the priority order at the bottom of this file.

## The core rule

**A card must require recall. If it can be answered by reasoning from what is
already on the card, it teaches nothing.**

Before writing a card, ask: *could someone who has never seen this material get
it right anyway?* If yes, the card is broken, however well-formatted it is.

The common ways this goes wrong:

- **Answer by elimination.** "The vessel is not small, so it must be large."
  If only two options exist and the card reveals one, the other is free.
- **Answer visible in the question.** Asking "which is the *largest* chamber?"
  when the answer is simply the thing described as largest.
- **Answer given by grammar or phrasing.** A blank that only one word fits
  grammatically.
- **Answer legible in the image.** See *Diagrams* below.

When contrasting two things, hide **both** sides with the same cloze number, or
ask for the distinction as a Basic question. Never leave one half visible as a
free hint.

## Lists

**A list is one card.** Five items do not become five cards.

Ask for the whole list in one question, and accept it as one recall:

> **Q:** What are the five requirements for efficient gas exchange?
> **A:** Large partial-pressure difference • short exchange distance • O₂ and
> CO₂ lipid-soluble • large surface area • airflow and blood flow coordinated

If you prefer cloze for a list, **give every item the same number** (`c1`), so
Anki hides them together and produces a single card:

> `The gas exchange requirements are {{c1::a large PP difference}},
> {{c1::short distances}}, {{c1::lipid solubility}}, {{c1::large surface area}}
> and {{c1::coordinated flow}}.`

Only split a list across cards when it is genuinely long (more than about eight
items) *and* the items are examined separately. Then group them logically into
two cards — never one card per item.

## Processes, cycles and flow diagrams

These are common in lecture material and are the fastest way to blow the budget.

**A process is one card.** Ask for the sequence as a whole:

> **Q:** Trace blood flow through the right side of the heart.
> **A:** Vena cava → right atrium → tricuspid valve → right ventricle →
> pulmonary valve → pulmonary artery

Do not make one card per step. Do not make a card for every arrow in a cycle
diagram. A second card is justified only where a specific step carries its own
examinable fact — for example *why* the AV node delay exists — and that is a
different question, not a step in the sequence.

## Definitions

**Each definition gets its own card.** Definitions are the backbone of the
subject and are worth their budget.

The exception: two definitions that are only meaningful as a pair — terms that
are defined against each other — belong on one card.

> **Q:** Systole vs diastole?
> **A:** Systole = cardiac muscle contracting. Diastole = relaxing.
> (Mnemonic: **S**ystole = **S**queeze)

Use **Basic (and reversed card)** only for short, single-term vocabulary where
producing the term from its definition is genuinely useful. Remember it costs
two cards.

## Diagrams

A diagram belongs on the **question** side when the student must work something
out from it — identifying a structure an arrow points to, reading a trace,
interpreting a result.

**Before using an image on the question side, check whether it contains the
answer.** If the structures are labelled, or the formula is written on the
image, then showing it gives the answer away. Asking "what is this formula?"
above an image of the formula is not a flashcard.

When the image is self-answering, do one of:

- ask about something the image does *not* spell out (a mechanism, a
  consequence, why it is so)
- put the image on the **answer** side, as confirmation of something recalled
  from text
- leave the image out

Most cards need no image at all.

## Highlighted text (Obsidian notes)

When the source is Obsidian markdown, `==highlighted text==` marks what the
student thought important while writing the notes.

**Treat highlighted text and the content attached to it as warranting its own
card**, ahead of surrounding unhighlighted material. Tag these `highlighted`.

*Note: this only works when the source file is markdown (`.md`). Highlight
colour is lost when notes are exported to PDF, so export notes as markdown to
get the benefit.*

## Answer style

- Plain English first, technical term second
- Short — a paragraph means the card is doing too much
- Concrete example or analogy where it genuinely helps
- Include a mnemonic where one exists or can be invented
- Give the Latin/Greek root for new biological terms

## Tagging

Tag every card by difficulty: `easy`, `medium`, `hard`.
Tag exam-flagged material `exam-priority`, and highlighted material `highlighted`.

## What to skip

- Trivial definitions already covered in earlier decks
- Anything marked `[SKIP]` in the source
- Housekeeping slides: titles, aims, references, "any questions?"

## Priority order when the budget is tight

Work down this list and stop at 30 cards:

1. `==Highlighted==` content — the student marked it themselves
2. Definitions of new terms
3. Anything flagged as examinable, or phrased as a past-paper question
4. Processes and cycles — one card each
5. Comparisons and distinctions
6. Supporting detail and examples

Prefer one broader card covering a topic over dropping that topic entirely.

---

# Worked examples

### 1 — A list is one card

**Bad.** Five items split into five separate deletions, costing five cards.

> `The classic model organisms are {{c1::E. coli}}, {{c2::yeast}},
> {{c3::Arabidopsis}}, {{c4::C. elegans}} and {{c5::Drosophila}}.`

**Good.** One card, one recall.

> **Q:** Name the five classic model organisms of cell biology.
> **A:** *E. coli* • yeast (*S. cerevisiae*) • *Arabidopsis* • *C. elegans* •
> *Drosophila*

### 2 — The answer must not be inferable

**Bad.** The card states veins are the low-pressure side, so "higher" is free.

> `Pressure is {{c1::higher}} in arteries than in veins, which are the
> low-pressure side of the circulation.`

**Good.** Both sides hidden together, so the contrast must actually be known.

> `Pressure is {{c1::higher}} in arteries and {{c1::lower}} in veins.`

Or as a Basic card that demands the reasoning:

> **Q:** Why is the left ventricle wall thicker than the right?
> **A:** It pumps into the systemic circuit at 80–100 mmHg, against the right
> ventricle's <15 mmHg into the pulmonary circuit — roughly 4–6× the pressure.

### 3 — Do not ask what the image already answers

**Bad.** The formula is printed in the image shown on the question side.

> **Q:** `<img src="img004.jpg">` What is Henry's Law?

**Good.** Ask for something the image does not state.

> **Q:** `<img src="img004.jpg">` Henry's Law is shown here. What does it predict
> happens to dissolved gas when partial pressure rises at constant temperature?
> **A:** More gas dissolves — the amount in solution is proportional to the
> partial pressure of that gas.

### 4 — A process is one card, not one per step

**Bad.** Four cards for one sequence.

> Four separate cards asking for step 1, step 2, step 3 and step 4 of the
> electrical conduction pathway.

**Good.**

> **Q:** Describe the heart's electrical conduction pathway in order.
> **A:** SA node → AV node (100 ms delay) → AV bundle (His) → Purkinje fibres

Then, only if it is examinable in its own right:

> **Q:** Why does the AV node delay the impulse by ~100 ms?
> **A:** It lets the atria empty fully into the ventricles before ventricular
> systole, maximising stroke volume.

---

## Topic request files

Written in `Topics Requested/` as plain `.md` files.

- Treat `## Special Emphasis` as high priority — more cards on these topics,
  past-paper phrasing, tagged `exam-priority`
- If a `## Source File` is named, use it as the primary source
- If `## Source File` is `(none)`, generate from general knowledge

---
*The deck name is derived from each source document, so there is no fixed deck list to maintain here.*
