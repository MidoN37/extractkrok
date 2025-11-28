import os
import sys
import re
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# --- CONFIG ---
USERNAME = os.environ.get("KROK_USERNAME")
PASSWORD = os.environ.get("KROK_PASSWORD")
TARGET_ID = int(os.environ.get("TARGET_ID", 0))

COURSE_URL = "https://test.testcentr.org.ua/course/view.php?id=4"
LOGIN_URL = "https://test.testcentr.org.ua/login/index.php"
OUTPUT_FOLDER = "txt"

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
        if not os.path.exists(OUTPUT_FOLDER):
            os.makedirs(OUTPUT_FOLDER)

    def setup_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        self.driver = webdriver.Chrome(options=options)

    def login(self):
        print(f"Logging in...")
        wait = WebDriverWait(self.driver, 15)
        self.driver.get(LOGIN_URL)
        wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(USERNAME)
        self.driver.find_element(By.ID, "password").send_keys(PASSWORD)
        self.driver.find_element(By.ID, "loginbtn").click()
        wait.until(EC.presence_of_element_located((By.ID, "page-footer")))
        print("Login successful.")

    def run(self):
        target_name = TEST_MAP.get(TARGET_ID)
        if not target_name:
            print(f"❌ Error: ID {TARGET_ID} is not in the list.")
            sys.exit(1)

        try:
            self.login()
            print(f"Searching for: {target_name}")
            self.driver.get(COURSE_URL)
            
            # Find the specific test link by text
            try:
                # We use partial link text because of occasional whitespace issues
                link = self.driver.find_element(By.PARTIAL_LINK_TEXT, target_name)
                print(f"Found link: {link.text}")
                link.click()
            except:
                print(f"❌ Could not find link with text: {target_name}")
                sys.exit(1)

            # Now inside the test folder - Scrape the logic
            questions = self.scrape_logic()
            
            if questions:
                self.save_txt(target_name, questions)
            else:
                print("❌ No questions collected.")
                sys.exit(1)

        finally:
            self.driver.quit()

    def scrape_logic(self):
        wait = WebDriverWait(self.driver, 10)
        questions_map = {}

        # 1. Start / Continue Test
        print("Starting attempt...")
        try:
            # Try finding "Continue" or "Attempt quiz now"
            btns = self.driver.find_elements(By.CSS_SELECTOR, "button")
            for btn in btns:
                txt = btn.text.lower()
                if "continue" in txt or "attempt" in txt or "розпочати" in txt or "продовжити" in txt:
                    self.driver.execute_script("arguments[0].click();", btn)
                    break
            
            # Start attempt popup confirmation
            try:
                popup = wait.until(EC.element_to_be_clickable((By.ID, "id_submitbutton")))
                popup.click()
            except: pass

        except Exception as e:
            print(f"Start logic warning: {e}")

        # 2. Finish Attempt (Immediately submit)
        print("Finishing attempt...")
        try:
            # Click "Finish attempt" link
            finish_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".endtestlink")))
            self.driver.execute_script("arguments[0].click();", finish_link)

            # Click "Submit all and finish" (1st time)
            s_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn-finishattempt button")))
            self.driver.execute_script("arguments[0].click();", s_btn)

            # Click "Submit all and finish" (Modal confirmation)
            m_btn = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".modal-footer button.btn-primary")))
            self.driver.execute_script("arguments[0].click();", m_btn)
        except Exception as e:
            print(f"Finish logic warning (test might be already closed): {e}")

        # 3. Expand All ("Show all questions on one page")
        print("Expanding questions...")
        try:
            show_all = wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@href, 'showall=1')]")))
            self.driver.execute_script("arguments[0].click();", show_all)
            time.sleep(2)
        except: 
            print("Could not find 'Show all' link, checking if already expanded...")

        # 4. Parse Content
        print("Parsing content...")
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        questions = soup.find_all("div", class_="que")
        
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

        return questions_map

    def save_txt(self, name, data):
        # Clean filename
        clean_name = re.sub(r'[\\/*?:"<>|]', "", name).strip()
        filename = f"{clean_name}.txt"
        filepath = os.path.join(OUTPUT_FOLDER, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            counter = 1
            for _, val in data.items():
                f.write(f"{counter}. {val}\n")
                counter += 1
        print(f"✅ Saved to: {filepath}")

if __name__ == "__main__":
    KrokScraper().run()
