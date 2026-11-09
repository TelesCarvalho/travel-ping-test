import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select, WebDriverWait
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
    opcoes.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=opcoes)
    wait = WebDriverWait(driver, 15)

    try:
        driver.get("https://portalturismo.sescgo.com.br/")
        
        # 1. Unidade (Caldas Novas)
        unidade = wait.until(EC.presence_of_element_located((By.ID, "search-unidade")))
        Select(unidade).select_by_visible_text("Caldas Novas")
        time.sleep(1)

        # 2. Período (31/12/2026 - 03/01/2027)
        campo_data = driver.find_element(By.NAME, "datas")
        driver.execute_script("arguments[0].value = '';", campo_data)
        campo_data.send_keys(Keys.CONTROL + "a")
        campo_data.send_keys(Keys.BACKSPACE)
        campo_data.send_keys("31/12/2026 - 03/01/2027")
        campo_data.send_keys(Keys.TAB)
        time.sleep(1)

        # 3. Adultos (2)
        adultos = driver.find_element(By.NAME, "adultos")
        Select(adultos).select_by_value("2")
        time.sleep(1)

        # 4. Regime de Pensão (Pensão Completa)
        pensao = driver.find_element(By.ID, "regime-pensao")
        Select(pensao).select_by_visible_text("Pensão Completa")
        time.sleep(1)

        # Clica no botão BUSCAR
        btn_buscar = driver.find_element(By.ID, "search-submit")
        driver.execute_script("arguments[0].click();", btn_buscar)
        
        time.sleep(10) # Espera o carregamento dos resultados

        # 5. Análise do Resultado
        pagina = driver.find_element(By.TAG_NAME, "body").text.lower()
        
        # Frase exata que confirma INDISPONIBILIDADE no período consultado
        texto_sem_disponibilidade = "não existe disponibilidade para o período consultado"
        
        # Termos que confirmam a vaga REAL (cobre 1 quarto ou vários quartos)
        tem_quarto_disponivel = (
            "selecionar" in pagina or 
            "selecionado" in pagina or 
            "reservar" in pagina or 
            "quarto 01" in pagina
        )

        if texto_sem_disponibilidade in pagina:
            print("Sem vagas no momento para o período consultado. O robô continuará vigiando.")
        elif tem_quarto_disponivel:
            notificar_guilherme("🚨 VAGA ENCONTRADA!\n📅 31/12/26 a 03/01/27\n🛏️ 1 Quarto p/ 2 Adultos\n🏃‍♂️ Corra para o site e reserve!")
            print("Mensagem enviada com sucesso!")
        else:
            print("Aviso: A página não carregou os resultados esperados. Nenhuma notificação enviada.")

    except Exception as e:
        print(f"Erro detalhado ao navegar: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    verificar_sesc()
