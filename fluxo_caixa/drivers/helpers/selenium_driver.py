import subprocess
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
def encerrar_chrome_drivers():
    subprocess.call(["taskkill", "/F", "/IM", "chromedriver.exe"])
    # Fecha todos os processos do navegador Chrome que foram abertos
    subprocess.call(["taskkill", "/F", "/IM", "chrome.exe"])

def iniciar_driver_selenium(driver_path: str, url: str):
    if driver_path and url:
        encerrar_chrome_drivers()
        time.sleep(5)
        chrome_options = Options()
        # chrome_options.add_argument("--headless") 
        chrome_options.add_argument("--incognito")
        service = Service(driver_path)

        driver = webdriver.Chrome(service=service, options=chrome_options)
        time.sleep(5)
        driver.get(url)
        return driver
    else:
        print("O caminho do ChromeDriver, login ou senha não foram especificados. O WebDriver não será iniciado.")
        return None
    

def efetuar_login(driver: WebDriver | None, login: str, senha: str):
    try:
        # Localizar o campo de login pelo seletor e inserir o nome de usuário
        campo_login = driver.find_element(By.CSS_SELECTOR, 
            "body > div.nlogin-content > div:nth-child(1) > div.nlogin-form-col.col-lg-5.col-md-5.col-sm-12.col-xs-12 > div > div > div.nlogin-form-b > form:nth-child(2) > div:nth-child(1) > input")
        campo_login.send_keys(login)
        
        # Localizar o campo de senha pelo seletor e inserir a senha
        campo_senha = driver.find_element(By.CSS_SELECTOR, 
            "body > div.nlogin-content > div:nth-child(1) > div.nlogin-form-col.col-lg-5.col-md-5.col-sm-12.col-xs-12 > div > div > div.nlogin-form-b > form:nth-child(2) > div:nth-child(2) > input")
        campo_senha.send_keys(senha)
        
        # Localizar o botão de login e clicar
        botao_login = driver.find_element(By.CSS_SELECTOR, 
            "body > div.nlogin-content > div:nth-child(1) > div.nlogin-form-col.col-lg-5.col-md-5.col-sm-12.col-xs-12 > div > div > div.nlogin-form-b > form:nth-child(2) > div:nth-child(4) > button")
        botao_login.click()

        # Espera alguns segundos para o processo de login completar (dependendo da página, pode ser necessário ajustar)
        driver.implicitly_wait(5)
        time.sleep(3)
        try: 
            botao_extra = driver.find_element(By.CSS_SELECTOR, 
                "body > div.nlogin-content > div:nth-child(1) > div.nlogin-form-col.col-lg-5.col-md-5.col-sm-12.col-xs-12 > div > div > div.nlogin-form-b > form > div > div:nth-child(3) > button")
            botao_extra.click()
            print("Botão extra encontrado e clicado.")
        except:
            print("Botão extra não encontrado. Prosseguindo com o login normal.")
        print("Login efetuado com sucesso.")
    
    except Exception as e:
        print(f"Erro ao tentar efetuar login: {e}")

