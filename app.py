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
        # Dica: US para Apple é 'AAPL', Portugal 'EDP.LS', Brasil 'PETR4.SA'
        ticker = st.text_input("Ticker da Ação (ex: AAPL, EDP.LS, PETR4.SA):").upper().strip()
    with col2:
        qtd = st.number_input("Quantidade:", min_value=1, step=1, value=10)

    submitted = st.form_submit_button("Guardar Ação")

    if submitted and ticker:
        st.session_state.carteira.append({"ticker": ticker, "quantidade": qtd})
        st.success(f"{ticker} adicionado com sucesso!")

# --- SECÇÃO 2: Resumo e Dividendos ---
if st.session_state.carteira:
    st.markdown("---")
    st.subheader("📊 A tua Carteira")

    total_acumulado_estimado = 0.0

    for item in st.session_state.carteira:
        simbolo = item["ticker"]
        quantidade = item["quantidade"]

        with st.spinner(f"A carregar dados de {simbolo}..."):
            try:
                stock = yf.Ticker(simbolo)
                info = stock.info
                nome = info.get("shortName", simbolo)
                moeda = info.get("currency", "USD")

                # Procurar dividendo por ação (anualizado ou recente)
                dividend_yield = info.get("dividendYield", 0)
                price = info.get("previousClose", 0) or info.get("currentPrice", 0)

                # Obter histórico de dividendos recente
                div_history = stock.dividends

                st.markdown(f"### {nome} (`{simbolo}`)")
                st.write(f"**Quantidade:** {quantidade} ações")
                st.write(f"**Preço Atual:** {price:.2f} {moeda}")

                if not div_history.empty:
                    ultimo_div = div_history.iloc[-1]
                    ultima_data = div_history.index[-1].strftime("%d/%m/%Y")
                    st.write(f"📅 **Último pagamento:** {ultimo_div:.2f} {moeda}/ação em {ultima_data}")

                    # Estimativa com base no último pagamento
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
