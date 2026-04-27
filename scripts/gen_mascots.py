"""One-off: regenerate the Cloudfire woodpecker mascot set via Gemini 3.1.

Runs each prompt sequentially and saves to a deterministic filename in
static/img/. Designed to be re-runnable; existing files get overwritten.
"""

import os
import sys
from pathlib import Path

# Make project root importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gemini_image_gen import generate_image  # noqa: E402

OUT_DIR = Path(__file__).resolve().parent.parent / "static" / "img"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL = "gemini-3.1-flash-image-preview"

# Shared character so every pose looks like the SAME woodpecker.
CHARACTER = (
    "A single chubby kawaii woodpecker mascot. Round cream-yellow body, "
    "tall coral-red mohawk crest, long pointy navy-grey beak, soft lavender "
    "wing tips, big shiny black eyes with white highlights, pink blushed "
    "cheeks, two small orange feet. Sticker style with thick white outline, "
    "flat vector illustration, soft pastel cream background, no text, "
    "no watermark, no logos, single character only, full body in frame."
)

POSES = [
    (
        "art-wave.png",
        f"{CHARACTER} Pose: standing facing forward, smiling, "
        "raising one wing in a friendly wave. Both eyes the same size."
    ),
    (
        "art-paint.png",
        f"{CHARACTER} Pose: standing in three-quarter view, holding a tiny "
        "wooden paintbrush in one wing, looking down at the brush with a "
        "calm focused smile. Exactly two eyes, two wings."
    ),
    (
        "art-peek.png",
        f"{CHARACTER} Pose: peeking curiously around the right edge of the "
        "frame, only the head and one wing visible, big curious eyes wide, "
        "small smile."
    ),
    (
        "art-sleep.png",
        f"{CHARACTER} Pose: standing with closed sleeping eyes, small smile, "
        "head tilted slightly, three small coral 'Z' letters floating above "
        "the head."
    ),
    (
        "art-logo.png",
        f"{CHARACTER} Pose: tightly cropped circular portrait, head and chest "
        "only, facing slightly to the right, gentle smile, eyes open. "
        "Composition centered, suitable as a circular brand logo."
    ),
]


def main():
    if not os.environ.get("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY is not set. Cannot run.")
        sys.exit(1)

    print(f"Generating {len(POSES)} mascots via {MODEL}\n")

    successes = []
    failures = []

    for filename, prompt in POSES:
        target = OUT_DIR / filename
        print(f"\n=== {filename} ===")
        files = generate_image(prompt, output_dir=str(OUT_DIR), model=MODEL)
        if not files:
            print(f"  FAILED: {filename}")
            failures.append(filename)
            continue
        # generate_image saved with a timestamped name; rename to target
        src = Path(files[0])
        if src.exists():
            if target.exists():
                target.unlink()
            src.rename(target)
            print(f"  -> {target}")
            successes.append(filename)
        else:
            failures.append(filename)

    print("\n--- summary ---")
    print(f"OK ({len(successes)}): {successes}")
    if failures:
        print(f"FAILED ({len(failures)}): {failures}")
        sys.exit(2)


if __name__ == "__main__":
    main()
