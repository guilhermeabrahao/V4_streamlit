# -*- coding: utf-8 -*-
import streamlit as st
import logging
import os
from dotenv import load_dotenv

# Importar funções de verificação adaptadas
from verifications_streamlit import run_verification_tasks

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente (para OPENAI_API_KEY)
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- Lógica de Pontuação e Qualificação ---
CRITERIA_POINTS = {
    # 1. Faixa de Faturamento
    "faturamento_ate_100k": -100,
    "faturamento_100_200k": -100,
    "faturamento_200_400k": 0,
    "faturamento_401k_1M": 30,
    "faturamento_1M_4M": 30,
    # 2. Produto de Interesse
    "interesse_assessoria": 30,
    "interesse_estruturacao": 10,
    "interesse_alavancagem": 0,
    # 3. Perfil do Contato
    "perfil_nome_completo": 30,
    "perfil_linkedin": 30,
    "perfil_cargo_estrategico": 30,
    "perfil_cargo_tatico": 20,
    "perfil_cargo_operacional": 0,
    # 4. Qualidade do Contato
    "contato_email_corp": 10,
    "contato_email_pessoal": 0,
    # 5. Estrutura Digital
    "digital_site_funcional": 30,
    "digital_site_fora_ar": -20,
    "digital_produto_sinergia": 20,
    # 6. Redes Sociais
    "social_insta_site": 5,
    "social_insta_google": 10,
    "social_insta_5k": 20,
    "social_sem_presenca": -20,
    # 7. Validação da Empresa
    "validacao_cnpj_localizado": 10,
    "validacao_pessoa_qsa": 30,
    "validacao_nome_generico": -30,
    # 8. Urgência
    "urgencia_imediata": 20,
    "urgencia_3_meses": 10,
    "urgencia_nao_informada": 0,
    # 9. Investimento Atual
    "investimento_google_meta": 30,
    "investimento_google": 20,
    "investimento_meta": 20,
    # 10. Confirmações Manuais
    "manual_verificado_maps": 20,
    "manual_redirecionado_assessoria": 15
}

def calculate_score(checklist_data, verification_results):
    total = 0
    logger.info(f"Calculando pontuação com checklist: {checklist_data}")
    logger.info(f"Resultados da verificação para pontuação: {verification_results}")

    for key, value in checklist_data.items():
        if key in CRITERIA_POINTS and value:
            total += CRITERIA_POINTS.get(key, 0)
            logger.info(f"Checklist item: \"{key}\" (Valor: {value}) adicionou {CRITERIA_POINTS.get(key, 0)}. Total parcial: {total}")

    logger.info(f"Pontuação após checklist manual: {total}")

    if verification_results.get("qsa_status") == "found":
        total += CRITERIA_POINTS["validacao_cnpj_localizado"]
        logger.info(f"QSA encontrado, adicionado {CRITERIA_POINTS['validacao_cnpj_localizado']} por CNPJ localizado. Total parcial: {total}")
        qsa_data = verification_results.get("qsa_data", {})
        if qsa_data and qsa_data.get("qsa") and len(qsa_data.get("qsa", [])) > 0:
            total += CRITERIA_POINTS["validacao_pessoa_qsa"]
            logger.info(f"Pessoas no QSA, adicionado {CRITERIA_POINTS['validacao_pessoa_qsa']}. Total parcial: {total}")

    google_active = verification_results.get("google_ads_status") == "active"
    fb_active = verification_results.get("facebook_ads_status") == "active"

    if google_active and fb_active:
        total += CRITERIA_POINTS["investimento_google_meta"]
        logger.info(f"Google e Meta Ads ativos, adicionado {CRITERIA_POINTS['investimento_google_meta']}. Total parcial: {total}")
    elif google_active:
        total += CRITERIA_POINTS["investimento_google"]
        logger.info(f"Google Ads ativo, adicionado {CRITERIA_POINTS['investimento_google']}. Total parcial: {total}")
    elif fb_active:
        total += CRITERIA_POINTS["investimento_meta"]
        logger.info(f"Meta Ads ativo, adicionado {CRITERIA_POINTS['investimento_meta']}. Total parcial: {total}")

    logger.info(f"Pontuação final após verificações automáticas: {total}")
    return total

def determine_qualification(score, valor_inicial, valor_atual):
    qualification = {
        "status": "descartar",
        "message": "🔴 Descartar Lead",
        "teto": 0,
        "show_teto": False,
        "alert": None
    }
    teto = 0
    valor_inicial_num = float(valor_inicial) if valor_inicial else 0
    valor_atual_num = float(valor_atual) if valor_atual else 0

    if score >= 130:
        teto = valor_inicial_num * 1.8
        qualification["status"] = "comprar"
        qualification["message"] = f"🟢 COMPRE JÁ liberado (Teto Sugerido: R$ {teto:.2f})"
        qualification["show_teto"] = True
    elif score >= 100:
        teto = valor_inicial_num * 1.3
        qualification["status"] = "acompanhar_alto"
        qualification["message"] = f"🟡 Acompanhar (Teto Sugerido: R$ {teto:.2f})"
        qualification["show_teto"] = True
    elif score >= 80:
        teto = valor_inicial_num
        qualification["status"] = "acompanhar_baixo"
        qualification["message"] = f"⚠️ Acompanhar (Teto Sugerido: R$ {teto:.2f})"
        qualification["show_teto"] = True

    qualification["teto"] = teto

    if valor_atual_num > teto and score >= 80 and teto > 0:
        qualification["alert"] = f"❗ Valor atual (R$ {valor_atual_num:.2f}) ultrapassou teto sugerido (R$ {teto:.2f}). Reavaliar risco!"

    logger.info(f"Resultado da qualificação: {qualification}")
    return qualification

# --- Interface Streamlit ---
st.set_page_config(layout="wide")
st.title("Verificador de Leads V4 Company")

if not OPENAI_API_KEY:
    st.error("Chave da API OpenAI (OPENAI_API_KEY) não encontrada. Configure-a no arquivo .env ou como variável de ambiente para habilitar a análise de anúncios.")

# Usar colunas para layout principal: Dados à esquerda, Checklist à direita
main_col1, main_col2 = st.columns([0.4, 0.6]) # Ajustar proporções conforme necessário

with main_col1:
    st.header("📊 Dados do Lead e Leilão")
    with st.container(border=True):
        instagram_username = st.text_input("👤 Instagram (usuário)", key="instagram_username", placeholder="Ex: nomeusuario", help="Nome de usuário do Instagram para análise de Meta Ads.")
        domain = st.text_input("🌐 Website (domínio)", key="domain", placeholder="Ex: nomedaempresa.com.br", help="Domínio para análise de Google Ads.")
        cnpj = st.text_input("🏢 CNPJ", key="cnpj", placeholder="00.000.000/0000-00", help="CNPJ para consulta de QSA na ReceitaWS.")
        
        st.subheader("💰 Valores do Leilão")
        val_col1, val_col2 = st.columns(2)
        with val_col1:
            valor_inicial = st.number_input("Valor Inicial (R$)", key="valorInicial", min_value=0.0, value=100.0, format="%.2f")
        with val_col2:
            valor_atual = st.number_input("Valor Atual (R$)", key="valorAtual", min_value=0.0, value=100.0, format="%.2f")

# Dicionários para mapear labels para chaves (para consistência com CRITERIA_POINTS)
# Estes devem corresponder aos `value` do HTML original
FATURAMENTO_MAP = {
    "Não informado/Não se aplica": "faturamento_nao_informado",
    "Até R$100k (-100)": "faturamento_ate_100k", 
    "R$100k a R$200k (-100)": "faturamento_100_200k", 
    "R$200k a R$400k (0)": "faturamento_200_400k", 
    "R$401k a R$1M (+30)": "faturamento_401k_1M", 
    "R$1M a R$4M (+30)": "faturamento_1M_4M"
}
INTERESSE_MAP = {
    "Não informado/Outro": "interesse_outro",
    "Assessoria (+30)": "interesse_assessoria", 
    "Estruturação (+10)": "interesse_estruturacao", 
    "Alavancagem (0)": "interesse_alavancagem"
}
CARGO_MAP = {
    "Não informado/Não se aplica": "perfil_cargo_nao_informado",
    "Estratégico (+30)": "perfil_cargo_estrategico", 
    "Tático (+20)": "perfil_cargo_tatico", 
    "Operacional (0)": "perfil_cargo_operacional"
}
EMAIL_MAP = {
    "Não informado": "contato_email_nao_informado",
    "E-mail corporativo (+10)": "contato_email_corp", 
    "E-mail pessoal (0)": "contato_email_pessoal"
}
SITE_STATUS_MAP = {
    "Não verificado/Não se aplica": "digital_site_nao_verificado",
    "Site funcional (+30)": "digital_site_funcional", 
    "Site fora do ar (-20)": "digital_site_fora_ar"
}
URGENCIA_MAP = {
    "Não informada (0)": "urgencia_nao_informada",
    "Imediata (+20)": "urgencia_imediata", 
    "Até 3 meses (+10)": "urgencia_3_meses"
}

with main_col2:
    st.header("📋 Checklist de Qualificação Manual")
    checklist_data_manual = {}
    with st.container(border=True):
        with st.expander("1. Faixa de Faturamento", expanded=True):
            faturamento_label = st.radio("Selecione a faixa:", list(FATURAMENTO_MAP.keys()), key="faturamento_group", horizontal=True, label_visibility="collapsed")
            checklist_data_manual["faturamento_selected_key"] = FATURAMENTO_MAP[faturamento_label]

        with st.expander("2. Produto de Interesse", expanded=True):
            interesse_label = st.radio("Selecione o produto:", list(INTERESSE_MAP.keys()), key="interesse_group", horizontal=True, label_visibility="collapsed")
            checklist_data_manual["interesse_selected_key"] = INTERESSE_MAP[interesse_label]

        with st.expander("3. Perfil do Contato", expanded=True):
            checklist_data_manual["perfil_nome_completo"] = st.checkbox("Nome completo (+30)", key="perfil_nome_completo")
            checklist_data_manual["perfil_linkedin"] = st.checkbox("LinkedIn (+30)", key="perfil_linkedin")
            st.markdown("**Cargo do Contato:**")
            cargo_label = st.radio("Selecione o cargo:", list(CARGO_MAP.keys()), key="cargo_group", horizontal=True, label_visibility="collapsed")
            checklist_data_manual["cargo_selected_key"] = CARGO_MAP[cargo_label]

        with st.expander("4. Qualidade do Contato", expanded=True):
            email_label = st.radio("Tipo de E-mail Principal:", list(EMAIL_MAP.keys()), key="email_group", horizontal=True, label_visibility="collapsed")
            checklist_data_manual["email_selected_key"] = EMAIL_MAP[email_label]

        with st.expander("5. Estrutura Digital", expanded=True):
            site_status_label = st.radio("Status do Site da Empresa:", list(SITE_STATUS_MAP.keys()), key="site_status_group", horizontal=True, label_visibility="collapsed")
            checklist_data_manual["site_status_selected_key"] = SITE_STATUS_MAP[site_status_label]
            checklist_data_manual["digital_produto_sinergia"] = st.checkbox("Sinergia produto/site (+20)", key="digital_produto_sinergia")

        with st.expander("6. Redes Sociais", expanded=True):
            checklist_data_manual["social_insta_site"] = st.checkbox("Instagram no site (+5)", key="social_insta_site")
            checklist_data_manual["social_insta_google"] = st.checkbox("Instagram no Google (+10)", key="social_insta_google")
            checklist_data_manual["social_insta_5k"] = st.checkbox("Instagram +5k seguidores (+20)", key="social_insta_5k")
            checklist_data_manual["social_sem_presenca"] = st.checkbox("Sem presença digital (-20)", key="social_sem_presenca")

        with st.expander("7. Validação Empresa (Manual)", expanded=True):
            checklist_data_manual["validacao_nome_generico"] = st.checkbox("Nome genérico (-30)", key="validacao_nome_generico")
            st.caption("CNPJ e QSA pontuam automaticamente se encontrados.")

        with st.expander("8. Urgência", expanded=True):
            urgencia_label = st.radio("Urgência para Contratação:", list(URGENCIA_MAP.keys()), key="urgencia_group", horizontal=True, label_visibility="collapsed")
            checklist_data_manual["urgencia_selected_key"] = URGENCIA_MAP[urgencia_label]

        with st.expander("9. Investimento Atual", expanded=True):
            st.caption("Pontuação automática baseada na verificação de anúncios Google/Meta.")

        with st.expander("10. Confirmações Manuais", expanded=True):
            checklist_data_manual["manual_verificado_maps"] = st.checkbox("Verificado (Maps, etc.) (+20)", key="manual_verificado_maps")
            checklist_data_manual["manual_redirecionado_assessoria"] = st.checkbox("Pode ir p/ Assessoria (+15)", key="manual_redirecionado_assessoria")

st.divider()

# Botão de Ação Principal Centralizado
btn_cols = st.columns([0.3, 0.4, 0.3])
with btn_cols[1]:
    if st.button(" Analisar Lead Agora! ", key="calculateButton", use_container_width=True, type="primary"):
        if not instagram_username and not domain and not cnpj:
            st.warning("Por favor, forneça pelo menos um Instagram, Domínio ou CNPJ para análise.")
        elif not OPENAI_API_KEY and (instagram_username or domain):
            st.error("A análise de anúncios (Instagram/Google) requer a chave OPENAI_API_KEY. Verifique a configuração.")
        else:
            # Construir o checklist_data final para a função calculate_score
            final_checklist = {}
            for key, value in checklist_data_manual.items():
                if key.endswith("_selected_key"):
                    # Para radios, a chave selecionada recebe True
                    if value not in ["faturamento_nao_informado", "interesse_outro", "perfil_cargo_nao_informado", "contato_email_nao_informado", "digital_site_nao_verificado"]:
                        final_checklist[value] = True
                else:
                    # Para checkboxes, o valor booleano é usado diretamente
                    final_checklist[key] = value
            logger.info(f"Checklist data (v2) a ser usado no cálculo: {final_checklist}")

            with st.spinner("Analisando o lead... Isso pode levar alguns minutos, especialmente as verificações de anúncios. ⏳"):
                try:
                    verification_results = run_verification_tasks(instagram_username, domain, cnpj)
                    score = calculate_score(final_checklist, verification_results)
                    qualification = determine_qualification(score, valor_inicial, valor_atual)

                    # Exibição dos Resultados em Abas
                    st.header("📈 Resultados da Análise do Lead")
                    tab_resumo, tab_verificacoes, tab_qsa_detalhes, tab_debug = st.tabs([
                        "🎯 Resumo da Qualificação", 
                        "🔎 Status das Verificações", 
                        "📄 Detalhes do CNPJ/QSA", 
                        "🐞 Dados Brutos (Debug)"
                    ])

                    with tab_resumo:
                        st.subheader("🎯 Qualificação Final")
                        st.metric(label="Pontuação Total", value=f"{score} pontos")
                        
                        if qualification["status"] == "comprar":
                            st.success(qualification["message"])
                        elif "acompanhar" in qualification["status"]:
                            st.warning(qualification["message"])
                        else:  # descartar
                            st.error(qualification["message"])
                        
                        if qualification["show_teto"] and qualification["teto"] > 0:
                            st.info(f"Teto Sugerido para Leilão: R$ {qualification['teto']:.2f}")
                        
                        if qualification["alert"]:
                            st.error(f"🚨 ALERTA: {qualification['alert']}")

                    with tab_verificacoes:
                        st.subheader("🔎 Status das Verificações Automáticas")
                        if instagram_username:
                            status_fb = verification_results.get("facebook_ads_status", "not_checked")
                            if status_fb == "active":
                                st.success(f"Meta Ads (Instagram: {instagram_username}): 🟢 Anúncios Ativos Encontrados")
                            elif status_fb == "inactive":
                                st.warning(f"Meta Ads (Instagram: {instagram_username}): 🟡 Não há Anúncios Ativos")
                            elif status_fb == "error":
                                st.error(f"Meta Ads (Instagram: {instagram_username}): 🔴 Erro - {verification_results.get('error_messages', [])}")
                            else:
                                st.info(f"Meta Ads (Instagram: {instagram_username}): ℹ️ Não verificado ou não fornecido.")
                        else:
                            st.info("Meta Ads (Instagram): ℹ️ Não fornecido.")
                        
                        if domain:
                            status_google = verification_results.get("google_ads_status", "not_checked")
                            if status_google == "active":
                                st.success(f"Google Ads (Domínio: {domain}): 🟢 Anúncios Ativos Encontrados")
                            elif status_google == "inactive":
                                st.warning(f"Google Ads (Domínio: {domain}): 🟡 Não há Anúncios Ativos")
                            elif status_google == "error":
                                st.error(f"Google Ads (Domínio: {domain}): 🔴 Erro - {verification_results.get('error_messages', [])}")
                            else:
                                st.info(f"Google Ads (Domínio: {domain}): ℹ️ Não verificado ou não fornecido.")
                        else:
                            st.info("Google Ads (Domínio): ℹ️ Não fornecido.")
                        
                        if cnpj:
                            status_qsa = verification_results.get("qsa_status", "not_checked")
                            qsa_data_res = verification_results.get("qsa_data", {})
                            if status_qsa == "found":
                                st.success(f"Consulta CNPJ ({cnpj}): 🟢 Encontrado e Válido")
                            elif status_qsa == "not_found":
                                st.warning(f"Consulta CNPJ ({cnpj}): 🟡 Não Encontrado ou Inválido - {qsa_data_res.get('error', '')}")
                            elif status_qsa == "error":
                                st.error(f"Consulta CNPJ ({cnpj}): 🔴 Erro - {qsa_data_res.get('error', 'Erro desconhecido')}")
                            else:
                                st.info(f"Consulta CNPJ ({cnpj}): ℹ️ Não verificado ou não fornecido.")
                        else:
                            st.info("Consulta CNPJ: ℹ️ Não fornecido.")

                    with tab_qsa_detalhes:
                        st.subheader("📄 Detalhes do CNPJ (ReceitaWS)")
                        qsa_data = verification_results.get("qsa_data")
                        if cnpj and qsa_data and qsa_data.get("success"):
                            st.write(f"**Razão Social:** {qsa_data.get('razao_social', 'N/A')}")
                            st.write(f"**Situação Cadastral:** {qsa_data.get('situacao', 'N/A')} (Data: {qsa_data.get('data_situacao', 'N/A')})")
                            st.write(f"**Abertura:** {qsa_data.get('abertura', 'N/A')}")
                            st.write(f"**Tipo:** {qsa_data.get('tipo', 'N/A')}")
                            st.write(f"**Natureza Jurídica:** {qsa_data.get('natureza_juridica', 'N/A')}")
                            st.write(f"**Atividade Principal:** {qsa_data.get('atividade_principal', 'N/A')}")
                            st.write(f"**Endereço:** {qsa_data.get('logradouro', '')}, {qsa_data.get('numero', '')} {qsa_data.get('complemento', '')} - {qsa_data.get('bairro', '')} - {qsa_data.get('municipio', '')}/{qsa_data.get('uf', '')} - CEP: {qsa_data.get('cep', '')}")
                            st.write(f"**Telefone:** {qsa_data.get('telefone', 'N/A')}")
                            st.write(f"**Email:** {qsa_data.get('email', 'N/A')}")
                            if qsa_data.get("qsa"): 
                                with st.expander("Quadro de Sócios e Administradores (QSA)"):
                                    for socio in qsa_data.get("qsa", []):
                                        st.write(f"- {socio.get('nome', 'Nome não informado')} ({socio.get('qual', 'Qualificação não informada')})")
                            else:
                                st.write("QSA não disponível ou não encontrado.")
                        elif cnpj:
                            st.warning(f"Não foi possível exibir detalhes do CNPJ. Status da consulta: {verification_results.get('qsa_status', 'N/A')}")
                        else:
                            st.info("CNPJ não fornecido.")
                    
                    with tab_debug:
                        st.subheader("🐞 Dados Brutos para Debug")
                        with st.expander("Checklist Data Enviado para Cálculo"):
                            st.json(final_checklist)
                        with st.expander("Resultados Completos da Verificação (JSON)"):
                            st.json(verification_results)
                        with st.expander("Preview Conteúdo Meta Ads (Raspagem)"):
                            st.text(verification_results.get("raw_fb_content_preview", "Nenhum preview disponível."))
                        with st.expander("Preview Conteúdo Google Ads (Raspagem)"):
                            st.text(verification_results.get("raw_google_content_preview", "Nenhum preview disponível."))

                except RuntimeError as e_runtime:
                    st.error(f"Ocorreu um erro crítico durante a execução (RuntimeError): {e_runtime}. Verifique se o ChromeDriver está instalado e configurado corretamente no ambiente, e se a internet está acessível.")
                    logger.error(f"RuntimeError na aplicação Streamlit (v2): {e_runtime}", exc_info=True)
                except Exception as e_general:
                    st.error(f"Ocorreu um erro inesperado: {e_general}")
                    logger.error(f"Erro inesperado na aplicação Streamlit (v2): {e_general}", exc_info=True)
    else:
        st.info("Preencha os dados do lead e o checklist, depois clique em 'Analisar Lead Agora!'.")
