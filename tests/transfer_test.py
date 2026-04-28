import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

@pytest.fixture
def driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--remote-debugging-port=9222")
    options.binary_location = "/usr/bin/google-chrome"

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.get("http://localhost:8000/?balance=10000&reserved=0")
    yield driver
    driver.quit()

def test_commission_rounding_bug(driver):
    # Выбираем рублёвый счёт
    rub_card = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'g-card') and .//h2[text()='Рубли']]"))
    )
    rub_card.click()

    # Вводим номер карты
    card_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='0000']"))
    )
    card_input.send_keys("1234567812345678")

    # Вводим сумму 110
    amount_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='1000']"))
    )
    amount_input.clear()
    amount_input.send_keys("110")

    # Получаем текст комиссии (элемент с id="comission")
    commission_span = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "comission"))
    )
    commission = int(commission_span.text)

    # Ожидаем 11, реально 10 → тест упадёт
    assert commission == 11, f"Комиссия должна быть 11, получено {commission}"

def test_negative_amount_bug(driver):
    # Перезагружаем страницу с нулевым доступным балансом
    driver.get("http://localhost:8000/?balance=1000&reserved=1000")

    rub_card = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'g-card') and .//h2[text()='Рубли']]"))
    )
    rub_card.click()

    card_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='0000']"))
    )
    card_input.send_keys("1234567812345678")

    amount_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='1000']"))
    )
    amount_input.clear()
    amount_input.send_keys("-500")

    # Проверяем, что кнопка "Перевести" НЕ появляется
    # Если появляется (баг) – тест упадёт
    with pytest.raises(Exception):
        WebDriverWait(driver, 3).until(
            EC.visibility_of_element_located((By.XPATH, "//button[text()='Перевести']"))
        )