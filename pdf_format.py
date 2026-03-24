import os
import re
import sys
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors

# --- CONFIG ---
FONT_FILE = "DejaVuSans.ttf" 
FONT_NAME = 'DejaVuSans'

def setup_font():
    if not os.path.exists(FONT_FILE):
        print(f"❌ Error: {FONT_FILE} not found. Please place it in this directory.")
        sys.exit(1)
    try:
        pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_FILE))
    except Exception as e:
        print(f"❌ Font Registration Error: {e}")
        sys.exit(1)

def wrap_text(text, font_name, font_size, max_width):
    """Exact wrapping logic from the original script."""
    lines = []
    words = text.split(' ')
    current_line = []
    for word in words:
        test_line = ' '.join(current_line + [word])
        if pdfmetrics.stringWidth(test_line, font_name, font_size) < max_width:
            current_line.append(word)
        else:
            lines.append(' '.join(current_line))
            current_line = [word]
    if current_line: 
        lines.append(' '.join(current_line))
    return lines

def convert_to_pdf(input_txt):
    if not os.path.exists(input_txt):
        print(f"❌ Error: {input_txt} not found.")
        return

    output_pdf = input_txt.replace(".txt", ".pdf")
    print(f"⚙️ Converting {input_txt} to {output_pdf}...")

    setup_font()
    
    c = canvas.Canvas(output_pdf, pagesize=A4)
    width, height = A4
    margin = 40
    max_w = width - (margin * 2)
    y = height - 40 
    font_size = 11
    c.setFont(FONT_NAME, font_size)

    with open(input_txt, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            
            # Handle empty lines
            if not line:
                y -= 10
                continue

            # --- STYLING LOGIC ---
            bg_color = None
            text_color = colors.black

            # 1. Logic for Questions (Starts with Number + Dot)
            if re.match(r'^\d+\.', line):
                bg_color = colors.lightyellow
            
            # 2. Logic for Correct Answers (Starts with *)
            elif line.startswith('*'):
                line = line[1:].strip() # Strip the asterisk
                bg_color = colors.lightgreen
                text_color = colors.darkgreen
            
            # 3. Logic for Other Options
            else:
                text_color = colors.darkgrey

            # Wrap text to fit page width
            wrapped_lines = wrap_text(line, FONT_NAME, font_size, max_w)
            
            for wl in wrapped_lines:
                # Check for page break
                if y < 50:
                    c.showPage()
                    c.setFont(FONT_NAME, font_size)
                    y = height - 40
                
                # Draw Background Rectangle
                if bg_color:
                    c.setFillColor(bg_color)
                    # Rect coordinates: (x, y, width, height)
                    c.rect(margin - 2, y - 4, max_w + 4, 15, fill=1, stroke=0)
                
                # Draw Text
                c.setFillColor(text_color)
                c.drawString(margin, y, wl)
                
                # Move cursor down
                y -= 15

    c.save()
    print(f"✅ PDF Created: {output_pdf}")

if __name__ == "__main__":
    # You can change this to any filename
    target_file = "test_data.txt"
    
    # Create a dummy file for testing if it doesn't exist
    if not os.path.exists(target_file):
        with open(target_file, "w", encoding="utf-8") as f:
            f.write("1. What is the capital of Ukraine?\n")
            f.write("A. Lviv\n")
            f.write("*B. Kyiv\n")
            f.write("C. Odesa\n")
            f.write("\n")
            f.write("2. Example of a very long question text that should trigger the text wrapping logic inside the PDF generator to ensure it does not bleed off the edge of the A4 page size.\n")
            f.write("*A. Correct Answer highlight\n")
            f.write("B. Grey distractor\n")
            
    convert_to_pdf(target_file)
