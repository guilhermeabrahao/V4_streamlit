"""
Este arquivo contém as funções de verificação adaptadas para o Streamlit (V2),
utilizando a API da OpenAI diretamente para análise de anúncios e webdriver-manager para Selenium.
"""
import os
import time
import logging
import requests
from dotenv import load_dotenv
from openai import OpenAI

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY não está configurada. A análise de IA falhará.")
else:
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

client = None
if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)

# --- Funções de Extração (Selenium com Webdriver-Manager) ---
def setup_selenium_driver():
    """Configura e retorna uma instância do WebDriver do Selenium usando webdriver-manager."""
    chrome_options = ChromeOptions()
    chrome_options.add_argument("--headless=new") # Modo headless moderno
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36") # User agent atualizado
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--lang=pt-BR")
    chrome_options.add_experimental_option('prefs', {'intl.accept_languages': 'pt-BR,pt'})

    try:
        logger.info("Configurando ChromeDriver com webdriver-manager.")
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        logger.info("WebDriver do Selenium (com webdriver-manager) inicializado com sucesso.")
        return driver
    except Exception as e:
        logger.error(f"Erro ao configurar o WebDriver do Selenium com webdriver-manager: {e}.", exc_info=True)
        raise RuntimeError(f"Falha ao inicializar o Selenium WebDriver via webdriver-manager: {e}")

def extract_facebook_ads(instagram_username):
    """Extrai o conteúdo da Biblioteca de Anúncios do Facebook para um dado usuário do Instagram usando Selenium e webdriver-manager."""
    if not instagram_username:
        return ""
    driver = None
    try:
        # URL atualizada e mais específica para Brasil e anúncios ativos
        url = f"https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=BR&is_targeted_country=false&media_type=all&q={instagram_username}&search_type=keyword_unordered"
        logger.info(f"Acessando Facebook Ads Library para: {instagram_username} com Selenium. URL: {url}")

        driver = setup_selenium_driver()
        driver.get(url)
        
        # Aumentar o tempo de espera e refinar seletores
        #wait = WebDriverWait(driver, 40) # Timeout aumentado
        #logger.info("Aguardando carregamento da página e possíveis pop-ups de cookies...")

        # Tentar fechar pop-ups de cookies/consentimento primeiro
        # Este seletor é um exemplo, pode precisar de ajuste para o Facebook
        #cookie_popup_selectors = [
         #   "//div[@aria-label='Fechar' and @role='button']", # Genérico
          #  "//div[@role='dialog']//div[@aria-label='Permitir todos os cookies']",
           # "//button[contains(., 'Aceitar todos os cookies') or contains(., 'Permitir cookies essenciais e opcionais')]",
            #"//div[@data-testid='cookie-policy-manage-dialog-accept-button']",
            #"//button[@title='Permitir todos os cookies']"
        #]

        #popup_closed = False
        #for i, selector in enumerate(cookie_popup_selectors):
         #   try:
                # Espera curta para o popup aparecer
          #      WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, selector)))
           #     cookie_button = driver.find_element(By.XPATH, selector)
            #    if cookie_button.is_displayed() and cookie_button.is_enabled():
             #       logger.info(f"Tentando fechar pop-up de cookie com seletor {i+1}: {selector}")
              #      driver.execute_script("arguments[0].click();", cookie_button)
               #     logger.info("Pop-up de cookie clicado.")
                #    popup_closed = True
                 #   time.sleep(3) # Pausa para o pop-up fechar e a página recarregar/estabilizar
                  #  break
          #  except (TimeoutException, NoSuchElementException):
          #      logger.info(f"Seletor de cookie {i+1} não encontrado ou não clicável: {selector}")
          #  except Exception as e_cookie:
          #      logger.warning(f"Erro ao tentar fechar cookie com seletor {i+1} ({selector}): {e_cookie}")
        
       # if not popup_closed:
        #    logger.info("Nenhum pop-up de cookie óbvio encontrado ou fechado. Continuando...")
        
        logger.info("Aguardando o conteúdo principal da biblioteca de anúncios...")
        # Seletor para resultados ou mensagem de "nenhum anúncio"
        # Este seletor é crucial e pode mudar com frequência no site do Facebook
       # main_content_selector = (
        #    "//div[contains(text(), 'Nenhum anúncio encontrado') or contains(text(), 'Nenhum anúncio ativo')] | " # Mensagens de nenhum anúncio
         #   "//div[contains(text(), 'anúncios de') and contains(@role, 'button')] | " # Indicador de que há anúncios
          #  "//div[contains(@class, '_702w') or contains(@class, '_99s5')] | " # Classes antigas que podem ainda existir
           # "//div[contains(text(), 'Resultados')] | " # Texto de resultados
            #"//div[string-length(normalize-space(.//a[@role=\'link\' and @target=\'_blank\']//span//div//div[1])) > 10]" # Tenta pegar um card de anúncio
        #)
        
        #wait.until(EC.presence_of_element_located((By.XPATH, main_content_selector)))
        logger.info("Conteúdo principal detectado.")
        time.sleep(5) # Espera adicional para renderização completa de JS e anúncios

        text = driver.find_element(By.TAG_NAME, 'body').text
        logger.info(f"Extração da Facebook Ads Library concluída para: {instagram_username}. Tamanho do texto: {len(text)} caracteres.")
        if not text.strip() or len(text.strip()) < 200: # Aumentar o limite mínimo
            logger.warning(f"Texto extraído da Facebook Ads Library para {instagram_username} parece muito curto. HTML da página será retornado.")
            page_html = driver.page_source
            return f"Erro ao extrair: Conteúdo do corpo do texto muito curto. HTML (primeiros 2000 chars): {page_html[:2000]}"
        return text

    except TimeoutException:
        logger.error(f"Timeout ao esperar pelo conteúdo da Facebook Ads Library para {instagram_username}", exc_info=True)
        page_source_on_timeout = ""
        body_text_on_timeout = ""
        try:
            if driver:
                 page_source_on_timeout = driver.page_source
                 body_text_on_timeout = driver.find_element(By.TAG_NAME, 'body').text
                 if body_text_on_timeout and body_text_on_timeout.strip() and len(body_text_on_timeout.strip()) > 100:
                     logger.warning(f"Conteúdo parcial do corpo extraído após timeout para {instagram_username}. Tamanho: {len(body_text_on_timeout)}")
                     return body_text_on_timeout
                 logger.warning(f"Corpo do texto vazio ou muito curto no timeout, mas page_source tem {len(page_source_on_timeout)} caracteres.")
                 return f"Erro ao extrair: Timeout. HTML no momento do timeout (primeiros 2000 chars): {page_source_on_timeout[:2000]}"
        except Exception as inner_e:
             logger.error(f"Erro ao tentar extrair conteúdo parcial após timeout para {instagram_username}: {inner_e}")
        return f"Erro ao extrair: Timeout esperando pelo conteúdo principal. Sem conteúdo recuperável."
    except WebDriverException as e:
         logger.error(f"Erro do WebDriver ao extrair anúncios do Facebook para {instagram_username}: {str(e)}", exc_info=True)
         return f"Erro ao extrair: Erro do WebDriver ({type(e).__name__}). Verifique a compatibilidade do ChromeDriver e do Chrome."
    except Exception as e:
        logger.error(f"Erro inesperado ao extrair anúncios do Facebook para {instagram_username}: {str(e)}", exc_info=True)
        return f"Erro ao extrair: {str(e)}"
    finally:
        if driver:
            driver.quit()

def extract_google_ads(domain):
    """Extrai o conteúdo do Centro de Transparência de Anúncios do Google usando Selenium e webdriver-manager."""
    if not domain:
        return ""
    driver = None
    try:
        url = f"https://adstransparency.google.com/?region=BR&domain={domain}"
        logger.info(f"Acessando Google Ads Transparency para: {domain} com Selenium. URL: {url}")

        driver = setup_selenium_driver()
        driver.get(url)

        # Espera explícita melhorada
        wait = WebDriverWait(driver, 30) # Timeout de 30 segundos
        logger.info("Aguardando carregamento inicial da página do Google Ads Transparency...")
        
        # Seletor para o corpo da página ou um elemento específico que indica conteúdo carregado
        # Este seletor espera por qualquer um dos textos indicativos ou o rodapé.
        wait.until(
            EC.presence_of_element_located((
                By.XPATH, 
                "//body[contains(.,'anúncio') or contains(.,'Nenhum anúncio') or contains(.,'Todos os formatos')] | //footer | //div[contains(text(), 'Anunciante verificado')]"
            ))
        )
        logger.info("Indicador de carregamento da página detectado.")
        time.sleep(10) # Espera adicional robusta para garantir que todos os scripts JS carreguem e anúncios sejam renderizados.

        text = driver.find_element(By.TAG_NAME, 'body').text
        logger.info(f"Extração do Google Ads Transparency concluída para: {domain}. Tamanho do texto: {len(text)} caracteres.")
        if not text.strip() or len(text.strip()) < 200: # Aumentar o limite mínimo
            logger.warning(f"Texto extraído do Google Ads Transparency para {domain} parece muito curto. HTML da página será retornado.")
            page_html = driver.page_source
            return f"Erro ao extrair: Conteúdo do corpo do texto muito curto. HTML (primeiros 2000 chars): {page_html[:2000]}"
        return text

    except TimeoutException:
        logger.error(f"Timeout ao esperar pelo conteúdo do Google Ads Transparency para {domain}", exc_info=True)
        page_source_on_timeout = ""
        body_text_on_timeout = ""
        try:
            if driver:
                 page_source_on_timeout = driver.page_source
                 body_text_on_timeout = driver.find_element(By.TAG_NAME, 'body').text
                 if body_text_on_timeout and body_text_on_timeout.strip() and len(body_text_on_timeout.strip()) > 100:
                     logger.warning(f"Conteúdo parcial do corpo extraído após timeout para {domain}. Tamanho: {len(body_text_on_timeout)}")
                     return body_text_on_timeout
                 logger.warning(f"Corpo do texto vazio ou muito curto no timeout, mas page_source tem {len(page_source_on_timeout)} caracteres.")
                 return f"Erro ao extrair: Timeout. HTML no momento do timeout (primeiros 2000 chars): {page_source_on_timeout[:2000]}"
        except Exception as inner_e:
             logger.error(f"Erro ao tentar extrair conteúdo parcial após timeout para {domain}: {inner_e}")
        return f"Erro ao extrair: Timeout esperando pelo conteúdo principal. Sem conteúdo recuperável."
    except WebDriverException as e:
         logger.error(f"Erro do WebDriver ao extrair anúncios do Google para {domain}: {str(e)}", exc_info=True)
         return f"Erro ao extrair: Erro do WebDriver ({type(e).__name__}). Verifique a compatibilidade do ChromeDriver e do Chrome."
    except Exception as e:
        logger.error(f"Erro inesperado ao extrair anúncios do Google para {domain}: {str(e)}", exc_info=True)
        return f"Erro ao extrair: {str(e)}"
    finally:
        if driver:
            driver.quit()

# --- Função de Análise com API da OpenAI (Mantida da v1, com pequenos ajustes no prompt) ---
def analyze_ads_with_openai_api(plataforma, conteudo, consulta):
    global client
    if not client:
        logger.error("Cliente OpenAI não inicializado. Verifique a chave API OPENAI_API_KEY.")
        return False
        
    # Checagem mais robusta de conteúdo mínimo e erro explícito
    if not conteudo or "Erro ao extrair:" in conteudo or len(conteudo.strip()) < 150:
        logger.warning(f"Conteúdo inválido, erro na extração ou muito curto para {consulta} na plataforma {plataforma} (tamanho: {len(conteudo)}). Análise de IA abortada.")
        return False

    max_content_length = 15800 # Limite para o prompt, GPT-3.5-turbo tem limite de ~16k tokens, mas o prompt em si consome tokens.
    conteudo_limitado = conteudo[:max_content_length]

    common_instructions = (
        "Responda APENAS com 'Sim' se encontrar anúncios ativos ou 'Não' caso contrário. "
        "Não inclua explicações, justificativas, saudações ou qualquer outro texto. Sua resposta deve ser exclusivamente 'Sim' ou 'Não'."
    )

    if plataforma == "facebook":
        prompt_text = (
            f"Você é um especialista em marketing digital. Analise o seguinte conteúdo da Biblioteca de Anúncios do Facebook e determine se existem anúncios ATIVOS para o usuário/página \'{consulta}\'.\n"
            f"Conteúdo da página (pode estar incompleto, conter ruído, ou ser o HTML da página se a extração de texto falhou parcialmente):\n--- INÍCIO DO CONTEÚDO ---\n{conteudo_limitado}\n--- FIM DO CONTEÚDO ---\n\n"
            f"Procure por indicadores como 'nenhum anúncio encontrado', '0 resultados'."
            f"'0 resultados é o maior indicador de que não há anúncios ativos'. "
            f"Todas as pesquisas terão uma aba escrita 'status online: Anúncios ativos', ou seja, isso não é um indicador de que anúncios estão ativos. "
            f"A presença de elementos como cards de anúncios, botões 'Saiba mais', 'Comprar agora', datas de veiculação recentes, ou textos como 'Anúncios de {consulta}' indicam anúncios ativos. "
            f"Se houver qualquer indicação clara de que anúncios estão sendo veiculados ou foram veiculados recentemente e estão ativos, responda 'Sim'. "
            f"Se houver uma mensagem explícita de que não há anúncios ativos ou nenhum resultado, responda 'Não'. "
            f"Considere o contexto do Brasil. {common_instructions}"
        )
    elif plataforma == "google":
        prompt_text = (
            f"Você é um especialista em marketing digital. Analise o seguinte conteúdo do Centro de Transparência de Anúncios do Google e determine se existem anúncios ATIVOS para o domínio \'{consulta}\'.\n"
            f"Conteúdo da página (pode estar incompleto, conter ruído, ou ser o HTML da página se a extração de texto falhou parcialmente):\n--- INÍCIO DO CONTEÚDO ---\n{conteudo_limitado}\n--- FIM DO CONTEÚDO ---\n\n"
            f"Procure por indicadores como 'Nenhum anúncio encontrado para este anunciante', 'não veiculou anúncios nos últimos tempos'. "
            f"A presença de listagem de anúncios com criativos (imagens, vídeos, texto), datas de veiculação, ou a frase 'Anunciante verificado' acompanhada de anúncios, indica atividade. "
            f"A simples presença de filtros de data ou região não indica anúncios ativos. "
            f"Se houver qualquer indicação clara de que anúncios estão sendo veiculados ou foram veiculados recentemente e estão ativos, responda 'Sim'. "
            f"Se houver uma mensagem explícita de que não há anúncios ativos ou nenhum resultado, responda 'Não'. "
            f"Considere o contexto do Brasil. {common_instructions}"
        )
    else:
        logger.error(f"Plataforma desconhecida para análise de IA: {plataforma}")
        return False

    try:
        logger.info(f"Iniciando análise com OpenAI API para {consulta} na plataforma {plataforma}. Tamanho do conteúdo enviado: {len(conteudo_limitado)}")
        
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo-0125", # Modelo atualizado
            messages=[
                {"role": "system", "content": "Você é um assistente que analisa conteúdo de páginas de bibliotecas de anúncios e responde estritamente com 'Sim' ou 'Não' para indicar se há anúncios ativos."},
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.0,
            max_tokens=10 # Aumentado um pouco para garantir 'Sim' ou 'Não'
        )
        
        result = completion.choices[0].message.content.strip().lower()
        # Remove pontuações comuns que podem vir junto
        result = result.replace('.', '').replace('!', '')
        logger.info(f"Resultado da análise OpenAI API para {consulta} ({plataforma}): '{result}'")
        
        if result == "sim":
            return True
        elif result == "não" or result == "nao":
            return False
        else:
            logger.warning(f"Resposta inesperada da OpenAI API: '{result}'. Considerando como 'Não'. Prompt enviado: {prompt_text[:300]}...")
            return False

    except Exception as e:
        logger.error(f"Erro durante a análise com OpenAI API para {consulta} ({plataforma}): {str(e)}", exc_info=True)
        return False

# --- Função de Verificação QSA (Mantida da v1) ---
def consultar_qsa(cnpj):
    if not cnpj:
        return {"error": "CNPJ não fornecido", "success": False}
    try:
        cnpj_limpo = ''.join(filter(str.isdigit, cnpj))
        if len(cnpj_limpo) != 14:
             return {"error": "CNPJ inválido, deve conter 14 dígitos.", "success": False}

        url = f"https://www.receitaws.com.br/v1/cnpj/{cnpj_limpo}"
        logger.info(f"Consultando QSA para CNPJ: {cnpj_limpo} na URL: {url}")

        max_retries = 2 
        delay = 20 
        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=25) 
                if response.status_code == 429:
                    if attempt < max_retries - 1:
                        logger.warning(f"Rate limit (429) na ReceitaWS. Tentando novamente em {delay}s... (tentativa {attempt + 1}/{max_retries})")
                        time.sleep(delay)
                    else:
                        logger.error("Rate limit (429) na ReceitaWS após múltiplas tentativas.")
                        return {"error": "Serviço de consulta CNPJ temporariamente indisponível (rate limit). Tente mais tarde.", "success": False}
                elif response.status_code == 504: 
                     if attempt < max_retries - 1:
                        logger.warning(f"Gateway Timeout (504) na ReceitaWS. Tentando novamente em {delay}s... (tentativa {attempt + 1}/{max_retries})")
                        time.sleep(delay)
                     else:
                        logger.error("Gateway Timeout (504) na ReceitaWS após múltiplas tentativas.")
                        return {"error": "Serviço de consulta CNPJ indisponível (gateway timeout). Tente mais tarde.", "success": False}
                elif response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "ERROR":
                        logger.warning(f"ReceitaWS retornou erro para {cnpj_limpo}: {data.get('message')}")
                        return {"error": f"Consulta ao CNPJ {cnpj_limpo} retornou: {data.get('message', 'Erro desconhecido da API')}", "success": False, "data": data}

                    logger.info(f"Consulta QSA bem-sucedida para CNPJ: {cnpj_limpo}")
                    qsa_info = {
                        "success": True,
                        "qsa": data.get("qsa", []),
                        "razao_social": data.get("nome", "N/A"),
                        "situacao": data.get("situacao", "N/A"),
                        "atividade_principal": data.get("atividade_principal", [{"text": "N/A"}])[0].get("text"),
                        "data_situacao": data.get("data_situacao", "N/A"),
                        "tipo": data.get("tipo", "N/A"),
                        "telefone": data.get("telefone", "N/A"),
                        "email": data.get("email", "N/A"),
                        "abertura": data.get("abertura", "N/A"),
                        "natureza_juridica": data.get("natureza_juridica", "N/A"),
                        "logradouro": data.get("logradouro", "N/A"),
                        "numero": data.get("numero", "N/A"),
                        "complemento": data.get("complemento", "N/A"),
                        "bairro": data.get("bairro", "N/A"),
                        "municipio": data.get("municipio", "N/A"),
                        "uf": data.get("uf", "N/A"),
                        "cep": data.get("cep", "N/A"),
                        "full_data": data
                    }
                    return qsa_info
                else:
                    logger.error(f"Erro na API da ReceitaWS: {response.status_code} - {response.text[:200]}")
                    error_detail = response.text[:200] if response.text else "Sem detalhes"
                    return {"error": f"Erro ao consultar API da ReceitaWS: status {response.status_code}. Detalhe: {error_detail}", "success": False}
            except requests.exceptions.Timeout:
                 logger.error(f"Timeout na tentativa {attempt + 1} ao consultar QSA para CNPJ: {cnpj}")
                 if attempt < max_retries - 1:
                     time.sleep(10) 
                 else:
                     return {"error": "Erro de conexão com ReceitaWS: Timeout persistente", "success": False}
            except requests.exceptions.RequestException as e:
                 logger.error(f"Erro na requisição QSA (tentativa {attempt + 1}) para CNPJ {cnpj}: {str(e)}")
                 if attempt < max_retries - 1:
                     time.sleep(10)
                 else:
                    return {"error": f"Erro de conexão com ReceitaWS: {str(e)}", "success": False}
        
        return {"error": "Serviço de consulta CNPJ não respondeu após múltiplas tentativas.", "success": False}

    except Exception as e:
        logger.error(f"Erro inesperado ao consultar QSA para CNPJ {cnpj}: {str(e)}", exc_info=True)
        return {"error": f"Erro inesperado no servidor ao processar CNPJ: {str(e)}", "success": False}

# --- Função Principal de Verificações (V2) ---
def run_verification_tasks(instagram_username, domain, cnpj):
    results = {
        "instagram_username": instagram_username,
        "domain": domain,
        "cnpj": cnpj,
        "facebook_ads_status": "not_checked", 
        "google_ads_status": "not_checked",   
        "qsa_status": "not_checked",        
        "qsa_data": None,                   
        "error_messages": [],
        "raw_fb_content_preview": "",
        "raw_google_content_preview": ""
    }

    if instagram_username:
        logger.info(f"Iniciando verificação Facebook Ads para: {instagram_username}")
        fb_content = extract_facebook_ads(instagram_username)
        results["raw_fb_content_preview"] = fb_content[:1000] + ("... (truncado)" if len(fb_content) > 1000 else "")
        if "Erro ao extrair:" in fb_content or not fb_content.strip():
            results["facebook_ads_status"] = "error"
            error_msg = fb_content if "Erro ao extrair:" in fb_content else "Conteúdo não extraído ou vazio."
            results["error_messages"].append(f"Facebook Ads: {error_msg}")
            logger.error(f"Erro na extração do Facebook Ads para {instagram_username}: {error_msg}")
        else:
            logger.info(f"Conteúdo do Facebook Ads extraído para {instagram_username}, enviando para análise OpenAI.")
            has_fb_ads = analyze_ads_with_openai_api("facebook", fb_content, instagram_username)
            results["facebook_ads_status"] = "active" if has_fb_ads else "inactive"
        logger.info(f"Resultado Facebook Ads para {instagram_username}: {results['facebook_ads_status']}")
    else:
        results["facebook_ads_status"] = "not_provided"

    if domain:
        logger.info(f"Iniciando verificação Google Ads para: {domain}")
        google_content = extract_google_ads(domain)
        results["raw_google_content_preview"] = google_content[:1000] + ("... (truncado)" if len(google_content) > 1000 else "")
        if "Erro ao extrair:" in google_content or not google_content.strip():
            results["google_ads_status"] = "error"
            error_msg = google_content if "Erro ao extrair:" in google_content else "Conteúdo não extraído ou vazio."
            results["error_messages"].append(f"Google Ads: {error_msg}")
            logger.error(f"Erro na extração do Google Ads para {domain}: {error_msg}")
        else:
            logger.info(f"Conteúdo do Google Ads extraído para {domain}, enviando para análise OpenAI.")
            has_google_ads = analyze_ads_with_openai_api("google", google_content, domain)
            results["google_ads_status"] = "active" if has_google_ads else "inactive"
        logger.info(f"Resultado Google Ads para {domain}: {results['google_ads_status']}")
    else:
        results["google_ads_status"] = "not_provided"

    if cnpj:
        logger.info(f"Iniciando verificação QSA para: {cnpj}")
        qsa_result = consultar_qsa(cnpj)
        results["qsa_data"] = qsa_result 
        if qsa_result.get("success"):
            results["qsa_status"] = "found"
        elif qsa_result.get("error") and ("inválido" in qsa_result.get("error", "").lower() or "não encontrado" in qsa_result.get("error", "").lower()):
            results["qsa_status"] = "not_found"
            results["error_messages"].append(f"QSA: {qsa_result.get('error', 'CNPJ não encontrado ou inválido')}")
        else:
            results["qsa_status"] = "error"
            results["error_messages"].append(f"QSA: {qsa_result.get('error', 'Erro desconhecido na consulta QSA')}")
        logger.info(f"Resultado QSA para {cnpj}: {results['qsa_status']}")
    else:
        results["qsa_status"] = "not_provided"

    return results

# Exemplo de uso (para teste local, se necessário)
# if __name__ == '__main__':
#     print("--- Iniciando Teste Local de Verificações V2 ---")
#     # Configure o .env com sua OPENAI_API_KEY
#     # test_insta = "metaai" # Usuário do Instagram para teste
#     test_insta = "cocacola_br"
#     test_domain = "cocacola.com.br"  # Domínio para teste
#     # test_cnpj = "00.000.000/0001-91" # CNPJ para teste (exemplo, pode ser inválido)
#     test_cnpj = "45.997.418/0001-53" # Coca-Cola

#     print(f"Testando com Instagram: {test_insta}, Domínio: {test_domain}, CNPJ: {test_cnpj}")
    
#     # Teste apenas Facebook Ads
#     print("\n--- Teste Apenas Facebook Ads ---")
#     fb_content_test = extract_facebook_ads(test_insta)
#     print(f"Preview conteúdo FB ({len(fb_content_test)} chars): {fb_content_test[:500]}")
#     if not "Erro ao extrair:" in fb_content_test and fb_content_test.strip():
#         fb_analise = analyze_ads_with_openai_api("facebook", fb_content_test, test_insta)
#         print(f"Análise FB Ads: {'Ativo' if fb_analise else 'Inativo'}")
#     else:
#         print(f"Erro na extração FB: {fb_content_test}")
#     print("------------------------")

#     # Teste apenas Google Ads
#     # print("\n--- Teste Apenas Google Ads ---")
#     # google_content_test = extract_google_ads(test_domain)
#     # print(f"Preview conteúdo Google ({len(google_content_test)} chars): {google_content_test[:500]}")
#     # if not "Erro ao extrair:" in google_content_test and google_content_test.strip():
#     #     google_analise = analyze_ads_with_openai_api("google", google_content_test, test_domain)
#     #     print(f"Análise Google Ads: {'Ativo' if google_analise else 'Inativo'}")
#     # else:
#     #     print(f"Erro na extração Google: {google_content_test}")
#     # print("------------------------")

#     # resultados_completos = run_verification_tasks(test_insta, test_domain, test_cnpj)
#     # print("\n--- Resultados Finais do Teste ---")
#     # import json
#     # print(json.dumps(resultados_completos, indent=2, ensure_ascii=False))
#     # print("-----------------------------------")

