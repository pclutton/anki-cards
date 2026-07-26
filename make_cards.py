#!/usr/bin/env python3
"""Generate Anki cards from PDFs using the Claude API."""

import argparse
import base64
import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import date
from pathlib import Path

import fitz  # PyMuPDF
import genanki
import pymupdf4llm
from anthropic import Anthropic, APIError
from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).parent
STYLE_PATH = SCRIPT_DIR / "STYLE.md"
SOURCE_DIR = SCRIPT_DIR / "Source Material"
TOPICS_DIR = SCRIPT_DIR / "Topics Requested"
OUTPUT_DIR = SCRIPT_DIR / "Card Decks"

MODEL = "claude-opus-5"
MAX_TOKENS = 32000

# Claude accepts up to 100 images per request; stay well under
MAX_IMAGES = 50
# Skip images smaller than this in either dimension (logos, bullets, rules)
MIN_IMAGE_PX = 150
# Claude's vision models cap effective resolution around this; anything
# bigger costs bytes and request-size budget without adding quality
MAX_IMAGE_DIM = 1568

# claude-opus-5 pricing, USD per million tokens. Output is 5x input, which is
# why an input-only estimate is badly misleading for a card-generating run.
INPUT_COST_PER_MTOK = 5.00
OUTPUT_COST_PER_MTOK = 25.00
# Above this estimated cost, ask before spending
COST_CONFIRM_THRESHOLD = 1.00

# Measured against a real 43-page textbook chapter using the free
# count_tokens endpoint: 42 cards came to ~5,275 tokens of JSON (~126 each)
# from ~9,435 input tokens of source text (~one card per 225 text tokens).
OUTPUT_TOKENS_PER_CARD = 126
# Cards scale with how much *reading* there is, not how many pictures. Image
# tokens must stay out of this: a chapter's 48k image tokens would otherwise
# predict a 200-card deck from a 42-card lecture.
TEXT_TOKENS_PER_CARD = 225
# Adaptive thinking is billed as output on top of the visible JSON. Reconciled
# against a real account total of $0.67 across six calls, thinking added only
# about 10% for this task — well below the 20-200% first assumed. Kept as a
# band because a denser lecture may reason more; the actual figure printed
# after every run is the number to trust over this.
THINKING_FACTOR_LOW = 1.0
THINKING_FACTOR_HIGH = 1.6

# Anki's built-in note types, via genanki's canonical definitions. Do not
# hand-roll these: a mismatched model ID makes Anki fork the note type on
# import (creating "Basic-a1b2c" alongside the real one).
MODELS = {
    "Basic": genanki.BASIC_MODEL,
    "Cloze": genanki.CLOZE_MODEL,
    "Basic (and reversed card)": genanki.BASIC_AND_REVERSED_CARD_MODEL,
}

IMG_SRC_RE = re.compile(r'<img\s[^>]*src\s*=\s*["\']([^"\']+)["\']', re.I)


def ensure_dirs() -> None:
    for d in (SOURCE_DIR, TOPICS_DIR, OUTPUT_DIR):
        d.mkdir(exist_ok=True)


def deck_id_for(deck_name: str) -> int:
    """Stable integer deck ID so re-imports merge into the same deck."""
    digest = hashlib.sha256(deck_name.encode("utf-8")).hexdigest()
    # Anki deck IDs are positive; keep well inside a 63-bit range
    return int(digest[:12], 16)


def question_of(card: dict) -> str:
    """The field that identifies a card across runs."""
    return card["text"] if card["model"] == "Cloze" else card["front"]


def unique_path(path: Path) -> Path:
    """Return a path that does not exist yet, so a deck is never overwritten.

    Two runs of the same source on the same day would otherwise collide on
    {deck}_{date}.apkg and the second would silently destroy the first.
    """
    if not path.exists():
        return path
    n = 2
    while True:
        candidate = path.with_name(f"{path.stem}_{n}{path.suffix}")
        if not candidate.exists():
            return candidate
        n += 1


def flatten_on_white(pix: fitz.Pixmap) -> fitz.Pixmap:
    """Composite a pixmap with an alpha channel onto a white background.

    PDFs keep transparency in a separate soft-mask object, and JPEG cannot
    carry alpha at all. Without this, transparent regions encode as solid
    black — which is exactly what happens to the transparent-background
    diagrams that slide exports are full of, making them unreadable on a card.
    """
    doc = fitz.open()
    page = doc.new_page(width=pix.width, height=pix.height)
    page.draw_rect(page.rect, color=None, fill=(1, 1, 1), overlay=False)
    page.insert_image(page.rect, pixmap=pix)
    flat = page.get_pixmap()
    doc.close()
    return flat


def extract_pdf_text(pdf_path: Path) -> str:
    """Extract PDF text as Markdown, preserving headings, lists and tables."""
    return pymupdf4llm.to_markdown(str(pdf_path))


def extract_pdf_images(pdf_path: Path) -> list[dict]:
    """Extract PDF images as JPEG bytes, deduped and filtered by minimum size.

    JPEG rather than PNG: textbook diagrams are continuous-tone and PNG
    compresses them poorly — a 43-page chapter's worth of images can otherwise
    exceed Claude's per-request size limit (confirmed: 50 images, 39MB as PNG
    vs 6.5MB as JPEG at quality 85, for the same visual content).
    """
    doc = fitz.open(str(pdf_path))
    images: list[dict] = []
    seen_xrefs: set[int] = set()

    for page_num, page in enumerate(doc):
        for img_info in page.get_images(full=True):
            xref, smask_xref = img_info[0], img_info[1]
            if xref in seen_xrefs:
                continue
            seen_xrefs.add(xref)
            try:
                pix = fitz.Pixmap(doc, xref)
                if pix.width < MIN_IMAGE_PX or pix.height < MIN_IMAGE_PX:
                    continue
                # Convert CMYK and other non-RGB colour spaces before encoding
                if pix.n - pix.alpha > 3:
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                # Re-attach the soft mask and flatten onto white. Extraction
                # returns only the base image, so transparent areas would
                # otherwise come through as black. Do this at native size, so
                # the mask still matches the base image's dimensions.
                if smask_xref:
                    pix = flatten_on_white(fitz.Pixmap(pix, fitz.Pixmap(doc, smask_xref)))
                # Downscale oversized images — Claude gains nothing past
                # MAX_IMAGE_DIM and large originals can blow the request-size limit
                if max(pix.width, pix.height) > MAX_IMAGE_DIM:
                    scale = MAX_IMAGE_DIM / max(pix.width, pix.height)
                    pix = fitz.Pixmap(pix, int(pix.width * scale), int(pix.height * scale))
                images.append({
                    "name": f"img{len(images):03d}.jpg",
                    "data": pix.tobytes("jpg", jpg_quality=85),
                    "page": page_num + 1,
                    "width": pix.width,
                    "height": pix.height,
                })
            except Exception as exc:
                print(f"  Skipped an image on page {page_num + 1}: {exc}", file=sys.stderr)

    if len(images) > MAX_IMAGES:
        print(f"  Note: {len(images)} images found, using the first {MAX_IMAGES}")
        images = images[:MAX_IMAGES]

    return images


def image_tokens(img: dict) -> int:
    """Anthropic's documented approximation for image token cost.

    Validated against count_tokens on a real extracted diagram: predicted
    1088 vs actual 1057 tokens, so within ~3%.
    """
    return int(img["width"] * img["height"] / 750)


def count_input_tokens(
    client: Anthropic,
    pdf_text: str | None,
    topic_text: str | None,
    images: list[dict],
    system_prompt: str,
) -> tuple[int, int]:
    """Exact input token count as (text_tokens, image_tokens).

    count_tokens is free, but sending 50 images to it would mean pushing
    several megabytes twice. The text is counted exactly via the API and the
    images are added with the size formula above. The two are kept separate
    because only the text predicts how many cards come back.
    """
    try:
        text_tokens = client.messages.count_tokens(
            model=MODEL,
            system=system_prompt,
            thinking={"type": "adaptive"},
            messages=[{"role": "user", "content": build_prompt(pdf_text, topic_text, [])}],
        ).input_tokens
    except APIError:
        # Fall back to a rough heuristic rather than failing the whole run
        text_tokens = (len(pdf_text or "") + len(topic_text or "")) // 4
    # Each image also carries its filename label, which is a handful of tokens
    return text_tokens, sum(image_tokens(i) + 15 for i in images)


def estimate_cost(text_tokens: int, img_tokens: int) -> tuple[float, float]:
    """Estimated (low, high) USD for a run, counting output as well as input.

    Output matters more than its token count suggests: it is billed at 5x the
    input rate, so a few thousand tokens of JSON can outweigh a long PDF.
    """
    input_cost = (text_tokens + img_tokens) / 1_000_000 * INPUT_COST_PER_MTOK
    expected_cards = max(10, min(60, text_tokens // TEXT_TOKENS_PER_CARD))
    visible_output = expected_cards * OUTPUT_TOKENS_PER_CARD
    low = input_cost + visible_output * THINKING_FACTOR_LOW / 1_000_000 * OUTPUT_COST_PER_MTOK
    high = input_cost + visible_output * THINKING_FACTOR_HIGH / 1_000_000 * OUTPUT_COST_PER_MTOK
    return low, high


def actual_cost(usage) -> float:
    """Real USD for a completed call, from the API's own token counts."""
    return (
        usage.input_tokens / 1_000_000 * INPUT_COST_PER_MTOK
        + usage.output_tokens / 1_000_000 * OUTPUT_COST_PER_MTOK
    )


def build_prompt(pdf_text: str | None, topic_text: str | None, images: list[dict]) -> list[dict]:
    text_parts = []
    if pdf_text:
        text_parts.append(f"<source_material>\n{pdf_text}\n</source_material>")
    if topic_text:
        text_parts.append(f"<topic_request>\n{topic_text}\n</topic_request>")

    instruction = (
        "Generate Anki flashcards from the material above.\n\n"
        "Return ONLY a JSON object — no prose, no markdown fences — with this exact structure:\n"
        "{\n"
        '  "deck": "Subject::Topic",\n'
        '  "tags": ["tag1", "tag2"],\n'
        '  "cards": [\n'
        '    {"model": "Basic", "front": "Question?", "back": "Answer", "tags": ["easy"]},\n'
        '    {"model": "Cloze", "text": "The {{c1::answer}} is here.", "back_extra": "Optional note", "tags": ["medium"]},\n'
        '    {"model": "Basic (and reversed card)", "front": "Term", "back": "Definition", "tags": ["hard"]}\n'
        "  ]\n"
        "}\n\n"
        "Rules:\n"
        '- model must be exactly "Basic", "Cloze", or "Basic (and reversed card)"\n'
        '- Basic and Basic (and reversed card) cards require "front" and "back"\n'
        '- Cloze cards require "text" (with {{c1::...}} syntax) and optional "back_extra"\n'
        "- Output raw JSON only — no text before or after the object"
    )
    if images:
        instruction += (
            "\n- Lecture diagrams are attached below. Each is preceded by a line giving its "
            'exact filename. To show a diagram on a card, embed it as <img src="FILENAME"> '
            "using that exact filename — do not invent or alter filenames.\n"
            "- Only use a diagram where seeing it genuinely aids recall (metabolic cycles, "
            "anatomical structures). Most cards should have no image."
        )

    text_parts.append(instruction)
    content: list[dict] = [{"type": "text", "text": "\n\n".join(text_parts)}]

    # Label every image so Claude can map an attachment to the filename that
    # will actually be bundled into the .apkg.
    for img in images:
        content.append({
            "type": "text",
            "text": f"Image filename: {img['name']} (from page {img['page']})",
        })
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": base64.standard_b64encode(img["data"]).decode(),
            },
        })

    return content


def get_client() -> Anthropic:
    """Build the API client, failing early and clearly if no key is set."""
    load_dotenv()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "Error: no API key found.\n"
            "  Copy .env.example to .env and add your key from https://console.anthropic.com/",
            file=sys.stderr,
        )
        sys.exit(1)
    return Anthropic()


def system_prompt() -> str:
    style = STYLE_PATH.read_text(encoding="utf-8") if STYLE_PATH.exists() else ""
    return style or "You are an expert at creating Anki flashcards."


def generate_cards(
    client: Anthropic,
    pdf_text: str | None,
    topic_text: str | None,
    images: list[dict],
) -> dict:
    print("Calling Claude (this can take a minute)...", flush=True)
    try:
        with client.messages.stream(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            thinking={"type": "adaptive"},
            system=system_prompt(),
            messages=[{"role": "user", "content": build_prompt(pdf_text, topic_text, images)}],
        ) as stream:
            response = stream.get_final_message()
    except APIError as exc:
        print(f"Error: the Claude API call failed — {exc}", file=sys.stderr)
        sys.exit(1)

    # Report what the run really cost, so the estimate above can be sanity
    # checked against reality rather than trusted blindly.
    usage = response.usage
    print(
        f"  Actual cost: ${actual_cost(usage):.2f} "
        f"({usage.input_tokens:,} in + {usage.output_tokens:,} out)"
    )

    if response.stop_reason == "max_tokens":
        print(
            "Error: Claude ran out of room before finishing the card list.\n"
            "  The lecture is likely too long for one pass. Split the PDF and run each part,\n"
            "  or use --text-only to leave more budget for the cards.",
            file=sys.stderr,
        )
        sys.exit(1)

    text = "".join(b.text for b in response.content if b.type == "text").strip()

    # Strip markdown code fences if Claude wrapped the JSON anyway
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines[1:])

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        dump = OUTPUT_DIR / "last_failed_response.txt"
        OUTPUT_DIR.mkdir(exist_ok=True)
        dump.write_text(text, encoding="utf-8")
        print(
            f"Error: Claude's response was not valid JSON ({exc}).\n"
            f"  The raw response was saved to {dump} so nothing is lost.\n"
            "  Re-running usually fixes this.",
            file=sys.stderr,
        )
        sys.exit(1)


def validate_cards(card_data: dict) -> list[dict]:
    """Drop malformed cards with a warning rather than losing the whole run."""
    valid = []
    for i, card in enumerate(card_data.get("cards", [])):
        if not isinstance(card, dict):
            print(f"  Skipping card {i + 1}: not an object", file=sys.stderr)
            continue
        model_name = card.get("model")
        if model_name not in MODELS:
            print(f"  Skipping card {i + 1}: unknown model {model_name!r}", file=sys.stderr)
            continue
        required = ("text",) if model_name == "Cloze" else ("front", "back")
        missing = [f for f in required if not card.get(f)]
        if missing:
            print(f"  Skipping card {i + 1}: missing {', '.join(missing)}", file=sys.stderr)
            continue
        valid.append(card)
    return valid


def build_apkg(
    card_data: dict,
    cards: list[dict],
    output_path: Path,
    images_by_name: dict[str, Path],
) -> None:
    deck_name = card_data["deck"]
    deck = genanki.Deck(deck_id_for(deck_name), deck_name)
    deck_tags = card_data.get("tags", [])
    used_media: set[str] = set()
    broken_refs: set[str] = set()

    for card in cards:
        model_name = card["model"]
        if model_name == "Cloze":
            fields = [card["text"], card.get("back_extra", "")]
        else:
            fields = [card["front"], card["back"]]

        # Only bundle images the cards actually reference, and drop references
        # to files that do not exist rather than shipping broken <img> tags.
        for idx, field in enumerate(fields):
            for ref in IMG_SRC_RE.findall(field):
                if ref in images_by_name:
                    used_media.add(ref)
                else:
                    broken_refs.add(ref)
                    fields[idx] = IMG_SRC_RE.sub(
                        lambda m: "" if m.group(1) == ref else m.group(0), fields[idx]
                    )

        # Stable GUID keyed on the question only, so editing an answer and
        # re-importing updates the existing card instead of duplicating it.
        note = genanki.Note(
            model=MODELS[model_name],
            fields=fields,
            tags=deck_tags + card.get("tags", []),
            guid=genanki.guid_for(deck_name, question_of(card)),
        )
        deck.add_note(note)

    if broken_refs:
        print(
            f"  Warning: removed {len(broken_refs)} image reference(s) to missing files: "
            f"{', '.join(sorted(broken_refs))}",
            file=sys.stderr,
        )

    OUTPUT_DIR.mkdir(exist_ok=True)
    package = genanki.Package(deck)
    package.media_files = [str(images_by_name[n]) for n in sorted(used_media)]
    package.write_to_file(str(output_path))

    print(f"  {len(cards)} cards, {len(used_media)} image(s) bundled")


def cmd_inbox() -> None:
    ensure_dirs()
    print("=== Source Material ===")
    files = sorted(f for f in SOURCE_DIR.iterdir() if f.is_file() and not f.name.startswith("."))
    for f in files:
        print(f"  {f.name}")
    if not files:
        print("  (empty — drop your PDFs here)")

    print("\n=== Topics Requested ===")
    topics = sorted(TOPICS_DIR.glob("*.md"))
    for f in topics:
        print(f"  {f.name}")
    if not topics:
        print("  (empty — drop topic request .md files here)")


def cmd_unprotect(pdf_path: Path) -> None:
    if not pdf_path.exists():
        candidate = SOURCE_DIR / pdf_path.name
        if not candidate.exists():
            print(f"Error: {pdf_path} not found", file=sys.stderr)
            sys.exit(1)
        pdf_path = candidate

    ensure_dirs()
    doc = fitz.open(str(pdf_path))
    if doc.needs_pass:
        print(
            f"Error: '{pdf_path.name}' needs a password to open.\n"
            "  Open it in a PDF reader with the password, save an unlocked copy,\n"
            "  and put that copy in Source Material/.",
            file=sys.stderr,
        )
        sys.exit(1)

    out_path = SOURCE_DIR / pdf_path.name
    if out_path.resolve() == pdf_path.resolve():
        out_path = SOURCE_DIR / f"{pdf_path.stem}_unprotected.pdf"
    doc.save(str(out_path), encryption=fitz.PDF_ENCRYPT_NONE)
    print(f"Saved unprotected PDF to {out_path}")


def cmd_generate(
    pdf_path: Path | None,
    topic_path: Path | None,
    include_images: bool,
    assume_yes: bool,
) -> None:
    ensure_dirs()
    # Check the key before doing any slow extraction work, so a missing key
    # is reported immediately rather than after parsing a 40-page PDF.
    client = get_client()

    pdf_text = None
    topic_text = None
    images: list[dict] = []

    if pdf_path:
        print(f"Reading {pdf_path.name}...")
        pdf_text = extract_pdf_text(pdf_path)
        if include_images:
            images = extract_pdf_images(pdf_path)
            print(f"  {len(images)} usable image(s) found")

    if topic_path:
        print(f"Reading {topic_path.name}...")
        topic_text = topic_path.read_text(encoding="utf-8")

    text_tokens, img_tokens = count_input_tokens(
        client, pdf_text, topic_text, images, system_prompt()
    )
    low, high = estimate_cost(text_tokens, img_tokens)
    detail = f"{text_tokens:,} text"
    if img_tokens:
        detail += f" + {img_tokens:,} image"
    print(f"Estimated cost: ${low:.2f}–${high:.2f}  ({detail} tokens in)")
    # Gate on the upper bound: better to over-warn than to overspend silently.
    if high > COST_CONFIRM_THRESHOLD and not assume_yes:
        if input("  Continue? [y/N] ").strip().lower() not in ("y", "yes"):
            print("Cancelled.")
            return

    with tempfile.TemporaryDirectory() as tmp:
        media_dir = Path(tmp)
        images_by_name = {}
        for img in images:
            path = media_dir / img["name"]
            path.write_bytes(img["data"])
            images_by_name[img["name"]] = path

        card_data = generate_cards(client, pdf_text, topic_text, images)

        deck_name = card_data.get("deck") or "Anki::Cards"
        card_data["deck"] = deck_name
        cards = validate_cards(card_data)
        if not cards:
            print("Error: Claude returned no usable cards.", file=sys.stderr)
            sys.exit(1)

        safe_name = re.sub(r"[^\w.-]+", "_", deck_name.replace("::", "_"))
        output_path = unique_path(OUTPUT_DIR / f"{safe_name}_{date.today().isoformat()}.apkg")

        print(f"Building '{deck_name}'...")
        build_apkg(card_data, cards, output_path, images_by_name)

    print(f"Saved: {output_path.relative_to(SCRIPT_DIR)}")
    print("Double-click that file to import it into Anki.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Anki cards from PDFs via the Claude API")
    parser.add_argument("pdf", nargs="?", help="PDF to process (or a filename inside Source Material/)")
    parser.add_argument("--topic", metavar="FILE", help="Topic request .md file (or a filename inside Topics Requested/)")
    parser.add_argument("--unprotect", metavar="PDF", help="Strip copy-protection and save to Source Material/")
    parser.add_argument("--inbox", action="store_true", help="Show inbox contents and exit")
    parser.add_argument("--text-only", action="store_true", help="Skip images (faster and cheaper)")
    parser.add_argument("-y", "--yes", action="store_true", help="Skip the cost confirmation prompt")
    args = parser.parse_args()

    if args.inbox:
        cmd_inbox()
        return

    if args.unprotect:
        cmd_unprotect(Path(args.unprotect))
        return

    if not args.pdf and not args.topic:
        parser.print_help()
        sys.exit(1)

    def resolve(value: str, fallback_dir: Path, label: str) -> Path:
        p = Path(value)
        if not p.exists():
            p = fallback_dir / Path(value).name
        if not p.exists():
            print(f"Error: '{value}' not found (also checked {label}/)", file=sys.stderr)
            sys.exit(1)
        return p

    ensure_dirs()
    pdf_path = resolve(args.pdf, SOURCE_DIR, "Source Material") if args.pdf else None
    topic_path = resolve(args.topic, TOPICS_DIR, "Topics Requested") if args.topic else None

    cmd_generate(pdf_path, topic_path, include_images=not args.text_only, assume_yes=args.yes)


if __name__ == "__main__":
    main()
