import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def notificar_guilherme(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": mensagem})

def verificar_sesc():
    opcoes = Options()
    opcoes.add_argument("--headless")
    opcoes.add_argument("--no-sandbox")
    opcoes.add_argument("--disable-dev-shm-usage")
    opcoes.add_argument("--window-size=1920,1080")
    # Simula um navegador real para evitar bloqueios
    opcoes.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=opcoes)

    try:
        driver.get("https://portalturismo.sescgo.com.br/")
        time.sleep(8) # Pausa maior para garantir que a página carrega totalmente na nuvem

        # 1. Unidade e Datas
        unidade = driver.find_element(By.XPATH, "//select[contains(@name, 'unidade') or contains(@name, 'Unidade')]")
        Select(unidade).select_by_visible_text("Caldas Novas")
        
        # Busca a única caixa de texto do formulário (que é a da data)
        campo_data = driver.find_element(By.XPATH, "//input[@type='text']")
        campo_data.clear()
        campo_data.send_keys("07/01/2027 - 08/01/2027")

        # 2. Configurar os 2 Adultos
        driver.find_element(By.XPATH, "//button[contains(text(), 'Selecione')]").click()
        time.sleep(2)
        Select(driver.find_element(By.XPATH, "(//select[contains(@class, 'form-select')])[1]")).select_by_visible_text("Dependente do Trabalhador do Comércio")
        Select(driver.find_element(By.XPATH, "(//select[contains(@class, 'form-select')])[2]")).select_by_visible_text("Dependente do Trabalhador do Comércio")
        driver.find_element(By.XPATH, "//button[text()='SALVAR']").click()
        time.sleep(2)

        # 3. Pensão e Busca
        Select(driver.find_element(By.XPATH, "//select[contains(text(), 'regime') or contains(@name, 'regime')]")).select_by_visible_text("Pensão Completa")
        driver.find_element(By.XPATH, "//button[contains(text(), 'BUSCAR') or contains(text(), 'Buscar')]").click()
        
        time.sleep(10) # Espera a página de resultados carregar totalmente

        # 4. Análise do Resultado
        pagina = driver.find_element(By.TAG_NAME, "body").text.lower()
        if "esgotado" not in pagina and "não há disponibilidade" not in pagina:
            notificar_guilherme("🚨 VAGA ENCONTRADA NO SESC CALDAS NOVAS!\n📅 07/01/27 a 08/01/27\n🛏️ 1 Quarto p/ 2 Adultos (Pensão Completa)\n🏃‍♂️ Corra para o site e reserve!")
        else:
            print("Sem vagas no momento. O robô continuará vigiando.")

    except Exception as e:
        print(f"Erro detalhado ao navegar: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    verificar_sesc()
