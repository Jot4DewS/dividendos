import datetime
import json
import os
import pandas as pd
import plotly.express as px
import streamlit as st
import yfinance as yf

# Configuração da página
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

    # --- PROCESSAMENTO INICIAL DOS DADOS DA CARTEIRA ---
    hoje = datetime.date.today()
    carteira_completa = user_data["carteira"]
    
    dados_graficos_globais = []
    lista_acoes_processadas = []

    for item in carteira_completa:
        simbolo = item["ticker"]
        quantidade = item["quantidade"]
        conta = item["conta"]

        try:
            stock = yf.Ticker(simbolo)
            info = stock.info
            nome = info.get("shortName", simbolo)
            moeda = info.get("currency", "USD")
            price = info.get("previousClose", 0) or info.get("currentPrice", 0)
            valor_total = price * quantidade

            # Obter último dividendo pago
            div_history = stock.dividends
            ultimo_div_val = 0
            ultimo_div_data = None
            if not div_history.empty:
                ultimo_div_val = float(div_history.iloc[-1])
                ultimo_div_data = div_history.index[-1].strftime("%d/%m/%Y")

            total_dividendos_recebidos = ultimo_div_val * quantidade

            # Obter Próximo Dividendo
            calendar = stock.calendar
            proxima_data = None
            if calendar is not None and isinstance(calendar, dict):
                ex_div = calendar.get("Ex-Dividend Date")
                if ex_div:
                    if isinstance(ex_div, (datetime.datetime, pd.Timestamp)):
                        ex_div = ex_div.date()
                    elif isinstance(ex_div, str):
                        try:
                            ex_div = datetime.datetime.strptime(ex_div, "%Y-%m-%d").date()
                        except Exception:
                            pass
                    if isinstance(ex_div, datetime.date) and ex_div >= hoje:
                        proxima_data = ex_div

            dado = {
                "ticker": simbolo,
                "nome": nome,
                "conta": conta,
                "quantidade": quantidade,
                "preco": price,
                "valor_total": valor_total,
                "moeda": moeda,
                "proxima_data": proxima_data,
                "ultimo_div_val": ultimo_div_val,
                "ultimo_div_data": ultimo_div_data,
                "total_dividendos": total_dividendos_recebidos
            }
            dados_graficos_globais.append(dado)
        except Exception:
            pass

    # --- MENU LATERAL (ESQUERDA) ---
    st.sidebar.title("📌 Menu")
    st.sidebar.write(f"Utilizador: **{user}** 👋")
    
    if st.sidebar.button("🚪 Sair / Logout"):
        st.session_state.autenticado = False
        st.session_state.user_atual = None
        st.rerun()

    st.sidebar.markdown("---")
    
    # Gestão de Contas
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
            st.warning(f"Tem a certeza que quer apagar a conta '{conta_para_apagar}'?")
            if st.button(f"⚠️ Confirmar Apagar '{conta_para_apagar}'"):
                user_data["contas"].remove(conta_para_apagar)
                user_data["carteira"] = [item for item in user_data["carteira"] if item["conta"] != conta_para_apagar]
                guardar_dados(dados_globais)
                st.success("Conta apagada!")
                st.rerun()

    # MINI-GRÁFICO DE DIVIDENDOS (INCOMES) NO MENU LATERAL
    if dados_graficos_globais:
        st.sidebar.markdown("---")
        st.sidebar.subheader("💵 Income Dividendos")
        df_sidebar = pd.DataFrame(dados_graficos_globais)
        
        fig_sidebar = px.bar(
            df_sidebar,
            x="ticker",
            y="total_dividendos",
            text="total_dividendos",
            labels={"ticker": "Ação", "total_dividendos": "Income ($)"},
            color="ticker",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_sidebar.update_traces(
            texttemplate="%{text:.2f}$",
            textposition="outside"
        )
        fig_sidebar.update_layout(
            height=200,
            showlegend=False,
            margin=dict(t=10, b=10, l=10, r=10),
            xaxis_title=None,
            yaxis_title=None
        )
        st.sidebar.plotly_chart(fig_sidebar, use_container_width=True)

    # --- CONTEÚDO PRINCIPAL ---
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

            # Soma quantidade se já existir na mesma conta
            encontrado = False
            for item in user_data["carteira"]:
                if item["ticker"] == ticker_final and item["conta"] == conta_selecionada:
                    item["quantidade"] += float(qtd)
                    encontrado = True
                    break

            if not encontrado:
                user_data["carteira"].append({
                    "conta": conta_selecionada,
                    "ticker": ticker_final,
                    "quantidade": float(qtd)
                })

            guardar_dados(dados_globais)
            st.success(f"{ticker_final} atualizado na conta {conta_selecionada}!")
            st.rerun()

    # SECÇÃO: Exibição da Carteira
    if dados_graficos_globais:
        st.markdown("---")
        st.subheader(f"📊 A tua Carteira ({filtro_conta})")

        if filtro_conta == "Todas as Contas":
            dados_filtrados = dados_graficos_globais
        else:
            dados_filtrados = [item for item in dados_graficos_globais if item["conta"] == filtro_conta]

        if not dados_filtrados:
            st.info(f"Nenhuma ação registada em '{filtro_conta}'.")
        else:
            # DISPLAY: Divisão em 2 colunas (Esquerda: Gráfico Pequeno Donut, Direita: Ações)
            col_grafico, col_lista = st.columns([0.8, 1.2])

            with col_grafico:
                df_grafico = pd.DataFrame(dados_filtrados)
                total_patrimonio = df_grafico["valor_total"].sum()
                moeda_pred = df_grafico["moeda"].iloc[0] if not df_grafico.empty else "USD"

                fig = px.pie(
                    df_grafico,
                    values="valor_total",
                    names="ticker",
                    hole=0.6,
                    color_discrete_sequence=px.colors.qualitative.Bold
                )
                
                # MOSTRAR VALOR EXATO EM VEZ DE PERCENTAGEM
                fig.update_traces(
                    textposition="inside",
                    texttemplate="<b>%{label}</b><br>%{value:.2f}",
                    hovertemplate="<b>%{label}</b><br>Valor: %{value:.2f} " + moeda_pred + "<extra></extra>"
                )
                
                # GRÁFICO MAIS PEQUENO (height=280)
                fig.update_layout(
                    height=280,
                    annotations=[{
                        "text": f"<b>Total</b><br>{total_patrimonio:.2f} {moeda_pred}",
                        "x": 0.5, "y": 0.5, "font_size": 15, "showarrow": False
                    }],
                    showlegend=False,
                    margin=dict(t=10, b=10, l=10, r=10)
                )
                st.plotly_chart(fig, use_container_width=True)

            with col_lista:
                for acao in dados_filtrados:
                    st.markdown(f"### {acao['nome']} (`{acao['ticker']}`)")
                    st.caption(f"🏦 **Conta:** {acao['conta']}")
                    st.write(f"**Quantidade:** {acao['quantidade']:.4f} ações | **Preço:** {acao['preco']:.2f} {acao['moeda']}")

                    if acao['proxima_data']:
                        st.info(f"🔮 **Próximo Dividendo:** Ex-Dividendo em {acao['proxima_data'].strftime('%d/%m/%Y')}")
                    else:
                        st.caption("ℹ️ *Próximo dividendo ainda não foi anunciado.*")

                    if acao['ultimo_div_val'] > 0:
                        st.write(f"⏮️ **Último dividendo pago:** {acao['ultimo_div_val']:.4f} {acao['moeda']}/ação ({acao['ultimo_div_data']})")
                        st.success(f"💵 **Estimado/Recebido:** {acao['total_dividendos']:.2f} {acao['moeda']}")
                    else:
                        st.write("⏮️ **Último dividendo pago:** Sem histórico recente.")

                    st.markdown("---")

        # Botão Limpar Carteira
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
