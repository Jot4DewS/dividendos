import pandas as pd
import streamlit as st
import yfinance as yf

# Configuração da página para telemóvel
st.set_page_config(page_title="Meus Dividendos", page_icon="💰", layout="centered")

st.title("💰 Meus Dividendos")
st.write("Acompanha os teus rendimentos passivos!")

# Inicializar a carteira na sessão
if "carteira" not in st.session_state:
    st.session_state.carteira = []

# --- SECÇÃO 1: Adicionar Ações ---
st.subheader("➕ Adicionar Ação")
with st.form("add_stock_form", clear_on_submit=True):
    col1, col2 = st.columns([2, 1])
    with col1:
        ticker_input = st.text_input("Ticker (ex: PETR4, AAPL, EDP.LS):").upper().strip()
    with col2:
        # Permitir números decimais para frações de ações (ex: 0.5)
        qtd = st.number_input("Quantidade:", min_value=0.0001, step=0.1, value=1.0, format="%.4f")

    submitted = st.form_submit_button("Guardar Ação")

    if submitted and ticker_input:
        # Ajuda automática: Se for ticker brasileiro comum sem sufixo (ex: PETR4, VALE3, ITUB4)
        if len(ticker_input) >= 5 and ticker_input[-1].isdigit() and not ticker_input.endswith(".SA"):
            ticker_final = f"{ticker_input}.SA"
        else:
            ticker_final = ticker_input

        st.session_state.carteira.append({"ticker": ticker_final, "quantidade": float(qtd)})
        st.success(f"{ticker_final} adicionado com sucesso!")

# --- SECÇÃO 2: Resumo e Dividendos ---
if st.session_state.carteira:
    st.markdown("---")
    st.subheader("📊 A tua Carteira")

    for item in st.session_state.carteira:
        simbolo = item["ticker"]
        quantidade = item["quantidade"]

        with st.spinner(f"A carregar dados de {simbolo}..."):
            try:
                stock = yf.Ticker(simbolo)
                info = stock.info
                nome = info.get("shortName", simbolo)
                moeda = info.get("currency", "USD")

                # Obter preço atual
                price = info.get("previousClose", 0) or info.get("currentPrice", 0)

                # Obter histórico de dividendos recente
                div_history = stock.dividends

                st.markdown(f"### {nome} (`{simbolo}`)")
                st.write(f"**Quantidade:** {quantidade:.4f} ações")
                st.write(f"**Preço Atual:** {price:.2f} {moeda}")

                if not div_history.empty:
                    ultimo_div = div_history.iloc[-1]
                    ultima_data = div_history.index[-1].strftime("%d/%m/%Y")
                    st.write(f"📅 **Último pagamento:** {ultimo_div:.4f} {moeda}/ação em {ultima_data}")

                    # Cálculo exato com a tua quantidade fracionada
                    estimativa_recebimento = ultimo_div * quantidade
                    st.success(f"💵 **A receber (por este pagamento):** {estimativa_recebimento:.2f} {moeda}")
                else:
                    st.info("Nenhum histórico recente de dividendos encontrado.")

                st.markdown("---")

            except Exception as e:
                st.error(f"Erro ao carregar {simbolo}: Verifica se o ticker está correto.")

    if st.button("🗑️ Limpar Carteira"):
        st.session_state.carteira = []
        st.rerun()
else:
    st.info("Adiciona uma ação acima para começares a ver os dividendos.")
