import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
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
    opcoes.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=opcoes)

    try:
        driver.get("https://portalturismo.sescgo.com.br/")
        time.sleep(8) 

        # 1. Unidade (usando o ID fornecido: search-unidade)
        unidade = driver.find_element(By.ID, "search-unidade")
        Select(unidade).select_by_visible_text("Caldas Novas")
        
        # 2. Período (usando o name fornecido: datas)
        campo_data = driver.find_element(By.NAME, "datas")
        campo_data.clear()
        campo_data.send_keys("31/12/2026 - 03/01/2027")
        time.sleep(2)

        # 3. Adultos (usando o name fornecido: adultos)
        adultos = driver.find_element(By.NAME, "adultos")
        Select(adultos).select_by_value("2")
        time.sleep(2)

       # 4. Regime de Pensão (usando o ID fornecido: regime-pensao)
        pensao = driver.find_element(By.ID, "regime-pensao")
        Select(pensao).select_by_visible_text("Pensão Completa")
        time.sleep(2)

        # Clica no botão BUSCAR usando o ID exato: search-submit
        btn_buscar = driver.find_element(By.ID, "search-submit")
        driver.execute_script("arguments[0].click();", btn_buscar)
        
        time.sleep(10) # Espera 10 segundos pela página de resultados

        # 5. Análise do Resultado
        pagina = driver.find_element(By.TAG_NAME, "body").text.lower()
        
        # Verifica se a frase exata da faixa amarela está na página
        if "não existe disponibilidade" in pagina:
            print("Sem vagas no momento. O robô continuará vigiando.")
        else:
            notificar_guilherme("🚨 VAGA ENCONTRADA!\n📅 31/12/26 a 03/01/27\n🛏️ 1 Quarto p/ 2 Adultos \n🏃‍♂️ Corra para o site e reserve!")
            print("Mensagem enviada com sucesso!")

    except Exception as e:
        print(f"Erro detalhado ao navegar: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    verificar_sesc()
