import pytest
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
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
    """Баг 1: комиссия для суммы 110 должна быть 11, сервис выдаёт 10"""
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

    commission_span = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "comission"))
    )
    commission = int(commission_span.text)

    assert commission == 11, f"Комиссия должна быть 11, получено {commission}"


def test_negative_amount_bug(driver):
    """Баг 2: отрицательная сумма -500 не должна приниматься"""
    driver.get("http://localhost:8000/?balance=1000&reserved=1000")  # доступно 0

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

    # Кнопка "Перевести" не должна появляться
    with pytest.raises(TimeoutException):
        WebDriverWait(driver, 3).until(
            EC.visibility_of_element_located((By.XPATH, "//button[text()='Перевести']"))
        )


def test_card_number_length_bug(driver):
    """Баг 3: номер карты из 17 цифр должен отклоняться"""
    driver.get("http://localhost:8000/?balance=10000&reserved=0")

    rub_card = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'g-card') and .//h2[text()='Рубли']]"))
    )
    rub_card.click()

    card_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='0000']"))
    )
    # Вводим 17 цифр
    card_input.send_keys("12345678901234567")

    # Поле суммы не должно появиться (ожидаем TimeoutException)
    with pytest.raises(TimeoutException):
        WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='1000']"))
        )


def test_insufficient_funds(driver):
    """Перевод суммы, превышающей доступный баланс с учётом комиссии"""
    driver.get("http://localhost:8000/?balance=5000&reserved=4000")  # доступно 1000

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
    amount_input.send_keys("950")  # 950 + 95 = 1045 > 1000

    # Кнопка "Перевести" не должна появиться
    with pytest.raises(TimeoutException):
        WebDriverWait(driver, 3).until(
            EC.visibility_of_element_located((By.XPATH, "//button[text()='Перевести']"))
        )

    # Сообщение об ошибке должно быть
    error_msg = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.XPATH, "//span[contains(text(),'Недостаточно средств')]"))
    )
    assert "Недостаточно" in error_msg.text


def test_commission_15_rubles(driver):
    """Проверка комиссии для суммы 15 (должна быть 1, сервис выдаёт 0)"""
    driver.get("http://localhost:8000/?balance=10000&reserved=0")

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
    amount_input.send_keys("15")

    commission_span = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "comission"))
    )
    commission = int(commission_span.text)

    assert commission == 1, f"Комиссия для 15 рублей должна быть 1, получено {commission}"