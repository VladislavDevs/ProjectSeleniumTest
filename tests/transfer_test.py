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

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    # Открываем сервис с параметрами, вызывающими дефект
    driver.get("http://localhost:8000/?balance=30000&reserved=20001")
    yield driver
    driver.quit()


def test_transfer_with_insufficient_funds_should_fail(driver):
    # Нажать на рублёвый счёт
    driver.find_element(By.CSS_SELECTOR, ".ruble-account").click()

    # Ввести номер карты (16 цифр)
    card_input = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.NAME, "cardNumber"))
    )
    card_input.send_keys("1234567812345678")
    driver.find_element(By.XPATH, "//button[text()='Далее']").click()

    # Ввести сумму, которая превышает доступную с учётом комиссии
    amount_input = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.NAME, "amount"))
    )
    amount_input.send_keys("10000")
    driver.find_element(By.XPATH, "//button[text()='Далее']").click()

    # Проверяем, что появилось сообщение о невозможности перевода
    error_msg = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.CLASS_NAME, "error-message"))
    )
    assert "невозможен" in error_msg.text
    # И кнопка "Перевести" отсутствует
    with pytest.raises(Exception):
        driver.find_element(By.XPATH, "//button[text()='Перевести']")