# Anki Card Style Guide

*This file controls how your flashcards are written. Edit it freely — changes take
effect on the next run. Everything about card quality is decided here.*

---

## The one rule that matters

**One recallable fact per card.**

Before writing a card, apply this test: *could this be graded right or wrong in a
single judgement?* If answering it correctly requires recalling two independent
facts, it is two cards.

A card you cannot honestly mark right or wrong is worse than no card, because it
trains the habit of half-remembering and pressing "Good".

Do **not** get around this by compressing several facts into fewer bullets. These
are all the same violation:

- three bullets, each holding three facts
- one bullet with facts separated by semicolons
- a comma-separated list inside a single bullet

The count of bullets is not the point. The count of *things to remember* is.

## How many cards

Aim for **2–3 cards per slide or major heading**. A 40-page lecture or textbook
chapter should produce roughly **90–120 cards**.

Prefer many small cards over a few dense ones. If you find yourself writing a
long answer, that is the signal to split, not to summarise harder.

## Handling lists

Lists are where card quality usually collapses. Never answer a list question with
a bulleted dump.

Instead write **one Cloze note with one deletion per item**. Anki turns that into
one card per item automatically, each showing the remaining items as context — so
a nine-item list becomes nine answerable cards from a single note.

Use `{{c1::…}}`, `{{c2::…}}`, `{{c3::…}}` and so on, numbering each item separately.
Reuse the same number only when two items should be hidden together.

## Choosing a card type

- **Cloze** — definitions, facts in context, and every list (see above)
- **Basic** — processes, explanations, comparisons, "why" questions
- **Basic (and reversed card)** — key vocabulary only, where recognising the term
  *and* producing it from the definition are both worth testing

Do not use reversed cards for anything whose definition is a full sentence of
prose — going backwards from a paragraph to a single word is not a fair test.

## Diagrams

If a question refers to a diagram in any way — "label", "identify", "shown here",
"in this image" — the `<img>` tag **must be in the question field**. A diagram
that only appears after the flip cannot be attempted, which makes the card
worthless as a labelling exercise.

Put an image on the answer side only to *confirm* something the student was
expected to recall from text alone.

Most cards should have no image at all. Use one where the visual is genuinely
what is being learned: anatomical structures, metabolic cycles, apparatus.

## Answer style

- Plain English first, technical term second
- Concrete example or analogy where it helps
- Include a mnemonic where one exists or can be invented
- Give the Latin/Greek root for new biological terms
- No long paragraphs — a paragraph means you should have split the card

## What to emphasise

- Exam-style phrasing, past-paper style where possible
- Anything flagged as "this will be in the exam"
- Common misconceptions, stated explicitly as misconceptions

## What to skip

- Trivial definitions already covered in earlier decks
- Anything marked `[SKIP]` in the source material

## Tagging

Tag every card by difficulty: `easy`, `medium`, or `hard`.
Tag exam-priority material `exam-priority`.

---

# Worked examples

These are real cards from a generated deck, with what was wrong and what to do
instead. Follow the patterns on the right.

### Example 1 — a list dumped into one card

**Bad.** Ten separate properties behind a single question. There is no way to
mark this right or wrong.

> **Q:** List the basic properties shared by all cells.
> **A:** • Highly complex & organised; possess and use a genetic program
> • Reproduce; acquire and use energy; carry out chemical reactions
> • Engage in mechanical activity, respond to stimuli, self-regulate, evolve

**Good.** One Cloze note, one deletion per property. Anki generates a separate
card for each, and each is gradeable.

> **Cloze:** All cells are highly {{c1::complex and organised}}, possess a
> {{c2::genetic program}} and act on it, are capable of {{c3::reproduction}},
> {{c4::acquire and use energy}}, carry out {{c5::chemical reactions}}, engage in
> {{c6::mechanical activities}}, are able to {{c7::respond to stimuli}},
> {{c8::self-regulate}}, and {{c9::evolve}}.

### Example 2 — a labelling question with no diagram to label

**Bad.** The diagram is on the answer, so the student sees only text and cannot
attempt the task.

> **Q:** Label the parts of a prokaryotic (bacterial) cell.
> **A:** Capsule, cell wall, plasma membrane, cytoplasm, ribosomes, DNA of
> nucleoid, pilus, bacterial flagellum `<img src="img012.jpg">`

**Good.** Image in the question, and ask for something specific rather than
everything at once.

> **Q:** `<img src="img012.jpg">` This bacterial cell has a protective outer layer
> external to the cell wall. Name it.
> **A:** The capsule

> **Q:** `<img src="img012.jpg">` Where in this cell is the DNA located, and what
> is that region called?
> **A:** Free in the cytoplasm, in a region called the **nucleoid** — it is not
> enclosed by a membrane.

### Example 3 — items crammed to satisfy a formatting rule

**Bad.** Six organisms behind one question, packed into two bullets.

> **Q:** Name the six classic model organisms of cell biology.
> **A:** • E. coli (bacterium), Saccharomyces (yeast), Arabidopsis (mustard plant)
> • C. elegans (nematode), Drosophila (fruit fly), Mus musculus (mouse)

**Good.** A Cloze note for the set, so each organism is tested individually.

> **Cloze:** The classic model organisms are {{c1::E. coli}} (bacterium),
> {{c2::Saccharomyces cerevisiae}} (yeast), {{c3::Arabidopsis thaliana}} (mustard
> plant), {{c4::C. elegans}} (nematode), {{c5::Drosophila melanogaster}} (fruit
> fly) and {{c6::Mus musculus}} (mouse).

Then, where the source explains *why* an organism is used, add a Basic card for
it — that is a separate fact and deserves its own card:

> **Q:** Why is *C. elegans* useful for studying development?
> **A:** Its cell lineage is completely mapped — every one of its ~1000 somatic
> cells can be traced from the fertilised egg.

---

## Topic request files

Written in `Topics Requested/` as plain `.md` files.

- Treat `## Special Emphasis` as high priority — generate more cards on these
  topics, use past-paper phrasing, and tag them `exam-priority`
- If a `## Source File` is named, use it as the primary source
- If `## Source File` is `(none)`, generate from general knowledge

---
*The deck name is derived from each source document, so there is no fixed deck list to maintain here.*
