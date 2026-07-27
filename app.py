import datetime
import json
import os
import pandas as pd
import streamlit as st
import yfinance as yf

# Configuração da página para telemóvel/desktop
st.set_page_config(page_title="Meus Dividendos", page_icon="💰", layout="wide")

FICHEIRO_DADOS = "dados_app.json"

# --- FUNÇÕES PARA GUARDAR E CARREGAR DADOS ---
def carregar_dados():
    if os.path.exists(FICHEIRO_DADOS):
        try:
            with open(FICHEIRO_DADOS, "r") as f:
                return json.load(f)
        except Exception:
            return {"users": {}}
    return {"users": {}}

def guardar_dados(dados):
    with open(FICHEIRO_DADOS, "w") as f:
        json.dump(dados, f, indent=4)

# --- INICIALIZAÇÃO DO ESTADO ---
dados_globais = carregar_dados()

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "user_atual" not in st.session_state:
    st.session_state.user_atual = None
if "confirmar_limpar_tudo" not in st.session_state:
    st.session_state.confirmar_limpar_tudo = False

# --- ECRÃ DE LOGIN / REGISTO ---
if not st.session_state.autenticado:
    st.title("💰 Meus Dividendos")
    
    opcao = st.radio("Escolhe uma opção:", ["Entrar (Login)", "Criar Nova Conta"], horizontal=True)

    if opcao == "Entrar (Login)":
        with st.form("login_form"):
            st.subheader("🔒 Entrar na Conta")
            user_input = st.text_input("Utilizador:").strip().lower()
            pass_input = st.text_input("Palavra-passe:", type="password").strip()
            btn_login = st.form_submit_button("Entrar")

            if btn_login:
                if user_input in dados_globais["users"] and dados_globais["users"][user_input]["password"] == pass_input:
                    st.session_state.autenticado = True
                    st.session_state.user_atual = user_input
                    st.success(f"Bem-vindo, {user_input}!")
                    st.rerun()
                else:
                    st.error("Utilizador ou palavra-passe incorretos.")

    else:
        with st.form("registo_form"):
            st.subheader("📝 Criar Nova Conta")
            novo_user = st.text_input("Escolhe um Utilizador:").strip().lower()
            nova_pass = st.text_input("Escolhe uma Palavra-passe:", type="password").strip()
            btn_registo = st.form_submit_button("Criar Conta")

            if btn_registo:
                if not novo_user or not nova_pass:
                    st.warning("Preenche todos os campos!")
                elif novo_user in dados_globais["users"]:
                    st.error("Este utilizador já existe!")
                else:
                    dados_globais["users"][novo_user] = {
                        "password": nova_pass,
                        "contas": ["Geral", "DEGIRO", "Revolut"],
                        "carteira": []
                    }
                    guardar_dados(dados_globais)
                    st.success("Conta criada com sucesso! Mude para a opção 'Entrar (Login)'.")

# --- APLICAÇÃO PRINCIPAL ---
else:
    user = st.session_state.user_atual
    user_data = dados_globais["users"][user]

    # --- MENU LATERAL (ESQUERDA) ---
    st.sidebar.title("📌 Menu")
    st.sidebar.write(f"Utilizador: **{user}** 👋")
    
    if st.sidebar.button("🚪 Sair / Logout"):
        st.session_state.autenticado = False
        st.session_state.user_atual = None
        st.rerun()

    st.sidebar.markdown("---")
    
    # Gestão de Contas no Menu Lateral
    st.sidebar.subheader("🏦 As tuas Contas")
    filtro_conta = st.sidebar.selectbox("🔍 Filtrar Carteira:", ["Todas as Contas"] + user_data["contas"])

    with st.sidebar.expander("⚙️ Criar / Apagar Conta"):
        nova_conta = st.text_input("Nova Conta (ex: Trading212):").strip()
        if st.button("➕ Adicionar"):
            if nova_conta and nova_conta not in user_data["contas"]:
                user_data["contas"].append(nova_conta)
                guardar_dados(dados_globais)
                st.success(f"Conta '{nova_conta}' adicionada!")
                st.rerun()

        st.markdown("---")
        conta_para_apagar = st.selectbox("Selecione para apagar:", ["-- Selecionar --"] + user_data["contas"])
        if conta_para_apagar != "-- Selecionar --":
            st.warning(f"Tem a certeza que quer apagar a conta '{conta_para_apagar}' e as suas ações?")
            if st.button(f"⚠️ Confirmar Apagar '{conta_para_apagar}'"):
                user_data["contas"].remove(conta_para_apagar)
                # Remove ações associadas a essa conta
                user_data["carteira"] = [item for item in user_data["carteira"] if item["conta"] != conta_para_apagar]
                guardar_dados(dados_globais)
                st.success("Conta apagada!")
                st.rerun()

    # --- CONTEÚDO PRINCIPAL (CENTRO) ---
    st.title("💰 Meus Dividendos")

    # SECÇÃO: Adicionar Ação
    st.subheader("➕ Adicionar Ação")
    with st.form("add_stock_form", clear_on_submit=True):
        conta_selecionada = st.selectbox("Escolha a Conta onde comprou:", user_data["contas"])
        
        col1, col2 = st.columns([2, 1])
        with col1:
            ticker_input = st.text_input("Ticker (ex: PETR4, AAPL, EDP.LS):").upper().strip()
        with col2:
            qtd = st.number_input("Quantidade:", min_value=0.0001, step=0.1, value=1.0, format="%.4f")

        submitted = st.form_submit_button("Guardar Ação")

        if submitted and ticker_input:
            if len(ticker_input) >= 5 and ticker_input[-1].isdigit() and not ticker_input.endswith(".SA"):
                ticker_final = f"{ticker_input}.SA"
            else:
                ticker_final = ticker_input

            user_data["carteira"].append({
                "conta": conta_selecionada,
                "ticker": ticker_final,
                "quantidade": float(qtd)
            })
            guardar_dados(dados_globais)
            st.success(f"{ticker_final} adicionado à conta {conta_selecionada}!")

    # SECÇÃO: Exibição da Carteira
    if user_data["carteira"]:
        st.markdown("---")
        st.subheader(f"📊 A tua Carteira ({filtro_conta})")

        if filtro_conta == "Todas as Contas":
            carteira_filtrada = user_data["carteira"]
        else:
            carteira_filtrada = [item for item in user_data["carteira"] if item["conta"] == filtro_conta]

        if not carteira_filtrada:
            st.info(f"Nenhuma ação registada em '{filtro_conta}'.")
        else:
            for item in carteira_filtrada:
                simbolo = item["ticker"]
                quantidade = item["quantidade"]
                conta = item["conta"]

                with st.spinner(f"A carregar {simbolo}..."):
                    try:
                        stock = yf.Ticker(simbolo)
                        info = stock.info
                        nome = info.get("shortName", simbolo)
                        moeda = info.get("currency", "USD")
                        price = info.get("previousClose", 0) or info.get("currentPrice", 0)

                        st.markdown(f"### {nome} (`{simbolo}`)")
                        st.caption(f"🏦 **Conta:** {conta}")
                        st.write(f"**Quantidade:** {quantidade:.4f} ações | **Preço:** {price:.2f} {moeda}")

                        # Tentar obter próxima data ex-dividendo do calendário
                        calendar = stock.calendar
                        proxima_data = None
                        if calendar is not None and isinstance(calendar, dict):
                            if "Ex-Dividend Date" in calendar:
                                proxima_data = calendar["Ex-Dividend Date"]

                        if proxima_data:
                            st.info(f"📅 **Próximo Ex-Dividendo anunciado:** {proxima_data}")
                        else:
                            st.caption("ℹ️ *Próximo dividendo ainda não foi anunciado oficialmente pela empresa.*")

                        # Histórico do último pago
                        div_history = stock.dividends
                        if not div_history.empty:
                            ultimo_div = div_history.iloc[-1]
                            ultima_data = div_history.index[-1].strftime("%d/%m/%Y")
                            total_ultimo = ultimo_div * quantidade
                            st.write(f"💵 **Último dividendo pago:** {ultimo_div:.4f} {moeda}/ação ({ultima_data})")
                            st.success(f"💰 **Total Recebido na Carteira:** {total_ultimo:.2f} {moeda}")
                        
                        st.markdown("---")

                    except Exception as e:
                        st.error(f"Erro ao carregar dados de {simbolo}.")

        # Botão Limpar Carteira com Confirmação
        if not st.session_state.confirmar_limpar_tudo:
            if st.button("🗑️ Limpar Toda a Carteira"):
                st.session_state.confirmar_limpar_tudo = True
                st.rerun()
        else:
            st.warning("⚠️ **Tem a certeza absoluta de que quer APAGAR TODAS as ações da carteira?**")
            col_sim, col_nao = st.columns(2)
            with col_sim:
                if st.button("✔️ Sim, Apagar Tudo"):
                    user_data["carteira"] = []
                    guardar_dados(dados_globais)
                    st.session_state.confirmar_limpar_tudo = False
                    st.success("Carteira limpa com sucesso!")
                    st.rerun()
            with col_nao:
                if st.button("❌ Cancelar"):
                    st.session_state.confirmar_limpar_tudo = False
                    st.rerun()
    else:
        st.info("Adiciona uma ação acima para veres os teus dividendos.")
