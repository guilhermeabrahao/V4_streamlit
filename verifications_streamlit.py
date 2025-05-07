
import logging
import time
import requests
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

def check_facebook_ads(instagram_username):
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920x1080")
        chrome_options.add_argument("--disable-dev-tools")
        chrome_options.add_argument("--remote-debugging-port=9222")

        driver = webdriver.Chrome(options=chrome_options)
        driver.get("https://www.facebook.com/ads/library/")

        wait = WebDriverWait(driver, 10)
        search_box = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//input[@placeholder="Pesquisar por nome ou tópico"]')
        ))
        search_box.send_keys(instagram_username)
        search_box.send_keys(Keys.ENTER)
        time.sleep(5)

        page_source = driver.page_source
        if "Não foram encontrados anúncios" in page_source:
            result = "Não há anúncios ativos"
        else:
            result = "Anúncios ativos encontrados"

        driver.quit()
        return result

    except Exception as e:
        return f"Facebook Ads: Erro ao extrair: {e}"

def check_google_ads(domain):
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920x1080")
        chrome_options.add_argument("--disable-dev-tools")
        chrome_options.add_argument("--remote-debugging-port=9222")

        driver = webdriver.Chrome(options=chrome_options)
        driver.get(f"https://transparencyreport.google.com/ads/advertiser/{domain}")

        time.sleep(5)
        page_source = driver.page_source

        if "Não há dados disponíveis" in page_source or "No data available" in page_source:
            result = "Não há anúncios ativos"
        else:
            result = "Anúncios ativos encontrados"

        driver.quit()
        return result

    except Exception as e:
        return f"Google Ads: Erro ao extrair: {e}"

def run_verification_tasks(instagram_username, domain):
    results = {}
    results['facebook_ads'] = check_facebook_ads(instagram_username)
    results['google_ads'] = check_google_ads(domain)
    return results
