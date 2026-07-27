import datetime
import pandas as pd
import streamlit as st
import streamlit_authenticator as stauth
import yfinance as yf

# Configuração da página para telemóvel
st.set_page_config(page_title="Meus Dividendos", page_icon="💰", layout="centered")

# --- CONFIGURAÇÃO DE LOGIN ---
names = ["Meu Nome"]
usernames = ["utilizador"]
passwords = ["1234"]  # Altera a tua palavra-passe aqui!

hashed_passwords = stauth.Hasher(passwords).generate()

credentials = {
    "usernames": {
        usernames[0]: {
            "name": names[0],
            "password": hashed_passwords[0]
        }
    }
}

authenticator = stauth.Authenticate(
    credentials,
    "dividendos_app_cookie",
    "chave_secreta_12345",
    cookie_expiry_days=30
)

name, authentication_status, username = authenticator.login("Login - Meus Dividendos", "main")

if authentication_status == False:
    st.error("Utilizador ou palavra-passe incorretos.")
elif authentication_status == None:
    st.warning("Por favor, introduz o teu utilizador e palavra-passe.")
elif authentication_status:

    st.sidebar.write(f"Olá, **{name}**! 👋")
    authenticator.logout("Sair / Logout", "sidebar")

    st.title("💰 Meus Dividendos")

    if "contas" not in st.session_state:
        st.session_state.contas = ["Geral", "DEGIRO", "Revolut"]

    if "carteira" not in st.session_state:
        st.session_state.carteira = []

    # --- SECÇÃO 1: Gestão de Contas ---
    with st.expander("⚙️ Gerir Contas / Corretoras"):
        nova_conta = st.text_input("Nome da Nova Conta (ex: Interactive Brokers):").strip()
        if st.button("➕ Adicionar Conta"):
            if nova_conta and nova_conta not in st.session_state.contas:
                st.session_state.contas.append(nova_conta)
                st.success(f"Conta '{nova_conta}' adicionada!")
                st.rerun()

    # --- SECÇÃO 2: Adicionar Ação ---
    st.subheader("➕ Adicionar Ação")
    with st.form("add_stock_form", clear_on_submit=True):
        conta_selecionada = st.selectbox("Escolha a Conta:", st.session_state.contas)
        
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

            st.session_state.carteira.append({
                "conta": conta_selecionada,
                "ticker": ticker_final,
                "quantidade": float(qtd)
            })
            st.success(f"{ticker_final} adicionado à conta **{conta_selecionada}**!")

    # --- SECÇÃO 3: Carteira e Próximos Dividendos ---
    if st.session_state.carteira:
        st.markdown("---")
        st.subheader("📊 A tua Carteira")

        filtro_conta = st.selectbox("🔍 Filtrar por Conta:", ["Todas as Contas"] + st.session_state.contas)

        if filtro_conta == "Todas as Contas":
            carteira_filtrada = st.session_state.carteira
        else:
            carteira_filtrada = [item for item in st.session_state.carteira if item["conta"] == filtro_conta]

        if not carteira_filtrada:
            st.info(f"Nenhuma ação registada na conta '{filtro_conta}'.")
        else:
            for item in carteira_filtrada:
                simbolo = item["ticker"]
                quantidade = item["quantidade"]
                conta = item["conta"]

                with st.spinner(f"A verificar dividendos para {simbolo}..."):
                    try:
                        stock = yf.Ticker(simbolo)
                        info = stock.info
                        nome = info.get("shortName", simbolo)
                        moeda = info.get("currency", "USD")
                        price = info.get("previousClose", 0) or info.get("currentPrice", 0)

                        st.markdown(f"### {nome} (`{simbolo}`)")
                        st.caption(f"🏦 **Conta:** {conta}")
                        st.write(f"**Quantidade:** {quantidade:.4f} ações | **Preço:** {price:.2f} {moeda}")

                        # Procura o calendário de próximos eventos/dividendos
                        calendar = stock.calendar
                        ex_date = None
                        pay_date = None

                        if calendar is not None and not (isinstance(calendar, pd.DataFrame) and calendar.empty):
                            if isinstance(calendar, dict):
                                ex_date = calendar.get("Ex-Dividend Date")
                                pay_date = calendar.get("Dividend Date")

                        # Fallback se a data estiver no 'info'
                        if not ex_date and "exDividendDate" in info and info["exDividendDate"]:
                            ex_date = datetime.datetime.fromtimestamp(info["exDividendDate"]).date()

                        div_history = stock.dividends

                        # Mostrar próximo pagamento (se já anunciado e futuro)
                        if ex_date or pay_date:
                            st.subheader("🔔 Próximo Dividendo Anunciado")
                            if ex_date:
                                st.write(f"📌 **Data Ex-Dividendo:** {ex_date}")
                            if pay_date:
                                st.write(f"💳 **Data de Pagamento:** {pay_date}")

                            if not div_history.empty:
                                valor_por_acao = div_history.iloc[-1]
                                total_estimado = valor_por_acao * quantidade
                                st.success(f"💵 **Valor Estimado a Receber:** {total_estimado:.2f} {moeda} ({valor_por_acao:.4f} {moeda}/ação)")
                        
                        # Histórico recente se não houver novo anúncio pendente
                        elif not div_history.empty:
                            ultimo_div = div_history.iloc[-1]
                            ultima_data = div_history.index[-1].strftime("%d/%m/%Y")
                            total_ultimo = ultimo_div * quantidade
                            st.write(f"📅 **Último dividendo pago:** {ultimo_div:.4f} {moeda}/ação em {ultima_data}")
                            st.info(f"💵 **Recebeste no último pagamento:** {total_ultimo:.2f} {moeda}")
                        else:
                            st.info("Sem anúncios ou histórico recente de dividendos.")

                        st.markdown("---")

                    except Exception as e:
                        st.error(f"Erro ao carregar dados de {simbolo}.")

        if st.button("🗑️ Limpar Toda a Carteira"):
            st.session_state.carteira = []
            st.rerun()
else:
    st.info("Adiciona uma ação acima para começares a ver os teus dividendos.")
