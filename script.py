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
        time.sleep(8) # Aguarda o carregamento inicial

        # 1. Unidade e Datas
        unidade = driver.find_element(By.XPATH, "//select[contains(@name, 'unidade') or contains(@name, 'Unidade')]")
        Select(unidade).select_by_visible_text("Caldas Novas")
        
        campo_data = driver.find_element(By.XPATH, "//input[@type='text']")
        campo_data.clear()
        campo_data.send_keys("07/01/2027 - 08/01/2027")
        time.sleep(2)

        # 2. Configurar os 2 Adultos (Com clique forçado via JS)
        botoes_selecione = driver.find_elements(By.XPATH, "//*[contains(text(), 'Selecione') or contains(@title, 'Selecione')]")
        for btn in botoes_selecione:
            try:
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(2) # Pausa para a janela modal abrir
                break # Se conseguiu clicar, sai do loop e avança
            except:
                continue

        # Seleciona os dependentes nos menus suspensos da janela modal
        Select(driver.find_element(By.XPATH, "(//select[contains(@class, 'form-select')])[1]")).select_by_visible_text("Dependente do Trabalhador do Comércio")
        Select(driver.find_element(By.XPATH, "(//select[contains(@class, 'form-select')])[2]")).select_by_visible_text("Dependente do Trabalhador do Comércio")
        
        # Clica no botão SALVAR da janela de adultos forçando via JS
        btn_salvar = driver.find_element(By.XPATH, "//*[contains(text(), 'SALVAR') or contains(text(), 'Salvar')]")
        driver.execute_script("arguments[0].click();", btn_salvar)
        time.sleep(2)

        # 3. Pensão e Busca
        Select(driver.find_element(By.XPATH, "//select[contains(text(), 'regime') or contains(@name, 'regime')]")).select_by_visible_text("Pensão Completa")
        
        # Clica no botão BUSCAR forçando via JS
        btn_buscar = driver.find_element(By.XPATH, "//*[contains(text(), 'BUSCAR') or contains(text(), 'Buscar')]")
        driver.execute_script("arguments[0].click();", btn_buscar)
        
        time.sleep(10) # Espera 10 segundos pela página de resultados (crucial na nuvem)

        # 4. Análise do Resultado
        pagina = driver.find_element(By.TAG_NAME, "body").text.lower()
        if "esgotado" not in pagina and "não há disponibilidade" not in pagina:
            notificar_guilherme("🚨 VAGA ENCONTRADA NO SESC CALDAS NOVAS!\n📅 07/01/27 a 08/01/27\n🛏️ 1 Quarto p/ 2 Adultos (Pensão Completa)\n🏃‍♂️ Corra para o site e reserve!")
            print("Mensagem enviada com sucesso!")
        else:
            print("Sem vagas no momento. O robô continuará vigiando.")

    except Exception as e:
        print(f"Erro detalhado ao navegar: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    verificar_sesc()
