"""Render a data-driven contact sheet from credited, unaltered game previews."""

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site/dist"


def main():
    catalog = json.loads((ROOT / "docs/catalog.json").read_text())
    valid = sum(card["status"] == "runnable" for card in catalog)
    columns, width, gap, margin = 9, 2400, 12, 48
    cell_width = (width - margin * 2 - gap * (columns - 1)) // columns
    picture_height, label_height = 130, 64
    cell_height = picture_height + label_height
    rows = math.ceil(len(catalog) / columns)
    height = 170 + rows * (cell_height + gap) + 60
    canvas = Image.new("RGB", (width, height), "#edeef0")
    draw = ImageDraw.Draw(canvas)
    title_font = ImageFont.load_default(size=46)
    meta_font = ImageFont.load_default(size=19)
    label_font = ImageFont.load_default(size=15)
    note_font = ImageFont.load_default(size=14)
    draw.rectangle((0, 0, width, 5), fill="#ff571c")
    draw.text((margin, 35), "GENERALGAMEBENCH", font=title_font, fill="#141516")
    draw.text(
        (margin, 102),
        "INTELLIGENCE THROUGH PLAY / ENVIRONMENT CATALOG",
        font=meta_font,
        fill="#63686d",
    )
    draw.text(
        (width - margin, 45),
        f"{len(catalog)} ENVIRONMENTS & FAMILIES",
        anchor="ra",
        font=meta_font,
        fill="#141516",
    )
    draw.text(
        (width - margin, 88),
        f"{valid} VALIDATED CARDS / {len(catalog) - valid} UNADMITTED",
        anchor="ra",
        font=meta_font,
        fill="#63686d",
    )
    for index, card in enumerate(catalog):
        x = margin + (index % columns) * (cell_width + gap)
        y = 160 + (index // columns) * (cell_height + gap)
        # Contain instead of crop: every preview retains its original framing.
        with Image.open(SITE / card["image"]) as source:
            preview = ImageOps.contain(source.convert("RGB"), (cell_width, picture_height))
        draw.rectangle((x, y, x + cell_width, y + picture_height), fill="#141516")
        canvas.paste(
            preview,
            (x + (cell_width - preview.width) // 2, y + (picture_height - preview.height) // 2),
        )
        draw.rectangle(
            (x, y + picture_height, x + cell_width, y + cell_height),
            fill="#ff571c" if card["status"] == "runnable" else "#d8dadd",
        )
        name = card["name"].replace("Procgen / ", "Procgen: ")
        lines, line = [], ""
        for word in name.split():
            proposal = f"{line} {word}".strip()
            if draw.textlength(proposal, font=label_font) > cell_width - 20:
                lines.append(line)
                line = word
            else:
                line = proposal
        lines.append(line)
        for offset, line in enumerate(lines):
            draw.text(
                (x + 10, y + picture_height + 8 + offset * 18),
                line,
                font=label_font,
                fill="#141516",
            )
    draw.text(
        (margin, height - 35),
        "Orange: validated card with at least one task. Gray: unadmitted. Credited previews may show other modes. Sources: docs/MEDIA.md",
        font=note_font,
        fill="#63686d",
    )
    target = SITE / "media/environment-atlas.png"
    canvas.save(target, optimize=True)
    print(f"Rendered {len(catalog)} cards, {valid} validated: {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
