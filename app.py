import datetime
import json
import os
import pandas as pd
import plotly.express as px
import streamlit as st
import yfinance as yf

# Configuração da página
st.set_page_config(
    page_title="Meus Dividendos", 
    page_icon="💰", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS para estilo dos botões
st.markdown("""
<style>
    div.stButton > button[key="btn_add_action_popup"] {
        background-color: #2e7d32 !important;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
    }
    div.stButton > button[key="btn_add_action_popup"]:hover {
        background-color: #388e3c !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

FICHEIRO_DADOS = "dados_app.json"

# --- DICIONÁRIO DE TRADUÇÃO (PT / EN) ---
TEXTS = {
    "PT": {
        "title": "💰 Meus Dividendos",
        "select_option": "Escolhe uma opção:",
        "login_option": "Entrar (Login)",
        "register_option": "Criar Nova Conta",
        "login_header": "🔒 Entrar na Conta",
        "user": "Utilizador:",
        "password": "Palavra-passe:",
        "login_btn": "Entrar",
        "login_success": "Bem-vindo, {}!",
        "login_error": "Utilizador ou palavra-passe incorretos.",
        "register_header": "📝 Criar Nova Conta",
        "new_user": "Escolhe um Utilizador:",
        "new_pass": "Escolhe uma Palavra-passe:",
        "register_btn": "Criar Conta",
        "fill_all": "Preenche todos os campos!",
        "user_exists": "Este utilizador já existe!",
        "register_success": "Conta criada com sucesso! Mude para a opção 'Entrar (Login)'.",
        "menu": "📌 Menu",
        "logout": "🚪 Sair / Logout",
        "your_accounts": "🏦 As tuas Contas",
        "filter_portfolio": "🔍 Filtrar Carteira:",
        "all_accounts": "Todas as Contas",
        "manage_accounts": "⚙️ Criar / Apagar Conta",
        "new_account_label": "Nova Conta (ex: Trading212, DEGIRO):",
        "add": "➕ Adicionar",
        "account_added": "Conta '{}' adicionada!",
        "select_delete": "Selecione para apagar:",
        "select": "-- Selecionar --",
        "confirm_delete_q": "Tem a certeza que quer apagar a conta '{}'?",
        "confirm_delete_btn": "⚠️ Confirmar Apagar '{}'",
        "account_deleted": "Conta apagada!",
        "upcoming_divs": "📅 Próximos Dividendos",
        "no_upcoming": "Nenhuma das tuas ações anunciou o próximo dividendo ainda.",
        "add_stock": "➕ Adicionar Ação",
        "choose_account": "Escolha a Conta onde comprou:",
        "ticker_label": "Ticker (ex: PETR4, AAPL, EDP.LS):",
        "quantity_label": "Quantidade:",
        "price_label": "Preço de Compra por Ação (0 = usar preço atual):",
        "save_stock": "Guardar Ação",
        "stock_updated": "{} atualizado na conta {}!",
        "your_portfolio": "📊 A tua Carteira ({})",
        "no_stocks_account": "Nenhuma ação registada em '{}'.",
        "total": "Total Atual",
        "quantity": "Quantidade:",
        "shares": "ações",
        "price": "Preço Atual:",
        "avg_price": "Preço Médio Compra:",
        "total_invested": "Total Investido:",
        "profit_loss": "Lucro / Prejuízo:",
        "account": "Conta:",
        "next_div": "🔮 **Próximo Dividendo:** Ex-Dividendo em {} ➔ **Vais receber:** {:.2f} {}",
        "next_div_not_announced": "ℹ️ *Próximo dividendo ainda não foi anunciado.*",
        "last_div": "⏮️ **Último dividendo pago:** {:.4f} {}/ação ({})",
        "last_div_none": "⏮️ **Último dividendo pago:** Sem histórico recente.",
        "clear_portfolio": "🗑️ Limpar Toda a Carteira",
        "clear_confirm_q": "⚠️ **Tem a certeza absoluta de que quer APAGAR TODAS as ações da carteira?**",
        "yes_clear": "✔️ Sim, Apagar Tudo",
        "cancel": "❌ Cancelar",
        "portfolio_cleared": "Carteira limpa com sucesso!",
        "add_stock_info": "Adiciona uma ação ou importa um CSV para veres os teus dividendos.",
        "will_receive": "Vais receber",
        "confirm_delete_stock_q": "Apagar **{}** da conta **{}**?",
        "yes": "Sim",
        "no": "Não",
        "import_csv_title": "📥 Importar CSV",
        "upload_csv": "Carregar ficheiro CSV:",
        "import_btn": "Importar Ações",
        "csv_success": "Importadas/Atualizadas {} ações na conta '{}'!"
    },
    "EN": {
        "title": "💰 My Dividends",
        "select_option": "Choose an option:",
        "login_option": "Login",
        "register_option": "Create New Account",
        "login_header": "🔒 Login to Account",
        "user": "Username:",
        "password": "Password:",
        "login_btn": "Login",
        "login_success": "Welcome, {}!",
        "login_error": "Incorrect username or password.",
        "register_header": "📝 Create New Account",
        "new_user": "Choose a Username:",
        "new_pass": "Choose a Password:",
        "register_btn": "Create Account",
        "fill_all": "Please fill in all fields!",
        "user_exists": "This username already exists!",
        "register_success": "Account created successfully! Switch to 'Login'.",
        "menu": "📌 Menu",
        "logout": "🚪 Logout",
        "your_accounts": "🏦 Your Accounts",
        "filter_portfolio": "🔍 Filter Portfolio:",
        "all_accounts": "All Accounts",
        "manage_accounts": "⚙️ Create / Delete Account",
        "new_account_label": "New Account (e.g., Trading212, DEGIRO):",
        "add": "➕ Add",
        "account_added": "Account '{}' added!",
        "select_delete": "Select to delete:",
        "select": "-- Select --",
        "confirm_delete_q": "Are you sure you want to delete account '{}'?",
        "confirm_delete_btn": "⚠️ Confirm Delete '{}'",
        "account_deleted": "Account deleted!",
        "upcoming_divs": "📅 Upcoming Dividends",
        "no_upcoming": "None of your stocks have announced upcoming dividends yet.",
        "add_stock": "➕ Add Stock",
        "choose_account": "Choose the Account:",
        "ticker_label": "Ticker (e.g., PETR4, AAPL, EDP.LS):",
        "quantity_label": "Quantity:",
        "price_label": "Buy Price per Share (0 = use current price):",
        "save_stock": "Save Stock",
        "stock_updated": "{} updated in account {}!",
        "your_portfolio": "📊 Your Portfolio ({})",
        "no_stocks_account": "No stocks registered in '{}'.",
        "total": "Current Total",
        "quantity": "Quantity:",
        "shares": "shares",
        "price": "Current Price:",
        "avg_price": "Avg Buy Price:",
        "total_invested": "Total Invested:",
        "profit_loss": "Profit / Loss:",
        "account": "Account:",
        "next_div": "🔮 **Next Dividend:** Ex-Dividend on {} ➔ **You will receive:** {:.2f} {}",
        "next_div_not_announced": "ℹ️ *Next dividend not announced yet.*",
        "last_div": "⏮️ **Last dividend paid:** {:.4f} {}/share ({})",
        "last_div_none": "⏮️ **Last dividend paid:** No recent history.",
        "clear_portfolio": "🗑️ Clear Entire Portfolio",
        "clear_confirm_q": "⚠️ **Are you absolutely sure you want to DELETE ALL stocks in portfolio?**",
        "yes_clear": "✔️ Yes, Clear All",
        "cancel": "❌ Cancel",
        "portfolio_cleared": "Portfolio cleared successfully!",
        "add_stock_info": "Add a stock or import a CSV to see your dividends.",
        "will_receive": "Will receive",
        "confirm_delete_stock_q": "Delete **{}** from account **{}**?",
        "yes": "Yes",
        "no": "No",
        "import_csv_title": "📥 Import CSV",
        "upload_csv": "Upload CSV file:",
        "import_btn": "Import Stocks",
        "csv_success": "Imported/Updated {} stocks in account '{}'!"
    }
}

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
if "lang" not in st.session_state:
    st.session_state.lang = "PT"
if "stock_to_delete" not in st.session_state:
    st.session_state.stock_to_delete = None

# --- SELETOR DE LÍNGUA NA BARRA LATERAL ---
lang_choice = st.sidebar.selectbox("🌐 Idioma / Language", ["🇵🇹 Português", "🇬🇧 English"])
st.session_state.lang = "PT" if "Português" in lang_choice else "EN"
t = TEXTS[st.session_state.lang]

# --- ECRÃ DE LOGIN / REGISTO ---
if not st.session_state.autenticado:
    st.title(t["title"])
    
    opcao = st.radio(t["select_option"], [t["login_option"], t["register_option"]], horizontal=True)

    if opcao == t["login_option"]:
        with st.form("login_form"):
            st.subheader(t["login_header"])
            user_input = st.text_input(t["user"]).strip().lower()
            pass_input = st.text_input(t["password"], type="password").strip()
            btn_login = st.form_submit_button(t["login_btn"])

            if btn_login:
                if user_input in dados_globais["users"] and dados_globais["users"][user_input]["password"] == pass_input:
                    st.session_state.autenticado = True
                    st.session_state.user_atual = user_input
                    st.success(t["login_success"].format(user_input))
                    st.rerun()
                else:
                    st.error(t["login_error"])

    else:
        with st.form("registo_form"):
            st.subheader(t["register_header"])
            novo_user = st.text_input(t["new_user"]).strip().lower()
            nova_pass = st.text_input(t["new_pass"], type="password").strip()
            btn_registo = st.form_submit_button(t["register_btn"])

            if btn_registo:
                if not novo_user or not nova_pass:
                    st.warning(t["fill_all"])
                elif novo_user in dados_globais["users"]:
                    st.error(t["user_exists"])
                else:
                    dados_globais["users"][novo_user] = {
                        "password": nova_pass,
                        "contas": ["Geral", "Trading212", "DEGIRO"],
                        "carteira": []
                    }
                    guardar_dados(dados_globais)
                    st.success(t["register_success"])

# --- APLICAÇÃO PRINCIPAL ---
else:
    user = st.session_state.user_atual
    user_data = dados_globais["users"][user]

    # --- DIÁLOGO (POP-UP) PARA ADICIONAR AÇÃO ---
    @st.dialog(t["add_stock"])
    def modal_adicionar_acao():
        with st.form("add_stock_modal_form", clear_on_submit=True):
            conta_selecionada = st.selectbox(t["choose_account"], user_data["contas"])
            ticker_input = st.text_input(t["ticker_label"]).upper().strip()
            
            c_qtd, c_prc = st.columns(2)
            with c_qtd:
                qtd = st.number_input(t["quantity_label"], min_value=0.0001, step=0.1, value=1.0, format="%.4f")
            with c_prc:
                preco_compra = st.number_input(t["price_label"], min_value=0.0, step=0.5, value=0.0, format="%.2f")

            submitted = st.form_submit_button(t["save_stock"], use_container_width=True)

            if submitted and ticker_input:
                if len(ticker_input) >= 5 and ticker_input[-1].isdigit() and not ticker_input.endswith(".SA"):
                    ticker_final = f"{ticker_input}.SA"
                else:
                    ticker_final = ticker_input

                encontrado = False
                for item in user_data["carteira"]:
                    if item["ticker"] == ticker_final and item["conta"] == conta_selecionada:
                        qtd_antiga = item.get("quantidade", 0)
                        prc_antigo = item.get("preco_compra", 0)
                        
                        nova_qtd_total = qtd_antiga + float(qtd)
                        if prc_antigo > 0 or preco_compra > 0:
                            novo_prc_medio = ((qtd_antiga * prc_antigo) + (float(qtd) * preco_compra)) / nova_qtd_total
                        else:
                            novo_prc_medio = 0.0

                        item["quantidade"] = nova_qtd_total
                        item["preco_compra"] = novo_prc_medio
                        encontrado = True
                        break

                if not len(user_data["carteira"]) or not encontrado:
                    user_data["carteira"].append({
                        "conta": conta_selecionada,
                        "ticker": ticker_final,
                        "quantidade": float(qtd),
                        "preco_compra": float(preco_compra)
                    })

                guardar_dados(dados_globais)
                st.success(t["stock_updated"].format(ticker_final, conta_selecionada))
                st.rerun()

    # --- PROCESSAMENTO INICIAL DOS DADOS DA CARTEIRA ---
    hoje = datetime.date.today()
    carteira_completa = user_data["carteira"]
    
    dados_graficos_globais = []

    for item in carteira_completa:
        simbolo = item["ticker"]
        quantidade = item["quantidade"]
        conta = item["conta"]
        preco_compra = item.get("preco_compra", 0.0)

        try:
            stock = yf.Ticker(simbolo)
            info = stock.info
            nome = info.get("shortName", simbolo)
            moeda = info.get("currency", "USD")
            price = info.get("previousClose", 0) or info.get("currentPrice", 0)
            
            prc_medio_utilizado = preco_compra if preco_compra > 0 else price
            total_investido = prc_medio_utilizado * quantidade
            valor_total_atual = price * quantidade
            ganho_perda = valor_total_atual - total_investido

            div_history = stock.dividends
            ultimo_div_val = 0
            ultimo_div_data = None
            if not div_history.empty:
                ultimo_div_val = float(div_history.iloc[-1])
                ultimo_div_data = div_history.index[-1].strftime("%d/%m/%Y")

            calendar = stock.calendar
            proxima_data = None
            proximo_div_val = 0.0

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
                        proximo_div_val = ultimo_div_val

            income_proximo = proximo_div_val * quantidade if proxima_data else 0.0

            dado = {
                "ticker": simbolo,
                "nome": nome,
                "conta": conta,
                "quantidade": quantidade,
                "preco": price,
                "preco_compra": prc_medio_utilizado,
                "total_investido": total_investido,
                "valor_total": valor_total_atual,
                "ganho_perda": ganho_perda,
                "moeda": moeda,
                "proxima_data": proxima_data,
                "proximo_div_val": proximo_div_val,
                "income_proximo": income_proximo,
                "ultimo_div_val": ultimo_div_val,
                "ultimo_div_data": ultimo_div_data
            }
            dados_graficos_globais.append(dado)
        except Exception:
            pass

    # --- MENU LATERAL (ESQUERDA) ---
    st.sidebar.title(t["menu"])
    st.sidebar.write(f"{t['user'].replace(':', '')}: **{user}** 👋")
    
    if st.sidebar.button(t["logout"]):
        st.session_state.autenticado = False
        st.session_state.user_atual = None
        st.rerun()

    # --- OPÇÃO: IMPORTAR CSV GERAL ---
    with st.sidebar.expander(t["import_csv_title"]):
        conta_dest_csv = st.selectbox(t["choose_account"], user_data["contas"], key="csv_acc")
        uploaded_file = st.file_uploader(t["upload_csv"], type=["csv"])
        
        if uploaded_file is not None:
            if st.button(t["import_btn"]):
                try:
                    df_csv = pd.read_csv(uploaded_file)
                    
                    compras_vendas = {}
                    
                    col_ticker = next((c for c in df_csv.columns if "ticker" in c.lower() or "symbol" in c.lower() or "ação" in c.lower()), None)
                    col_shares = next((c for c in df_csv.columns if "shares" in c.lower() or "qty" in c.lower() or "qtd" in c.lower() or "quantidade" in c.lower()), None)
                    col_action = next((c for c in df_csv.columns if "action" in c.lower() or "tipo" in c.lower() or "operação" in c.lower()), None)
                    col_price = next((c for c in df_csv.columns if "price" in c.lower() or "preço" in c.lower() or "ppr" in c.lower()), None)

                    if col_ticker and col_shares:
                        for _, row in df_csv.iterrows():
                            tkr = str(row[col_ticker]).strip().upper()
                            try:
                                shs = float(row[col_shares])
                                prc = float(row[col_price]) if col_price else 0.0
                            except Exception:
                                continue

                            act = str(row[col_action]).strip().lower() if col_action else "buy"

                            if tkr not in compras_vendas:
                                compras_vendas[tkr] = {"qty": 0.0, "total_cost": 0.0}

                            if "sell" in act or "venda" in act:
                                compras_vendas[tkr]["qty"] -= shs
                            else:
                                compras_vendas[tkr]["qty"] += shs
                                compras_vendas[tkr]["total_cost"] += (shs * prc)

                        count_import = 0
                        for tkr, data in compras_vendas.items():
                            qty = data["qty"]
                            if qty > 0:
                                count_import += 1
                                if len(tkr) >= 5 and tkr[-1].isdigit() and not tkr.endswith(".SA"):
                                    tkr_final = f"{tkr}.SA"
                                else:
                                    tkr_final = tkr

                                prc_medio = data["total_cost"] / qty if data["total_cost"] > 0 else 0.0

                                encontrado = False
                                for item in user_data["carteira"]:
                                    if item["ticker"] == tkr_final and item["conta"] == conta_dest_csv:
                                        item["quantidade"] = qty
                                        item["preco_compra"] = prc_medio
                                        encontrado = True
                                        break
                                if not encontrado:
                                    user_data["carteira"].append({
                                        "conta": conta_dest_csv,
                                        "ticker": tkr_final,
                                        "quantidade": qty,
                                        "preco_compra": prc_medio
                                    })

                        guardar_dados(dados_globais)
                        st.success(t["csv_success"].format(count_import, conta_dest_csv))
                        st.rerun()
                    else:
                        st.error("Não foi possível identificar as colunas do CSV. Certifique-se que contém colunas como Ticker/Symbol e Quantidade/Shares.")
                except Exception as e:
                    st.error(f"Erro ao ler CSV: {e}")

    st.sidebar.markdown("---")
    
    # Gestão de Contas
    st.sidebar.subheader(t["your_accounts"])
    filtro_conta = st.sidebar.selectbox(t["filter_portfolio"], [t["all_accounts"]] + user_data["contas"])

    with st.sidebar.expander(t["manage_accounts"]):
        nova_conta = st.text_input(t["new_account_label"]).strip()
        if st.button(t["add"]):
            if nova_conta and nova_conta not in user_data["contas"]:
                user_data["contas"].append(nova_conta)
                guardar_dados(dados_globais)
                st.success(t["account_added"].format(nova_conta))
                st.rerun()

        st.markdown("---")
        conta_para_apagar = st.selectbox(t["select_delete"], [t["select"]] + user_data["contas"])
        if conta_para_apagar != t["select"]:
            st.warning(t["confirm_delete_q"].format(conta_para_apagar))
            if st.button(t["confirm_delete_btn"].format(conta_para_apagar)):
                user_data["contas"].remove(conta_para_apagar)
                user_data["carteira"] = [item for item in user_data["carteira"] if item["conta"] != conta_para_apagar]
                guardar_dados(dados_globais)
                st.success(t["account_deleted"])
                st.rerun()

    # MINI-GRÁFICO REDONDO (DONUT) DE PRÓXIMOS DIVIDENDOS NO MENU
    if dados_graficos_globais:
        st.sidebar.markdown("---")
        st.sidebar.subheader(t["upcoming_divs"])
        
        acoes_com_proximo = [item for item in dados_graficos_globais if item["proxima_data"] is not None and item["income_proximo"] > 0]
        
        if acoes_com_proximo:
            df_sidebar = pd.DataFrame(acoes_com_proximo)
            total_income = df_sidebar["income_proximo"].sum()
            moeda_sidebar = df_sidebar["moeda"].iloc[0] if not df_sidebar.empty else "USD"

            fig_sidebar = px.pie(
                df_sidebar,
                values="income_proximo",
                names="ticker",
                hole=0.6,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_sidebar.update_traces(
                textposition="inside",
                texttemplate="<b>%{label}</b><br>%{value:.2f}",
                hovertemplate="<b>%{label}</b><br>" + t["will_receive"] + ": %{value:.2f} " + moeda_sidebar + "<extra></extra>"
            )
            fig_sidebar.update_layout(
                height=230,
                annotations=[{
                    "text": f"<b>Total</b><br>{total_income:.2f} {moeda_sidebar}",
                    "x": 0.5, "y": 0.5, "font_size": 13, "showarrow": False
                }],
                showlegend=False,
                margin=dict(t=10, b=10, l=10, r=10)
            )
            st.sidebar.plotly_chart(fig_sidebar, use_container_width=True)
            
            for a in acoes_com_proximo:
                st.sidebar.caption(f"🗓️ **{a['ticker']}**: {a['proxima_data'].strftime('%d/%m/%Y')} ➔ **{a['income_proximo']:.2f} {a['moeda']}**")
        else:
            st.sidebar.info(t["no_upcoming"])

    # --- CONTEÚDO PRINCIPAL ---
    st.title(t["title"])

    # SECÇÃO: Exibição da Carteira
    if dados_graficos_globais:
        st.subheader(t["your_portfolio"].format(filtro_conta))

        if filtro_conta == t["all_accounts"]:
            dados_filtrados = dados_graficos_globais
        else:
            dados_filtrados = [item for item in dados_graficos_globais if item["conta"] == filtro_conta]

        if not dados_filtrados:
            st.info(t["no_stocks_account"].format(filtro_conta))
            if st.button(t["add_stock"], key="btn_add_action_popup"):
                modal_adicionar_acao()
        else:
            col_grafico, col_lista = st.columns([0.8, 1.2])

            with col_grafico:
                df_grafico = pd.DataFrame(dados_filtrados)
                total_patrimonio = df_grafico["valor_total"].sum()
                total_investido_geral = df_grafico["total_investido"].sum()
                moeda_pred = df_grafico["moeda"].iloc[0] if not df_grafico.empty else "USD"

                fig = px.pie(
                    df_grafico,
                    values="valor_total",
                    names="ticker",
                    hole=0.6,
                    color_discrete_sequence=px.colors.qualitative.Bold
                )
                
                fig.update_traces(
                    textposition="inside",
                    texttemplate="<b>%{label}</b><br>%{value:.2f}",
                    hovertemplate="<b>%{label}</b><br>Valor: %{value:.2f} " + moeda_pred + "<extra></extra>"
                )
                
                fig.update_layout(
                    height=280,
                    annotations=[{
                        "text": f"<b>{t['total']}</b><br>{total_patrimonio:.2f} {moeda_pred}",
                        "x": 0.5, "y": 0.5, "font_size": 15, "showarrow": False
                    }],
                    showlegend=False,
                    margin=dict(t=10, b=10, l=10, r=10)
                )
                st.plotly_chart(fig, use_container_width=True)

                st.caption(f"💵 **{t['total_invested']}** {total_investido_geral:.2f} {moeda_pred}")

                if st.button(t["add_stock"], key="btn_add_action_popup", use_container_width=True):
                    modal_adicionar_acao()

            with col_lista:
                for idx, acao in enumerate(dados_filtrados):
                    col_titulo, col_btn_del = st.columns([12, 1])
                    
                    with col_titulo:
                        st.markdown(f"### {acao['nome']} (`{acao['ticker']}`)")
                    
                    with col_btn_del:
                        if st.button("❌", key=f"btn_x_{acao['ticker']}_{acao['conta']}_{idx}"):
                            st.session_state.stock_to_delete = f"{acao['ticker']}_{acao['conta']}"
                            st.rerun()

                    if st.session_state.stock_to_delete == f"{acao['ticker']}_{acao['conta']}":
                        st.warning(t["confirm_delete_stock_q"].format(acao['ticker'], acao['conta']))
                        c_sim, c_nao = st.columns(2)
                        with c_sim:
                            if st.button(t["yes"], key=f"yes_del_{acao['ticker']}_{acao['conta']}_{idx}"):
                                user_data["carteira"] = [
                                    item for item in user_data["carteira"]
                                    if not (item["ticker"] == acao["ticker"] and item["conta"] == acao["conta"])
                                ]
                                guardar_dados(dados_globais)
                                st.session_state.stock_to_delete = None
                                st.rerun()
                        with c_nao:
                            if st.button(t["no"], key=f"no_del_{acao['ticker']}_{acao['conta']}_{idx}"):
                                st.session_state.stock_to_delete = None
                                st.rerun()

                    st.caption(f"🏦 **{t['account']}** {acao['conta']}")
                    st.write(f"**{t['quantity']}** {acao['quantidade']:.4f} {t['shares']} | **{t['price']}** {acao['preco']:.2f} {acao['moeda']}")
                    
                    if acao['preco_compra'] > 0:
                        cor_lucro = "green" if acao['ganho_perda'] >= 0 else "red"
                        # Linha com a correção da chave acao['total_investido']
                        st.write(f"**{t['avg_price']}** {acao['preco_compra']:.2f} {acao['moeda']} | **{t['total_invested']}** {acao['total_investido']:.2f} {acao['moeda']}")
                        st.markdown(f"**{t['profit_loss']}** <span style='color:{cor_lucro}; font-weight:bold;'>{acao['ganho_perda']:+.2f} {acao['moeda']}</span>", unsafe_allow_html=True)

                    if acao['proxima_data']:
                        total_a_receber = acao['income_proximo']
                        st.info(t["next_div"].format(acao['proxima_data'].strftime('%d/%m/%Y'), total_a_receber, acao['moeda']))
                    else:
                        st.caption(t["next_div_not_announced"])

                    if acao['ultimo_div_val'] > 0:
                        st.write(t["last_div"].format(acao['ultimo_div_val'], acao['moeda'], acao['ultimo_div_data']))
                    else:
                        st.write(t["last_div_none"])

                    st.markdown("---")

        st.markdown("<br>", unsafe_allow_html=True)
        # Botão Limpar Carteira Toda
        if not st.session_state.confirmar_limpar_tudo:
            if st.button(t["clear_portfolio"]):
                st.session_state.confirmar_limpar_tudo = True
                st.rerun()
        else:
            st.warning(t["clear_confirm_q"])
            col_sim, col_nao = st.columns(2)
            with col_sim:
                if st.button(t["yes_clear"]):
                    user_data["carteira"] = []
                    guardar_dados(dados_globais)
                    st.session_state.confirmar_limpar_tudo = False
                    st.rerun()
            with col_nao:
                if st.button(t["cancel"]):
                    st.session_state.confirmar_limpar_tudo = False
                    st.rerun()
    else:
        st.info(t["add_stock_info"])
        if st.button(t["add_stock"], key="btn_add_action_popup"):
            modal_adicionar_acao()
