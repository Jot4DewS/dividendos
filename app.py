import streamlit as st
import yfinance as yf
import pandas as pd
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

# Configuração da página para telemóvel
st.set_page_config(page_title="Meus Dividendos", page_icon="💰", layout="centered")

# --- SISTEMA DE AUTENTICAÇÃO SIMPLES ---
if "users" not in st.session_state:
    # Utilizador padrão para testes (Username: admin | Password: 123)
    st.session_state.users = {
        "admin": {"name": "Investidor", "password": "123"}
    }

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None

# --- ECRÃ DE LOGIN / REGISTO ---
if not st.session_state.logged_in:
    st.title("🔐 Acesso aos Dividendos")
    
    tab_login, tab_register = st.tabs(["Entrar", "Criar Conta"])

    with tab_login:
        with st.form("login_form"):
            user = st.text_input("Utilizador:").strip()
            password = st.text_input("Palavra-passe:", type="password").strip()
            submit_login = st.form_submit_button("Entrar")

            if submit_login:
                if user in st.session_state.users and st.session_state.users[user]["password"] == password:
                    st.session_state.logged_in = True
                    st.session_state.username = user
                    st.success(f"Bem-vindo, {st.session_state.users[user]['name']}!")
                    st.rerun()
                else:
                    st.error("Utilizador ou palavra-passe incorretos.")

    with tab_register:
        with st.form("register_form"):
            new_user = st.text_input("Novo Utilizador (ex: joao):").strip()
            new_name = st.text_input("O teu Nome:").strip()
            new_pass = st.text_input("Nova Palavra-passe:", type="password").strip()
            submit_reg = st.form_submit_button("Criar Conta")

            if submit_reg:
                if new_user in st.session_state.users:
                    st.warning("Este utilizador já existe!")
                elif new_user and new_pass:
                    st.session_state.users[new_user] = {"name": new_name, "password": new_pass}
                    st.success("Conta criada com sucesso! Já podes fazer login no outro separador.")
                else:
                    st.error("Preenche todos os campos.")

    st.stop() # Interrompe a execução para não mostrar a app a quem não está logado

# ==========================================
# 🚀 APLICAÇÃO PRINCIPAL (SÓ PARA UTILIZADORES LOGADOS)
# ==========================================

# Botão de Logout no topo
col_user, col_logout = st.columns([3, 1])
with col_user:
    st.write(f"👤 *Sessão iniciada como:* **{st.session_state.users[st.session_state.username]['name']}**")
with col_logout:
    if st.button("Sair"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.rerun()

st.title("💰 Meus Dividendos")

# --- DADOS DO UTILIZADOR (Isolados por conta de login) ---
user_key_carteira = f"carteira_{st.session_state.username}"
user_key_contas = f"contas_{st.session_state.username}"

if user_key_contas not in st.session_state:
    st.session_state[user_key_contas] = ["Geral", "DEGIRO", "Revolut"]

if user_key_carteira not in st.session_state:
    st.session_state[user_key_carteira] = []

# --- SECÇÃO 1: Gestão de Contas / Corretoras ---
with st.expander("⚙️ Gerir Contas / Corretoras"):
    nova_conta = st.text_input("Nome da Nova Conta (ex: Interactive Brokers):").strip()
    if st.button("➕ Adicionar Conta"):
        if nova_conta and nova_conta not in st.session_state[user_key_contas]:
            st.session_state[user_key_contas].append(nova_conta)
            st.success(f"Conta '{nova_conta}' adicionada!")
            st.rerun()

# --- SECÇÃO 2: Adicionar Ação ---
st.subheader("➕ Adicionar Ação")
with st.form("add_stock_form", clear_on_submit=True):
    conta_selecionada = st.selectbox("Escolha a Conta:", st.session_state[user_key_contas])
    
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

        st.session_state[user_key_carteira].append({
            "conta": conta_selecionada,
            "ticker": ticker_final,
            "quantidade": float(qtd)
        })
        st.success(f"{ticker_final} adicionado!")

# --- SECÇÃO 3: Visualização da Carteira ---
carteira_atual = st.session_state[user_key_carteira]

if carteira_atual:
    st.markdown("---")
    st.subheader("📊 A tua Carteira")

    filtro_conta = st.selectbox("🔍 Filtrar por Conta:", ["Todas as Contas"] + st.session_state[user_key_contas])

    if filtro_conta == "Todas as Contas":
        carteira_filtrada = carteira_atual
    else:
        carteira_filtrada = [item for item in carteira_atual if item["conta"] == filtro_conta]

    if not carteira_filtrada:
        st.info(f"Nenhuma ação registada na conta '{filtro_conta}'.")
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
                    div_history = stock.dividends

                    st.markdown(f"### {nome} (`{simbolo}`)")
                    st.caption(f"🏦 **Conta:** {conta}")
                    st.write(f"**Quantidade:** {quantidade:.4f} ações")
                    st.write(f"**Preço Atual:** {price:.2f} {moeda}")

                    if not div_history.empty:
                        ultimo_div = div_history.iloc[-1]
                        ultima_data = div_history.index[-1].strftime("%d/%m/%Y")
                        st.write(f"📅 **Último pagamento:** {ultimo_div:.4f} {moeda}/ação em {ultima_data}")

                        estimativa_recebimento = ultimo_div * quantidade
                        st.success(f"💵 **A receber (por este pagamento):** {estimativa_recebimento:.2f} {moeda}")
                    else:
                        st.info("Nenhum histórico recente de dividendos encontrado.")

                    st.markdown("---")

                except Exception as e:
                    st.error(f"Erro ao carregar {simbolo}: Verifica se o ticker está correto.")

    if st.button("🗑️ Limpar a minha Carteira"):
        st.session_state[user_key_carteira] = []
        st.rerun()
else:
    st.info("Adiciona uma ação acima para começares a ver os teus dividendos.")
