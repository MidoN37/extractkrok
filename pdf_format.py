import os
import re
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors

FONT_NAME = "DejaVuSans"
FONT_FILE = "DejaVuSans.ttf"

pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_FILE))


def create_styled_pdf(txt_path, pdf_path):
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4

    margin_left = 40
    margin_right = 40
    max_width = width - margin_left - margin_right

    font_size = 10
    line_height = 14
    y = height - 40

    c.setFont(FONT_NAME, font_size)

    with open(txt_path, "r", encoding="utf-8", errors="replace") as f:
        for raw_line in f:
            line = raw_line.strip()

            if not line:
                y -= 6
                continue

            bg_color = None
            text_color = colors.black

            if re.match(r"^\d+\.", line):
                bg_color = colors.lightyellow
            elif line.startswith("*"):
                line = line[1:].strip()
                bg_color = colors.lightgreen
                text_color = colors.darkgreen
            else:
                text_color = colors.darkgrey

            words = line.split()
            current = []
            wrapped = []

            for w in words:
                test = " ".join(current + [w])
                if pdfmetrics.stringWidth(test, FONT_NAME, font_size) < max_width:
                    current.append(w)
                else:
                    wrapped.append(" ".join(current))
                    current = [w]

            if current:
                wrapped.append(" ".join(current))

            for wline in wrapped:
                if y < 40:
                    c.showPage()
                    c.setFont(FONT_NAME, font_size)
                    y = height - 40

                if bg_color:
                    c.setFillColor(bg_color)
                    c.rect(
                        margin_left - 2,
                        y - 4,
                        max_width + 4,
                        line_height,
                        fill=1,
                        stroke=0,
                    )

                c.setFillColor(text_color)
                c.drawString(margin_left, y, wline)
                y -= line_height

    c.save()


# Read input from environment variable set by GitHub Actions
input_txt = os.environ["INPUT_TXT"]
os.makedirs("pdf", exist_ok=True)
base = os.path.splitext(os.path.basename(input_txt))[0]
pdf_path = os.path.join("pdf", f"{base}.pdf")

print(f"📄 Converting {base}.txt → {base}.pdf")
create_styled_pdf(input_txt, pdf_path)
print("✅ Done.")
