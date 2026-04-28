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
    # Явно указываем путь к Chrome (для надёжности)
    options.binary_location = "/usr/bin/google-chrome"

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.get("http://localhost:8000/?balance=30000&reserved=20001")
    yield driver
    driver.quit()

def test_transfer_with_insufficient_funds_should_fail(driver):
    # 1. Клик по карточке "Рубли" (ищем по тексту)
    rub_card = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'g-card') and .//h2[text()='Рубли']]"))
    )
    rub_card.click()

    # 2. Поле ввода номера карты (ищем по плейсхолдеру)
    card_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='0000 0000']"))
    )
    card_input.send_keys("1234567812345678")

    # 3. Поле ввода суммы
    amount_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='1000']"))
    )
    amount_input.clear()
    amount_input.send_keys("10000")

    # 4. Сообщение об ошибке должно появиться (доступно: 30000-20001=9999, комиссия 1000, итого 11000 > 9999)
    error_msg = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.XPATH, "//span[contains(text(),'Недостаточно средств')]"))
    )
    assert "Недостаточно" in error_msg.text

    # 5. Кнопка "Перевести" НЕ должна появляться
    with pytest.raises(Exception):
        WebDriverWait(driver, 3).until(
            EC.visibility_of_element_located((By.XPATH, "//button[text()='Перевести']"))
        )