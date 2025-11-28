import os
import sys
import re
import time
# requests is no longer needed for the font
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# --- PDF IMPORTS ---
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors

# --- CONFIG ---
USERNAME = os.environ.get("KROK_USERNAME")
PASSWORD = os.environ.get("KROK_PASSWORD")
TARGET_ID = int(os.environ.get("TARGET_ID", 0))

COURSE_URL = "https://test.testcentr.org.ua/course/view.php?id=4"
LOGIN_URL = "https://test.testcentr.org.ua/login/index.php"
TXT_FOLDER = "txt"
PDF_FOLDER = "pdf"

# --- FONT CONFIG ---
# We expect this file to be in the repo now
FONT_FILE = "DejaVuSans.ttf" 
FONT_NAME = 'DejaVuSans'

# --- THE HARDCODED LIST ---
TEST_MAP = {
    1: 'Крок 1 Промислова фармація',
    2: 'Крок 1 Фармація (UA)',
    3: 'Крок 1 Стоматологія (UA)',
    4: 'Krok 1 Stomatology (EN)',
    5: 'Krok 1 Pharmacy (EN)',
    6: 'Krok 1 Medicine (EN)',
    7: 'Крок 1 Медицина (UA)',
    8: 'Крок 1 Фармація (UA) (для здобувачів, які складатимуть іспит з червня 2025 року)',
    9: 'Крок 2 Медична психологія (UA)',
    10: 'Крок 2 Фізична терапія (UA)',
    11: 'Крок 2 Громадське здоров\'я (UA)',
    12: 'Крок 2 Технології медичної діагностики та лікування',
    13: 'Крок 2 Ерготерапія',
    14: 'Крок 2 Промислова фармація',
    15: 'Крок 2 Стоматологія (UA)',
    16: 'Krok 2 Stomatology (EN)',
    17: 'Крок 2 Фармація (UA)',
    18: 'Krok 2 Pharmacy (EN)',
    19: 'Крок 2 Медицина (UA)',
    20: 'Krok 2 Medicine (EN)',
    21: 'Krok 2 Public health (EN)',
    22: 'Крок 2 Педіатрія (UA)',
    23: 'Крок 3 Епідеміологія',
    24: 'Крок 3 Медична Психологія',
    25: 'Крок 3 Патологічна анатомія',
    26: 'Крок 3 Радіологія',
    27: 'Крок 3 Внутрішні хвороби',
    28: 'Крок 3 Дерматовенерологія',
    29: 'Крок 3 Загальна практика - сімейна медицина',
    30: 'Крок 3 Інфекційні хвороби',
    31: 'Крок 3 Неврологія',
    32: 'Крок 3 Ортопедія і травматологія',
    33: 'Крок 3 Отоларингологія',
    34: 'Крок 3 Педіатрія',
    35: 'Крок 3 Психіатрія',
    36: 'Крок 3 Фізична та реабілітаційна медицина',
    37: 'Крок 3 Медицина невідкладних станів',
    38: 'Крок 3 Фармація',
    39: 'Крок 3 Стоматологія',
    40: 'Крок 3 Лабораторна діагностика, вірусологія, мікробіологія',
    41: 'Крок 3 Офтальмологія',
    42: 'ЄДКІ Фахова передвища освіта "Фармація, промислова фармація"',
    43: 'ЄДКІ Фахова передвища освіта "Медсестринство"',
    44: 'ЄДКІ Фахова передвища освіта "Стоматологія" Ортопедична',
    45: 'ЄДКІ Фахова передвища освіта "Стоматологія" Профілактична',
    46: 'ЄДКІ Бакалаври "Екстрена медицина"',
    47: 'ЄДКІ Бакалаври "Фізична терапія, ерготерапія"',
    48: 'ЄДКІ Бакалаври "Технології медичної діагностики та лікування"',
    49: 'ЄДКІ Бакалаври "Медсестринство" (UA)',
    50: 'ЄДКІ Фахова передвища освіта "Стоматологія"',
    51: 'USQE "Nursing" bachelor\'s program (EN)',
    52: 'АМПС Медицина (питання множинного вибору)',
    53: 'АМПС Стоматологія (питання множинного вибору)',
    54: 'АМПС Фармація, промислова фармація (питання множинного вибору)',
    55: 'АМПС Медицина (текст 1 та питання до нього )',
    56: 'АМПС Медицина (текст 2 та питання до нього)',
    57: 'АМПС Медицина (текст 3 та питання до нього)',
    58: 'АМПС Стоматологія (текст 1 та питання до нього)',
    59: 'АМПС Фармація (текст 1 та питання до нього)',
    60: 'АМПС Фармація (текст 2 та питання до нього)',
    61: 'АМПС Медицина/Фармація/Стоматологія (текст 1 та питання до нього)',
}

class KrokScraper:
    def __init__(self):
        self.driver = None
        self.setup_driver()
        self.prepare_folders()
        self.setup_font()

    def prepare_folders(self):
        if not os.path.exists(TXT_FOLDER): os.makedirs(TXT_FOLDER)
        if not os.path.exists(PDF_FOLDER): os.makedirs(PDF_FOLDER)

    def setup_font(self):
        # Check if font exists in the repo
        if not os.path.exists(FONT_FILE):
            print(f"❌ Error: {FONT_FILE} not found in repository root.", flush=True)
            print("   Please upload DejaVuSans.ttf to your GitHub repo.", flush=True)
            sys.exit(1)
        
        # Register Font
        try:
            pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_FILE))
            print(f"✅ Font registered: {FONT_NAME}", flush=True)
        except Exception as e:
            print(f"❌ Font Registration Error: {e}", flush=True)
            sys.exit(1)

    def setup_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        self.driver = webdriver.Chrome(options=options)

    def login(self):
        print(f"🔑 Logging in...", flush=True)
        wait = WebDriverWait(self.driver, 15)
        self.driver.get(LOGIN_URL)
        wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(USERNAME)
        self.driver.find_element(By.ID, "password").send_keys(PASSWORD)
        self.driver.find_element(By.ID, "loginbtn").click()
        wait.until(EC.presence_of_element_located((By.ID, "page-footer")))
        print("✅ Login successful.", flush=True)

    def run(self):
        target_name = TEST_MAP.get(TARGET_ID)
        if not target_name:
            print(f"❌ Error: ID {TARGET_ID} is not in the list.", flush=True)
            sys.exit(1)

        try:
            self.login()
            print(f"🔎 Searching for test: {target_name}", flush=True)
            self.driver.get(COURSE_URL)
            
            try:
                link_element = self.driver.find_element(By.PARTIAL_LINK_TEXT, target_name)
                target_link = link_element.get_attribute('href')
                print(f"🔗 Found link: {target_link}", flush=True)
            except:
                print(f"❌ Could not find link with text: {target_name}", flush=True)
                sys.exit(1)

            # --- SCRAPE ---
            questions = self.scrape_loop(target_link)
            
            if questions:
                # 1. Save TXT
                txt_path = self.save_txt(target_name, questions)
                # 2. Convert to PDF
                self.convert_to_pdf(txt_path)
            else:
                print("❌ No questions collected.", flush=True)
                sys.exit(1)

        finally:
            self.driver.quit()

    def scrape_loop(self, quiz_link):
        questions_map = {}
        wait = WebDriverWait(self.driver, 10)
        
        consecutive_empty_rounds = 0
        round_num = 1
        max_rounds = 4 

        print(f"\n🚀 STARTING SCRAPE LOOP (Max empty rounds: {max_rounds})", flush=True)

        while consecutive_empty_rounds < max_rounds:
            print(f"\n🔄 STARTING ROUND {round_num}...", flush=True)
            try:
                self.driver.get(quiz_link)

                # 1. Attempt / Continue
                for sel in [".quizstartbuttondiv button", "//button[contains(text(), 'Continue')]", "//button[contains(text(), 'Attempt')]"]:
                    try:
                        if "//" in sel: btn = wait.until(EC.element_to_be_clickable((By.XPATH, sel)))
                        else: btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
                        self.driver.execute_script("arguments[0].click();", btn)
                        break
                    except: continue
                
                # 2. Popup
                try:
                    popup_btn = self.driver.find_element(By.ID, "id_submitbutton")
                    if popup_btn.is_displayed(): self.driver.execute_script("arguments[0].click();", popup_btn)
                except: pass

                # 3. Finish Attempt
                try:
                    finish_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".endtestlink")))
                    self.driver.execute_script("arguments[0].click();", finish_link)
                except: 
                    print("   ⚠️ Could not find 'Finish attempt' link. Retrying...", flush=True)
                    consecutive_empty_rounds += 1
                    continue

                # 4. Submit
                for _ in range(3):
                    try:
                        s_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn-finishattempt button")))
                        self.driver.execute_script("arguments[0].click();", s_btn)
                        m_btn = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".modal-footer button.btn-primary")))
                        self.driver.execute_script("arguments[0].click();", m_btn)
                        break
                    except: time.sleep(0.5)

                # 5. Expand
                try:
                    show_all = wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@href, 'showall=1')]")))
                    self.driver.execute_script("arguments[0].click();", show_all)
                    time.sleep(2)
                except: pass

                # 6. Parse
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "que")))
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                questions = soup.find_all("div", class_="que")
                
                new_count = 0
                for q in questions:
                    q_text_div = q.find("div", class_="qtext")
                    if not q_text_div: continue
                    q_text = q_text_div.get_text(strip=True)
                    
                    if q_text in questions_map: continue

                    correct_ans = ""
                    feedback = q.find("div", class_="feedback")
                    if feedback:
                        ra = feedback.find("div", class_="rightanswer")
                        if ra: correct_ans = ra.get_text(strip=True).replace("The correct answer is:", "").replace("Правильна відповідь:", "").strip()

                    options_str = ""
                    ans_div = q.find("div", class_="answer")
                    if ans_div:
                        opts = ans_div.find_all("div", recursive=False) or ans_div.find_all("div", class_="d-flex")
                        for opt in opts:
                            l_span = opt.find("span", class_="answernumber")
                            if not l_span: continue
                            letter = l_span.get_text(strip=True)
                            t_div = opt.find("div", class_="flex-fill")
                            txt = t_div.get_text(strip=True) if t_div else ""
                            
                            pre = "*" if correct_ans and txt.strip() == correct_ans else ""
                            options_str += f"{pre}{letter} {txt}\n"

                    questions_map[q_text] = f"{q_text}\n{options_str}"
                    new_count += 1

                print(f"   ✅ Round {round_num} Complete: Found {new_count} new questions. (Total: {len(questions_map)})", flush=True)
                
                if new_count == 0: consecutive_empty_rounds += 1
                else: consecutive_empty_rounds = 0

                round_num += 1
                time.sleep(1)

            except Exception as e:
                print(f"   ❌ Round Error: {e}", flush=True)
                consecutive_empty_rounds += 1
                time.sleep(2)
        
        return questions_map

    def save_txt(self, name, data):
        clean_name = re.sub(r'[\\/*?:"<>|]', "", name).strip()
        filename = f"{clean_name}.txt"
        filepath = os.path.join(TXT_FOLDER, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            counter = 1
            for _, val in data.items():
                f.write(f"{counter}. {val}\n")
                counter += 1
        print(f"\n💾 TXT Saved: {filepath}", flush=True)
        return filepath

    # --- PDF LOGIC ---
    def wrap_text(self, text, font_name, font_size, max_width):
        lines = []
        words = text.split(' ')
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            width = pdfmetrics.stringWidth(test_line, font_name, font_size)
            if width < max_width:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        return lines

    def convert_to_pdf(self, txt_path):
        filename = os.path.basename(txt_path).replace(".txt", ".pdf")
        pdf_path = os.path.join(PDF_FOLDER, filename)
        print(f"⚙️ Converting to PDF: {pdf_path}...", flush=True)

        c = canvas.Canvas(pdf_path, pagesize=A4)
        width, height = A4
        
        margin_left = 40
        margin_right = 40
        max_text_width = width - margin_left - margin_right
        line_height = 16
        font_size = 11
        
        y = height - 40 
        c.setFont(FONT_NAME, font_size)

        with open(txt_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    y -= 10
                    continue

                bg_color = None
                text_color = colors.black

                # 1. DETECT QUESTION (Yellow)
                if re.match(r'^\d+\.', line):
                    bg_color = colors.lightyellow
                    text_color = colors.black
                
                # 2. DETECT CORRECT ANSWER (Green)
                elif line.startswith('*'):
                    line = line[1:].strip() # Remove asterisk
                    bg_color = colors.lightgreen
                    text_color = colors.darkgreen
                
                # 3. NORMAL OPTION
                else:
                    text_color = colors.darkgrey

                wrapped_lines = self.wrap_text(line, FONT_NAME, font_size, max_text_width)

                for wrapped_line in wrapped_lines:
                    if y < 40:
                        c.showPage()
                        c.setFont(FONT_NAME, font_size)
                        y = height - 40

                    if bg_color:
                        c.setFillColor(bg_color)
                        c.rect(margin_left - 2, y - 4, max_text_width + 4, line_height, fill=1, stroke=0)

                    c.setFillColor(text_color)
                    c.drawString(margin_left, y, wrapped_line)
                    y -= line_height

        c.save()
        print(f"✅ PDF Created Successfully.", flush=True)

if __name__ == "__main__":
    KrokScraper().run()
