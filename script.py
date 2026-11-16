import os
import time
import traceback
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
SESC_CPF = os.environ.get("SESC_CPF")
SESC_SENHA = os.environ.get("SESC_SENHA")
GITHUB_TOKEN = os.environ.get("GH_TOKEN")
GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY")

PERIODO_BUSCA = "31/12/2026 - 03/01/2027"
PERIODO_TEXTO = "31/12/2026 a 03/01/2027"


def enviar_telegram(mensagem):
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
        try:
            requests.post(url, data=payload, timeout=10)
        except Exception as e:
            print(f"Erro ao enviar mensagem no Telegram: {e}")


def enviar_foto_telegram(caminho_foto, legenda):
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID and os.path.exists(caminho_foto):
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        try:
            with open(caminho_foto, "rb") as foto:
                requests.post(
                    url,
                    data={"chat_id": TELEGRAM_CHAT_ID, "caption": legenda, "parse_mode": "Markdown"},
                    files={"photo": foto},
                    timeout=15
                )
        except Exception as e:
            print(f"Erro ao enviar foto no Telegram: {e}")


def desativar_workflow_github():
    """Desativa o workflow main.yml no GitHub Actions após reter a(s) reserva(s)."""
    if GITHUB_TOKEN and GITHUB_REPOSITORY:
        url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/actions/workflows/main.yml/disable"
        headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        res = requests.put(url, headers=headers)
        if res.status_code == 204:
            print("🔒 Workflow main.yml desativado com sucesso!")
        else:
            print(f"Erro ao tentar desativar workflow: {res.status_code} - {res.text}")


def tem_botao_reservar_visivel(driver):
    """Retorna True apenas se existir um botão Reservar realmente visível na tela."""
    botoes = driver.find_elements(By.XPATH, "//a[contains(@class, 'set-disponibilidade-session')]")
    return any(b.is_displayed() for b in botoes)


def buscar_disponibilidade(driver, wait, qtd_adultos):
    """Acessa a home, preenche os filtros e retorna True se houver vaga real."""
    print(f"Buscando disponibilidade para {qtd_adultos} adultos ({PERIODO_BUSCA})...")
    driver.get("https://portalturismo.sescgo.com.br/")

    unidade = wait.until(EC.presence_of_element_located((By.ID, "search-unidade")))
    Select(unidade).select_by_visible_text("Caldas Novas")

    campo_datas = driver.find_element(By.NAME, "datas")
    driver.execute_script("arguments[0].value = '';", campo_datas)
    campo_datas.send_keys(Keys.CONTROL + "a")
    campo_datas.send_keys(Keys.BACKSPACE)
    campo_datas.send_keys(PERIODO_BUSCA)
    campo_datas.send_keys(Keys.TAB)

    adultos = driver.find_element(By.NAME, "adultos")
    Select(adultos).select_by_value(str(qtd_adultos))

    pensao = driver.find_element(By.ID, "regime-pensao")
    Select(pensao).select_by_visible_text("Pensão Completa")

    btn_buscar = driver.find_element(By.ID, "search-submit")
    driver.execute_script("arguments[0].click();", btn_buscar)

    WebDriverWait(driver, 25).until(
        lambda d: "não existe disponibilidade" in d.find_element(By.TAG_NAME, "body").text.lower()
        or tem_botao_reservar_visivel(d)
    )

    body_text = driver.find_element(By.TAG_NAME, "body").text.lower()
    sem_vaga = ("não existe disponibilidade" in body_text) or ("outras datas próximas" in body_text)

    if sem_vaga or not tem_botao_reservar_visivel(driver):
        print(f"Nenhuma vaga encontrada para {qtd_adultos} adultos.")
        return False

    print(f"🚨 VAGA REAL ENCONTRADA para {qtd_adultos} adultos!")
    return True


def reservar_e_logar(driver, wait, qtd_adultos, numero_quarto):
    """Clica em Reservar, faz login (se ainda não estiver logado) e confirma a retenção de 30 min."""
    etapa = "Iniciando reserva"
    try:
        etapa = f"1. Clicar no botão Reservar (Quarto {numero_quarto} - {qtd_adultos} adultos)"
        btn_reservar = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(@class, 'set-disponibilidade-session')]"))
        )
        driver.execute_script("arguments[0].click();", btn_reservar)

        # Aguarda abrir a tela de login OU ir direto para a tela de integrantes (caso já esteja logado)
        WebDriverWait(driver, 20).until(
            lambda d: len(d.find_elements(By.ID, "login-form-username")) > 0
            or len(d.find_elements(By.ID, "btn-efetuar-pgto")) > 0
        )

        campos_cpf = driver.find_elements(By.ID, "login-form-username")
        if campos_cpf and campos_cpf[0].is_displayed():
            etapa = "2. Preencher CPF e Senha do titular"
            campos_cpf[0].send_keys(SESC_CPF)
            driver.find_element(By.ID, "login-form-password").send_keys(SESC_SENHA)

            etapa = "3. Clicar em Entrar no login"
            btn_entrar = driver.find_element(By.ID, "login-form-submit")
            driver.execute_script("arguments[0].click();", btn_entrar)

        etapa = "4. Confirmar retenção na tela de integrantes (/Booking/People)"
        WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.ID, "btn-efetuar-pgto")))
        time.sleep(2)

        arquivo_print = f"reserva_sucesso_{numero_quarto}.png"
        driver.save_screenshot(arquivo_print)
        enviar_foto_telegram(
            arquivo_print,
            f"🛒 *QUARTO {numero_quarto} PRESO NO CPF ({qtd_adultos} ADULTOS)!*\n"
            f"📅 Período: {PERIODO_TEXTO}\n"
            f"⏰ Vocês têm *30 minutos* para entrar no site do Sesc, adicionar os integrantes e pagar!"
        )
        print(f"✅ Quarto {numero_quarto} ({qtd_adultos} adultos) retido com sucesso!")
        return True

    except Exception as err:
        tipo_erro = type(err).__name__
        url_atual = driver.current_url
        print(f"Falha na etapa [{etapa}] ({tipo_erro}): {err}")
        traceback.print_exc()

        arquivo_erro = f"erro_reserva_{numero_quarto}.png"
        driver.save_screenshot(arquivo_erro)
        enviar_foto_telegram(
            arquivo_erro,
            f"⚠️ *VAGA ENCONTRADA ({qtd_adultos} adultos), mas falhou na etapa:*\n`{etapa}`\n"
            f"🔍 *Erro:* `{tipo_erro}`\n"
            f"🌐 *URL:* {url_atual}\n\n"
            f"🏃‍♂️ *Entrem no site AGORA e tentem reservar manualmente!*"
        )
        return False


chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 15)

try:
    reservas_garantidas = 0

    # TENTATIVA 1: 1 quarto para 5 adultos
    if buscar_disponibilidade(driver, wait, qtd_adultos=5):
        enviar_telegram(
            f"🚨 *VAGA ENCONTRADA PARA 5 ADULTOS!*\n📅 Período: {PERIODO_TEXTO}\n🤖 *Prendendo o quarto no CPF...*"
        )
        if reservar_e_logar(driver, wait, qtd_adultos=5, numero_quarto=1):
            reservas_garantidas += 1

    # TENTATIVA 2: Se não achou para 5 adultos, tenta até 2 quartos para 3 adultos
    else:
        for tentativa in range(1, 3):
            if buscar_disponibilidade(driver, wait, qtd_adultos=3):
                enviar_telegram(
                    f"🚨 *VAGA ENCONTRADA PARA 3 ADULTOS (Quarto {tentativa}/2)!*\n"
                    f"📅 Período: {PERIODO_TEXTO}\n🤖 *Prendendo o quarto no CPF...*"
                )
                if reservar_e_logar(driver, wait, qtd_adultos=3, numero_quarto=tentativa):
                    reservas_garantidas += 1
            else:
                break

    if reservas_garantidas > 0:
        enviar_telegram(
            f"✅ *PROCESSO CONCLUÍDO ({reservas_garantidas} quarto(s) retido(s))!*\n"
            f"🔒 O robô foi *DESATIVADO* automaticamente. Finalizem o cadastro dos adultos e o pagamento no portal do Sesc!"
        )
        desativar_workflow_github()

finally:
    driver.quit()
