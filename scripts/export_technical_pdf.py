from pathlib import Path
import textwrap

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "docs" / "technical_analysis.md"
OUTPUT = ROOT / "docs" / "technical_analysis.pdf"
FIGURES_DIR = ROOT / "docs" / "figures"


def load_font(size: int):
    candidates = [
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/calibri.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def render_pdf(source: Path = SOURCE, output: Path = OUTPUT) -> Path:
    text = source.read_text(encoding="utf-8")
    regular = load_font(28)
    heading = load_font(38)
    small = load_font(22)

    page_width, page_height = 1240, 1754
    margin = 90
    line_height = 40
    pages = []
    image = Image.new("RGB", (page_width, page_height), "white")
    draw = ImageDraw.Draw(image)
    y = margin

    def new_page():
        nonlocal image, draw, y
        pages.append(image)
        image = Image.new("RGB", (page_width, page_height), "white")
        draw = ImageDraw.Draw(image)
        y = margin

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            y += line_height // 2
            continue

        is_heading = line.startswith("#")
        font = heading if is_heading else small if line.startswith("|") else regular
        clean = line.lstrip("#").strip()
        width = 48 if is_heading else 72 if not line.startswith("|") else 90

        for wrapped in textwrap.wrap(clean, width=width) or [""]:
            if y > page_height - margin:
                new_page()
            draw.text((margin, y), wrapped, fill=(29, 37, 35), font=font)
            y += 54 if is_heading else line_height

    pages.append(image)

    for figure in sorted(FIGURES_DIR.glob("*.png")):
        figure_image = Image.open(figure).convert("RGB")
        page = Image.new("RGB", (page_width, page_height), "white")
        page_draw = ImageDraw.Draw(page)
        page_draw.text((margin, margin), figure.stem.replace("_", " ").title(), fill=(29, 37, 35), font=heading)

        max_width = page_width - margin * 2
        max_height = page_height - margin * 3
        figure_image.thumbnail((max_width, max_height))
        x = (page_width - figure_image.width) // 2
        y = margin + 90
        page.paste(figure_image, (x, y))
        pages.append(page)

    output.parent.mkdir(parents=True, exist_ok=True)
    first, *rest = pages
    first.save(output, "PDF", resolution=150.0, save_all=True, append_images=rest)
    return output


if __name__ == "__main__":
    print(render_pdf())
