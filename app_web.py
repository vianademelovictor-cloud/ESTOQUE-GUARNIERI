# --- IMPORTAÇÃO DE BIBLIOTECAS ---
import io
import math
import time
import urllib.parse
import json 
from datetime import datetime
from fpdf import FPDF
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import requests
import libsql

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Guarnieri Materiais de Construção",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- 2. SISTEMA DE DESIGN ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
    .block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; }
    .stApp { background-color: #0a1120; color: #f8fafc; }
    section[data-testid="stSidebar"] { background-color: #060d19 !important; border-right: 2px solid #1e293b !important; }
    h1, h2, h3 { color: #f8fafc !important; font-weight: 800 !important; }
    label, p, span { color: #e2e8f0 !important; font-weight: 600; }
    div[data-testid="stSidebar"] label { font-size: 1.05rem !important; color: #f8fafc !important; padding: 6px 10px !important; border-radius: 8px !important; transition: all 0.2s ease !important; }
    div[data-testid="stSidebar"] label:hover { background: #1e293b !important; color: #ffffff !important; }
    input, div[data-baseweb="select"] > div, textarea { background-color: #0f172a !important; color: #ffffff !important; border: 1px solid #334155 !important; border-radius: 8px !important; }
    div[data-testid="stForm"], div[data-testid="stBlock"] > div[style*="border"] { background-color: #111c2e !important; border: 1px solid #1e293b !important; border-radius: 12px !important; padding: 20px !important; }
    div.stButton > button, div[data-testid="stFormSubmitButton"] > button { background-color: #000000 !important; color: #ffffff !important; font-weight: 800 !important; font-size: 1rem !important; border: 2px solid #ffffff !important; border-radius: 8px !important; padding: 10px 20px !important; transition: all 0.2s ease-in-out !important; width: 100%; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.4) !important; }
    div.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover { background-color: #1a1a1a !important; color: #ffffff !important; border-color: #ffffff !important; transform: translateY(-2px) !important; box-shadow: 0 4px 12px rgba(255, 255, 255, 0.2) !important; }
    div.stButton > button *, div[data-testid="stFormSubmitButton"] > button * { color: #ffffff !important; }
    [data-testid="stMetricValue"] { color: #38bdf8 !important; font-weight: 800 !important; font-size: 2rem !important; }
    .stDataFrame { border: 1px solid #1e293b !important; border-radius: 10px !important; }
    .top-header { text-align: center; padding: 10px 0 20px 0; display: flex; flex-direction: column; align-items: center; justify-content: center; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CAMADA DE DADOS (TURSO) ---
def conectar():
    url = st.secrets["TURSO_DATABASE_URL"]
    token = st.secrets["TURSO_AUTH_TOKEN"]
    return libsql.connect(url, auth_token=token)

def carregar_dataframe(query, conn, params=None):
    cursor = conn.cursor()
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)
    
    if cursor.description:
        cols = [desc[0] for desc in cursor.description]
        return pd.DataFrame(cursor.fetchall(), columns=cols)
    return pd.DataFrame()

def inicializar_banco():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS produtos 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, codigo TEXT UNIQUE, nome TEXT, 
         m2_por_caixa REAL, preco_m2 REAL, m2_total REAL)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS clientes 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, cpf TEXT UNIQUE, 
         telefone TEXT, endereco TEXT, bairro TEXT, cep TEXT)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS vendas_cabecalho 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, data_venda TEXT, cliente_id INTEGER, 
         total_pago REAL, forma_pagamento TEXT)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS vendas_itens 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, venda_id INTEGER, produto TEXT, 
         qtd REAL, unitario REAL, subtotal REAL, caixas INTEGER)""")
    
    cursor.execute("PRAGMA table_info(vendas_itens)")
    colunas_itens = [info[1] for info in cursor.fetchall()]
    if "caixas" not in colunas_itens:
        cursor.execute("ALTER TABLE vendas_itens ADD COLUMN caixas INTEGER DEFAULT 0")
        
    cursor.execute("PRAGMA table_info(vendas_cabecalho)")
    colunas_vendas = [info[1] for info in cursor.fetchall()]
    if "forma_pagamento" not in colunas_vendas:
        cursor.execute("ALTER TABLE vendas_cabecalho ADD COLUMN forma_pagamento TEXT DEFAULT 'Não Informado'")
    if "status_entrega" not in colunas_vendas:
        cursor.execute("ALTER TABLE vendas_cabecalho ADD COLUMN status_entrega TEXT DEFAULT 'Pendente'")
        
    conn.commit()
    conn.close()

inicializar_banco()

# --- 4. FUNÇÃO REUTILIZÁVEL DE RECIBO (MODAL / PDF / WHATSAPP) ---
def renderizar_acoes_recibo(cliente_info, itens_carrinho, total_geral, pedido_id, forma_paga, data_venda_str):
    with st.expander(f"📄 Opções do Recibo / Comprovante (Pedido #{pedido_id:04d})", expanded=False):
        st.write(f"**Data da Venda:** {data_venda_str}")
        st.write(f"**Forma de Pagamento:** {forma_paga}")
        
        df_recibo = pd.DataFrame(itens_carrinho)
        if "prod" in df_recibo.columns:
            df_recibo = df_recibo.rename(columns={"prod": "DISCRIMINAÇÃO", "caixas": "QTD CAIXAS", "qtd": "TOTAL m²", "unit": "UNITÁRIO", "total": "TOTAL R$"})
        st.table(df_recibo[["DISCRIMINAÇÃO", "QTD CAIXAS", "TOTAL m²", "TOTAL R$"]])
        st.markdown(f"<h3 style='text-align: right; color: #ffffff;'>TOTAL R$ {total_geral:,.2f}</h3>", unsafe_allow_html=True)

        # Montagem do HTML para Impressão
        linhas_tabela = ""
        for _, item in df_recibo.iterrows():
            linhas_tabela += f"<tr><td style='padding: 10px; border-bottom: 1px solid #ddd;'>{item['DISCRIMINAÇÃO']}</td><td style='text-align: center; padding: 10px; border-bottom: 1px solid #ddd;'>{item['QTD CAIXAS']}</td><td style='text-align: center; padding: 10px; border-bottom: 1px solid #ddd;'>{item['TOTAL m²']:.2f}</td><td style='text-align: right; padding: 10px; border-bottom: 1px solid #ddd;'>R$ {item['TOTAL R$']:,.2f}</td></tr>"

        html_recibo = f"""
        <html><head><title>Recibo - Pedido {pedido_id:04d}</title><style>body {{ font-family: Arial, sans-serif; padding: 20px; color: #000; max-width: 800px; margin: auto; }} .header {{ text-align: center; color: #1e5d2d; margin-bottom: 0; font-size: 24px; }} .sub {{ text-align: center; font-size: 12px; margin-top: 5px; }} .info {{ margin: 25px 0; font-size: 14px; line-height: 1.6; }} table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }} th, td {{ border: 1px solid #ccc; padding: 10px; font-size: 14px; }} th {{ background-color: #f2f2f6; text-align: left; }} .total {{ text-align: right; font-size: 18px; font-weight: bold; margin-top: 20px; }} .pago {{ text-align: center; border: 3px solid black; padding: 12px; font-weight: bold; font-size: 22px; margin-top: 30px; background-color: #f0f2f6; }}</style></head><body><h2 class="header">GUARNIERI MATERIAIS DE CONSTRUÇÃO</h2><div class="sub"><b>Fone: (19) 9 9473-6066</b><br>Rua Ana Herminia Trento Roque, 902 - Limeira - SP</div><hr style="margin: 20px 0;"><div class="info"><p><b>Data:</b> {data_venda_str} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>PEDIDO Nº:</b> {pedido_id:04d}</p><p><b>Cliente:</b> {cliente_info['nome']}<br><b>Endereço:</b> {cliente_info['endereco']}, {cliente_info['bairro']}<br><b>Pagamento:</b> {forma_paga}</p></div><hr style="margin: 20px 0;"><table><thead><tr><th>DISCRIMINAÇÃO</th><th style='text-align: center;'>QTD CAIXAS</th><th style='text-align: center;'>TOTAL m²</th><th style='text-align: right;'>TOTAL R$</th></tr></thead><tbody>{linhas_tabela}</tbody></table><div class="total">VALOR TOTAL: R$ {total_geral:,.2f}</div><div class="pago">PAGO VIA {forma_paga.upper()}</div></body></html>
        """
        
        conteudo_safe = json.dumps(html_recibo)
        html_js = f"<div><button onclick=\"imprimirRecibo()\" style=\"width: 100%; background-color: #000000; color: white; padding: 10px; border: 2px solid white; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 15px; font-family: sans-serif; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.4);\">🖨️ Imprimir / Salvar Recibo</button></div><script>function imprimirRecibo() {{ const janela = window.open('', '', 'width=800,height=600'); janela.document.write({conteudo_safe}); janela.document.close(); janela.focus(); setTimeout(() => {{ janela.print(); janela.close(); }}, 500); }}</script>"
        components.html(html_js, height=60)

        # Gerador de PDF
        def limpar_texto(texto):
            return str(texto).encode('latin-1', 'ignore').decode('latin-1')

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(190, 10, "GUARNIERI MATERIAIS DE CONSTRUCAO", ln=True, align="C")
        pdf.set_font("Arial", "", 10)
        pdf.cell(190, 7, "Rua Ana Herminia Trento Roque, 902 - Limeira - SP", ln=True, align="C")
        pdf.cell(190, 7, "Fone: (19) 9 9473-6066", ln=True, align="C")
        pdf.ln(10)
        
        pdf.set_font("Arial", "B", 12)
        pdf.cell(190, 10, f"PEDIDO DE VENDA: {pedido_id:04d}", ln=True)
        pdf.set_font("Arial", "", 11)
        pdf.cell(190, 7, f"Data: {data_venda_str}", ln=True)
        pdf.cell(190, 7, limpar_texto(f"Cliente: {cliente_info['nome']}"), ln=True)
        pdf.cell(190, 7, limpar_texto(f"Endereco: {cliente_info['endereco']}, {cliente_info['bairro']}"), ln=True)
        pdf.cell(190, 7, limpar_texto(f"Forma de Pagamento: {forma_paga}"), ln=True)
        pdf.ln(5)
        
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(80, 8, "PRODUTO", 1, 0, "C", True)
        pdf.cell(30, 8, "CAIXAS", 1, 0, "C", True)
        pdf.cell(40, 8, "TOTAL m2", 1, 0, "C", True)
        pdf.cell(40, 8, "TOTAL R$", 1, 1, "C", True)
        
        pdf.set_font("Arial", "", 10)
        for _, item in df_recibo.iterrows():
            pdf.cell(80, 8, limpar_texto(item["DISCRIMINAÇÃO"]), 1)
            pdf.cell(30, 8, str(item["QTD CAIXAS"]), 1, 0, "C")
            pdf.cell(40, 8, f"{item['TOTAL m²']:.2f}", 1, 0, "C")
            pdf.cell(40, 8, f"R$ {item['TOTAL R$']:,.2f}", 1, 1, "R")
            
        pdf.ln(5)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(190, 10, f"VALOR TOTAL: R$ {total_geral:,.2f}", ln=True, align="R")
        
        pdf_output = pdf.output(dest="S").encode("latin-1", errors="replace")
        st.download_button(label="📥 Baixar Recibo em PDF", data=pdf_output, file_name=f"Recibo_Guarnieri_{pedido_id}.pdf", mime="application/pdf", key=f"dl_pdf_{pedido_id}", use_container_width=True)

        # Link WhatsApp
        msg_recibo = f"*📄 RECIBO DE PEDIDO - GUARNIERI MATERIAIS DE CONSTRUÇÃO*\n-------------------------------------------\n*PEDIDO Nº:* {pedido_id:04d}\n*DATA:* {data_venda_str}\n-------------------------------------------\n*CLIENTE:* {cliente_info['nome']}\n*PAGAMENTO:* {forma_paga}\n-------------------------------------------\n"
        for _, item in df_recibo.iterrows():
            msg_recibo += f"• {item['DISCRIMINAÇÃO']}: {item['QTD CAIXAS']} cx ({item['TOTAL m²']}m²)\n"
        msg_recibo += f"-------------------------------------------\n*VALOR TOTAL: R$ {total_geral:,.2f}*\n-------------------------------------------\nAgradecemos a preferência! 🏗️"
        
        msg_url = urllib.parse.quote(msg_recibo)
        link_wa = f"https://wa.me/55{cliente_info['telefone']}?text={msg_url}"
        st.link_button("📲 Enviar Recibo via WhatsApp", link_wa, use_container_width=True)

# --- 5. NAVEGAÇÃO LATERAL ---
st.sidebar.markdown("<h2 style='color:#ffffff; font-weight:800; font-size:1.3rem; margin-bottom:10px;'>SERVIÇOS GUARNIERI</h2>", unsafe_allow_html=True)
menu = st.sidebar.radio("Navegue pelas Opções:", ["⚖️ Início", "🚨 Alerta de Estoque Baixo", "🛒 Realizar Venda", "📋 Estoque", "👤 Cadastro de Cliente", "🔍 Buscar Cliente", "📈 Histórico de Vendas", "🏆 Ranking de Clientes", "📦 Gestão de Produtos"])

# --- 6. LÓGICA DAS TELAS ---
if menu == "⚖️ Início":
    st.markdown("""<div class="top-header"><div style="font-size: 80px; line-height: 1; margin-bottom: 12px;">⚖️</div><h1 style="margin: 0; font-size: 1.8rem; letter-spacing: 1px;">GUARNIERI MATERIAIS DE CONSTRUÇÃO</h1><p style="color: #94a3b8; font-size: 1rem; margin-top: 4px; margin-bottom: 12px;">Sistema Oficial de Gestão, Vendas e Estoque</p></div>""", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("""<div style="text-align: center; padding: 10px;"><h3 style="margin-bottom: 8px;">Bem-vindo ao Painel de Controle</h3><p style="color: #94a3b8; font-size: 1.05rem; margin: 0;">Utilize o menu lateral à esquerda <b>SERVIÇOS GUARNIERI</b> para acessar os módulos de vendas, reposição de estoque, controle de estoque e consulta de clientes.</p></div>""", unsafe_allow_html=True)

elif menu == "🚨 Alerta de Estoque Baixo":
    st.header("🚨 Alerta de Reposição de Estoque")
    conn = conectar()
    df_raw = carregar_dataframe("SELECT * FROM produtos", conn)
    conn.close()
    if not df_raw.empty:
        df_raw["Caixas Fechadas"] = df_raw.apply(lambda r: math.floor(r["m2_total"] / r["m2_por_caixa"]) if r["m2_por_caixa"] > 0 else 0, axis=1)
        df_critico = df_raw[df_raw["Caixas Fechadas"] < 10].copy()
        if not df_critico.empty:
            df_critico["Sugestão de Reposição (Cx)"] = 10 - df_critico["Caixas Fechadas"]
            df_critico_exib = df_critico.rename(columns={"codigo": "Cód", "nome": "Produto", "Caixas Fechadas": "Caixas Atuais", "m2_por_caixa": "Rendimento (m²/Cx)", "m2_total": "Saldo Atual (m²)"})
            k1, k2 = st.columns(2)
            k1.metric("Produtos em Situação Crítica", f"{len(df_critico)} item(ns)")
            k2.metric("Total de Caixas a Repor (Mínimo)", f"{df_critico['Sugestão de Reposição (Cx)'].sum():,} cx")
            st.warning("⚠️ **Atenção:** Os produtos listados abaixo estão com **menos de 10 caixas/unidades** em estoque.")
            colunas = ["Cód", "Produto", "Caixas Atuais", "Sugestão de Reposição (Cx)", "Rendimento (m²/Cx)", "Saldo Atual (m²)"]
            st.dataframe(df_critico_exib[colunas], use_container_width=True, hide_index=True)
        else:
            st.success("✅ **Estoque Seguro!** Todos os seus produtos possuem 10 ou mais caixas/unidades em estoque.")
    else:
        st.info("Nenhum produto cadastrado no sistema.")

elif menu == "🛒 Realizar Venda":
    st.header("🛒 Novo Pedido de Venda")
    
    with st.container(border=True):
        st.subheader("1. Seleção de Cliente e Pagamento")
        col_c1, col_c2 = st.columns([2, 1])
        with col_c1:
            busca_cli = st.text_input("🔍 Pesquisar Cliente (Nome, CPF ou Telefone):", help="Digite para filtrar instantaneamente. Deixe em branco para listar todos.")
        with col_c2:
            forma_pago = st.selectbox("Forma de Pagamento", ["Pix", "Dinheiro", "Cartão de Crédito", "Cartão de Débito"])
            
        conn = conectar()
        if busca_cli:
            query = "SELECT * FROM clientes WHERE nome LIKE ? OR cpf LIKE ? OR telefone LIKE ?"
            param = f"%{busca_cli}%"
            clientes_df = carregar_dataframe(query, conn, (param, param, param))
        else:
            clientes_df = carregar_dataframe("SELECT * FROM clientes", conn)
        conn.close()
        
        if clientes_df.empty:
            st.warning("⚠️ Nenhum cliente encontrado com a sua busca.")
            cli_nome = None
        else:
            lista_nomes_clientes = sorted(clientes_df["nome"].tolist())
            cli_nome = st.selectbox("Selecione o Cliente:", options=[""] + lista_nomes_clientes, index=0)
            
        if cli_nome:
            cli_dados = clientes_df[clientes_df["nome"] == cli_nome].iloc[0]
            
            if "carrinho" not in st.session_state:
                st.session_state.carrinho = []
                
            with st.container(border=True):
                st.subheader("2. Adicionar Produtos")
                
                busca_prod = st.text_input("🔍 Buscar Produto no Estoque (Nome ou Código):")
                
                conn = conectar()
                if busca_prod:
                    query_p = "SELECT codigo, nome FROM produtos WHERE nome LIKE ? OR codigo LIKE ? ORDER BY nome"
                    param_p = f"%{busca_prod}%"
                    prods_df = carregar_dataframe(query_p, conn, (param_p, param_p))
                else:
                    prods_df = carregar_dataframe("SELECT codigo, nome FROM produtos ORDER BY nome", conn)
                conn.close()
                
                if prods_df.empty:
                    st.warning("⚠️ Nenhum produto encontrado.")
                else:
                    lista_produtos = [""] + [f"{r['codigo']} - {r['nome']}" for _, r in prods_df.iterrows()]
                    prod_selecionado = st.selectbox("Selecione o Produto:", options=lista_produtos, index=0)
                    
                    if prod_selecionado:
                        cod = prod_selecionado.split(" - ")[0]
                        conn = conectar()
                        p = conn.execute("SELECT nome, m2_por_caixa, preco_m2, m2_total FROM produtos WHERE codigo = ?", (cod,)).fetchone()
                        conn.close()
                        
                        if p:
                            preco_caixa = p[1] * p[2]
                            st.info(f"📦 **{p[0]}** | Estoque Atual: **{p[3]} m²** | Rendimento: **{p[1]} m²/cx** | **Preço Unitário: R$ {preco_caixa:,.2f}**")
                            m2_desejado = st.number_input("Quantos m² (ou unidades) o cliente precisa?", min_value=0.0, step=0.1)
                            
                            if m2_desejado > 0:
                                qtd_caixas = math.ceil(m2_desejado / p[1]) if p[1] > 0 else 1
                                m2_final = round(qtd_caixas * p[1], 2) if p[1] > 0 else m2_desejado
                                v_total = round(m2_final * p[2], 2)
                                st.warning(f"💡 Venda calculada: **{qtd_caixas} caixas/unid.** ({m2_final} m²) = **R$ {v_total:,.2f}**")
                                
                                if st.button("➕ Adicionar ao Carrinho"):
                                    st.session_state.carrinho.append({"prod": p[0], "cod": cod, "caixas": qtd_caixas, "qtd": m2_final, "unit": p[2], "total": v_total})
                                    st.success("Adicionado!")
                                    time.sleep(0.5)
                                    st.rerun()
                                    
            if st.session_state.carrinho:
                with st.container(border=True):
                    st.subheader("3. Itens no Pedido")
                    df_c = pd.DataFrame(st.session_state.carrinho)
                    st.table(df_c[["prod", "caixas", "qtd", "total"]])
                    
                    subtotal_pedido = df_c["total"].sum()
                    desconto_valor = st.number_input("💸 Aplicar Desconto (R$):", min_value=0.0, max_value=float(subtotal_pedido), step=1.0, value=0.0)
                    total_final = subtotal_pedido - desconto_valor
                    
                    c_tot1, c_tot2 = st.columns(2)
                    c_tot1.write(f"**Subtotal dos Produtos:** R$ {subtotal_pedido:,.2f}")
                    if desconto_valor > 0:
                        c_tot1.write(f"**Desconto Aplicado:** - R$ {desconto_valor:,.2f}")
                    st.markdown(f"<h2 style='text-align: right; color: #ffffff;'>Total a Pagar: R$ {total_final:,.2f}</h2>", unsafe_allow_html=True)
                    
                    if st.button("✅ Finalizar Venda e Salvar na Nuvem"):
                        conn = conectar()
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO vendas_cabecalho (data_venda, cliente_id, total_pago, forma_pagamento, status_entrega) VALUES (?,?,?,?,?)", (datetime.now().strftime("%d/%m/%Y"), int(cli_dados["id"]), total_final, forma_pago, "Pendente"))
                        v_id = cursor.lastrowid
                        
                        for item in st.session_state.carrinho:
                            cursor.execute("INSERT INTO vendas_itens (venda_id, produto, qtd, unitario, subtotal, caixas) VALUES (?,?,?,?,?,?)", (v_id, item["prod"], item["qtd"], item["unit"], item["total"], item["caixas"]))
                            cursor.execute("UPDATE produtos SET m2_total = m2_total - ? WHERE codigo = ?", (item["qtd"], item["cod"]))
                            
                        conn.commit()
                        conn.close()
                        
                        st.success(f"Pedido #{v_id:04d} finalizado com sucesso!")
                        renderizar_acoes_recibo(cli_dados, st.session_state.carrinho, total_final, v_id, forma_pago, datetime.now().strftime('%d/%m/%Y'))
                        st.session_state.carrinho = []

elif menu == "📋 Estoque":
    st.header("📋 Controle de Estoque")
    conn = conectar()
    df_raw = carregar_dataframe("SELECT * FROM produtos", conn)
    conn.close()
    if not df_raw.empty:
        df_raw["Caixas Fechadas"] = df_raw.apply(lambda r: math.floor(r["m2_total"] / r["m2_por_caixa"]) if r["m2_por_caixa"] > 0 else 0, axis=1)
        df_raw["Preço por Caixa (R$)"] = df_raw["m2_por_caixa"] * df_raw["preco_m2"]
        df_est = df_raw.rename(columns={"codigo": "Cód", "nome": "Produto", "m2_por_caixa": "Rendimento (m²/Caixa)", "preco_m2": "Preço/m² (R$)", "m2_total": "Saldo Total (m²)"})
        k1, k2, k3 = st.columns(3)
        k1.metric("Itens Cadastrados", len(df_est))
        k2.metric("Total de Caixas/Unidades", f"{df_est['Caixas Fechadas'].sum():,} cx")
        k3.metric("Total em Estoque (m²)", f"{df_est['Saldo Total (m²)'].sum():,.2f} m²")
        st.divider()
        colunas_ordem = ["Cód", "Produto", "Caixas Fechadas", "Preço por Caixa (R$)", "Rendimento (m²/Caixa)", "Preço/m² (R$)", "Saldo Total (m²)"]
        df_exibicao = df_est[colunas_ordem].copy()
        df_exibicao["Preço por Caixa (R$)"] = df_exibicao["Preço por Caixa (R$)"].map("R$ {:,.2f}".format)
        df_exibicao["Preço/m² (R$)"] = df_exibicao["Preço/m² (R$)"].map("R$ {:,.2f}".format)
        st.dataframe(df_exibicao, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum produto cadastrado no estoque.")

elif menu == "👤 Cadastro de Cliente":
    st.header("👤 Cadastro de Novos Clientes")
    if 'endereco_api' not in st.session_state:
        st.session_state.endereco_api = {"logradouro": "", "bairro": "", "localidade": "", "uf": ""}
    
    st.write("**1. Buscar Endereço (API ViaCEP)**")
    col_cep1, col_cep2 = st.columns([1, 2])
    with col_cep1:
        cep_busca = st.text_input("Digite o CEP (Somente números)")
    with col_cep2:
        st.write("") 
        st.write("")
        if st.button("🔎 Preencher Endereço Automaticamente"):
            if cep_busca and len(cep_busca) == 8:
                try:
                    resposta = requests.get(f"https://viacep.com.br/ws/{cep_busca}/json/")
                    dados = resposta.json()
                    if "erro" not in dados:
                        st.session_state.endereco_api = dados
                        st.success(f"📍 Endereço encontrado: {dados['logradouro']}, {dados['bairro']} - {dados['localidade']}/{dados['uf']}")
                    else:
                        st.error("CEP não encontrado.")
                except:
                    st.error("Erro ao conectar com a API do ViaCEP.")
            else:
                st.warning("Por favor, digite um CEP válido de 8 números.")

    st.write("---")
    st.write("**2. Dados do Cliente**")

    with st.form("cadastro_cli"):
        col1, col2 = st.columns(2)
        with col1:
            n = st.text_input("Nome Completo")
            c = st.text_input("CPF (Somente números)")
            t = st.text_input("Telefone (com DDD)")
        with col2:
            e = st.text_input("Endereço (Rua, Nº)", value=st.session_state.endereco_api.get('logradouro', ''))
            b = st.text_input("Bairro", value=st.session_state.endereco_api.get('bairro', ''))
            cp = st.text_input("CEP", value=cep_busca if cep_busca else '')
            
        if st.form_submit_button("💾 Salvar Cliente"):
            if n and c:
                conn = conectar()
                try:
                    conn.execute("INSERT INTO clientes (nome, cpf, telefone, endereco, bairro, cep) VALUES (?,?,?,?,?,?)", (n, c, t, e, b, cp))
                    conn.commit()
                    st.success("✅ Cliente cadastrado com sucesso na nuvem!")
                    st.session_state.endereco_api = {"logradouro": "", "bairro": "", "localidade": "", "uf": ""}
                except Exception:
                    st.error("❌ Erro: Este CPF já está cadastrado ou houve falha na rede.")
                finally:
                    conn.close()
            else:
                st.warning("⚠️ Nome e CPF são campos obrigatórios.")

elif menu == "🔍 Buscar Cliente":
    st.header("🔍 Consultar Ficha, Comprovantes e Entregas")
    conn = conectar()
    all_cli = carregar_dataframe("SELECT * FROM clientes", conn)
    
    if all_cli.empty:
        st.info("Nenhum cliente cadastrado no momento.")
        conn.close()
    else:
        with st.container(border=True):
            st.subheader("🔎 Buscar Ficha de Cliente")
            lista_nomes = sorted(all_cli["nome"].tolist())
            nome_selecionado = st.selectbox("Digite ou selecione o Nome do Cliente:", options=[""] + lista_nomes, index=0)
            
            if nome_selecionado:
                cli = all_cli[all_cli["nome"] == nome_selecionado].iloc[0]
                st.markdown(f"### 📋 Ficha de: **{cli['nome']}**")
                c1, c2, c3 = st.columns(3)
                c1.write(f"**CPF:** {cli['cpf']}")
                c2.write(f"**Telefone:** {cli['telefone']}")
                c3.write(f"**CEP:** {cli['cep']}")
                st.write(f"**Endereço para Entrega:** {cli['endereco']} - **Bairro:** {cli['bairro']}")
                
                # --- SESSÃO DE ENTREGAS E RECIBOS ---
                st.divider()
                st.subheader("📦 Controle de Pedidos, Entregas e Comprovantes")
                pedidos_cli = carregar_dataframe(f"SELECT * FROM vendas_cabecalho WHERE cliente_id = {cli['id']} ORDER BY id DESC", conn)
                
                if pedidos_cli.empty:
                    st.info("Nenhum pedido registrado para este cliente.")
                else:
                    tab_pend, tab_hist = st.tabs(["🚚 Entregas Pendentes", "✅ Histórico de Compras"])
                    
                    with tab_pend:
                        pendentes = pedidos_cli[pedidos_cli['status_entrega'] == 'Pendente']
                        if pendentes.empty:
                            st.success("✅ Tudo certo! Nenhuma entrega pendente para este cliente.")
                        else:
                            for _, ped in pendentes.iterrows():
                                with st.expander(f"🔴 Pedido Nº {ped['id']:04d} - Data: {ped['data_venda']} - R$ {ped['total_pago']:,.2f}"):
                                    st.write(f"**Forma de Pagamento:** {ped['forma_pagamento']}")
                                    
                                    # Puxar itens do pedido para exibir na tabela e gerar recibo se necessário
                                    itens_ped_raw = carregar_dataframe(f"SELECT produto as 'prod', caixas, qtd, unitario as 'unit', subtotal as 'total' FROM vendas_itens WHERE venda_id = {ped['id']}", conn)
                                    itens_dict = itens_ped_raw.to_dict(orient="records")
                                    
                                    st.table(itens_ped_raw.rename(columns={"prod": "DISCRIMINAÇÃO", "caixas": "QTD CAIXAS", "qtd": "TOTAL m²", "unit": "UNITÁRIO", "total": "TOTAL R$"}))
                                    
                                    # Botão para ver/baixar recibo a qualquer momento
                                    renderizar_acoes_recibo(cli, itens_dict, ped['total_pago'], ped['id'], ped['forma_pagamento'], ped['data_venda'])
                                    
                                    col_btn1, col_btn2 = st.columns(2)
                                    with col_btn1:
                                        if st.button(f"✅ Dar Baixa (Marcar como Entregue)", key=f"entregar_{ped['id']}"):
                                            conn_up = conectar()
                                            conn_up.execute("UPDATE vendas_cabecalho SET status_entrega = 'Entregue' WHERE id = ?", (ped['id'],))
                                            conn_up.commit()
                                            conn_up.close()
                                            st.success("Baixa realizada! Pedido movido para o histórico.")
                                            time.sleep(1)
                                            st.rerun()
                                    with col_btn2:
                                        if st.button(f"🗑️ Apagar Pedido", key=f"excluir_{ped['id']}"):
                                            conn_up = conectar()
                                            conn_up.execute("DELETE FROM vendas_cabecalho WHERE id = ?", (ped['id'],))
                                            conn_up.execute("DELETE FROM vendas_itens WHERE venda_id = ?", (ped['id'],))
                                            conn_up.commit()
                                            conn_up.close()
                                            st.success("Pedido excluído do sistema!")
                                            time.sleep(1)
                                            st.rerun()

                    with tab_hist:
                        historico = pedidos_cli[pedidos_cli['status_entrega'] == 'Entregue']
                        if historico.empty:
                            st.info("Nenhum histórico de entregas concluídas.")
                        else:
                            for _, ped in historico.iterrows():
                                with st.expander(f"🟢 Pedido Nº {ped['id']:04d} - Data: {ped['data_venda']} - R$ {ped['total_pago']:,.2f}"):
                                    st.write(f"**Status:** Entregue ✅ | **Pagamento:** {ped['forma_pagamento']}")
                                    
                                    itens_ped_raw = carregar_dataframe(f"SELECT produto as 'prod', caixas, qtd, unitario as 'unit', subtotal as 'total' FROM vendas_itens WHERE venda_id = {ped['id']}", conn)
                                    itens_dict = itens_ped_raw.to_dict(orient="records")
                                    
                                    st.table(itens_ped_raw.rename(columns={"prod": "DISCRIMINAÇÃO", "caixas": "QTD CAIXAS", "qtd": "TOTAL m²", "unit": "UNITÁRIO", "total": "TOTAL R$"}))
                                    
                                    # Opção de recibo também no histórico
                                    renderizar_acoes_recibo(cli, itens_dict, ped['total_pago'], ped['id'], ped['forma_pagamento'], ped['data_venda'])
                                    
                                    if st.button(f"🗑️ Apagar Histórico", key=f"excluir_hist_{ped['id']}"):
                                        conn_up = conectar()
                                        conn_up.execute("DELETE FROM vendas_cabecalho WHERE id = ?", (ped['id'],))
                                        conn_up.execute("DELETE FROM vendas_itens WHERE venda_id = ?", (ped['id'],))
                                        conn_up.commit()
                                        conn_up.close()
                                        st.success("Registro apagado!")
                                        time.sleep(1)
                                        st.rerun()

                st.divider()
                if st.button("🗑️ Excluir Ficha do Cliente", key="del_cli"):
                    conn_up = conectar()
                    conn_up.execute("DELETE FROM clientes WHERE id = ?", (int(cli["id"]),))
                    conn_up.commit()
                    conn_up.close()
                    st.success("Cadastro excluído com sucesso!")
                    time.sleep(1)
                    st.rerun()
                    
        conn.close() 
        
        st.divider()
        with st.container(border=True):
            st.subheader("📋 Lista Completa de Clientes Cadastrados")
            df_exibicao = all_cli.rename(columns={"id": "ID", "nome": "Nome", "cpf": "CPF", "telefone": "Telefone", "endereco": "Endereço", "bairro": "Bairro", "cep": "CEP"})
            st.dataframe(df_exibicao, use_container_width=True, hide_index=True)

elif menu == "📈 Histórico de Vendas":
    st.header("📈 Dashboard e Histórico Completo de Vendas")
    conn = conectar()
    query = "SELECT v.id as 'Pedido', v.data_venda as 'Data', c.nome as 'Cliente', v.forma_pagamento as 'Pagamento', v.total_pago as 'Valor Total' FROM vendas_cabecalho v JOIN clientes c ON v.cliente_id = c.id ORDER BY v.id DESC"
    df_h = carregar_dataframe(query, conn)
    conn.close()
    if not df_h.empty:
        st.subheader("📊 Indicadores de Desempenho")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de Pedidos", len(df_h))
        col2.metric("Faturamento Total", f"R$ {df_h['Valor Total'].sum():,.2f}")
        col3.metric("Ticket Médio", f"R$ {df_h['Valor Total'].mean():,.2f}")
        
        st.write("---")
        col_graf1, col_graf2 = st.columns(2)
        with col_graf1:
            st.write("**Faturamento por Forma de Pagamento**")
            st.bar_chart(df_h.groupby('Pagamento')['Valor Total'].sum(), color="#38bdf8") 
            
        with col_graf2:
            st.write("**Evolução de Vendas por Data**")
            st.line_chart(df_h.groupby('Data')['Valor Total'].sum(), color="#f8fafc")
            
        st.write("---")
        st.subheader("📋 Detalhamento dos Pedidos")
        st.dataframe(df_h, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma venda registrada até o momento.")

elif menu == "🏆 Ranking de Clientes":
    st.header("🏆 Ranking dos Melhores Clientes")
    conn = conectar()
    query_ranking = "SELECT c.nome as 'Cliente', c.cpf as 'CPF', c.telefone as 'Telefone', COUNT(v.id) as 'Total de Pedidos', SUM(v.total_pago) as 'Total Comprado (R$)' FROM vendas_cabecalho v JOIN clientes c ON v.cliente_id = c.id GROUP BY c.id ORDER BY SUM(v.total_pago) DESC"
    df_rank = carregar_dataframe(query_ranking, conn)
    conn.close()
    if not df_rank.empty:
        categorias = []
        for idx in range(len(df_rank)):
            if idx == 0: categorias.append("🥇 1º Lugar")
            elif idx == 1: categorias.append("🥈 2º Lugar")
            elif idx == 2: categorias.append("🥉 3º Lugar")
            else: categorias.append("Cliente")
        df_rank.insert(0, "Posição", categorias)
        st.subheader("🥇 Pódio de Clientes")
        st.dataframe(df_rank, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma compra registrada para gerar o ranking ainda.")

elif menu == "📦 Gestão de Produtos":
    st.header("📦 Gestão de Produtos e Estoque")
    tab1, tab2, tab3 = st.tabs(["📥 Repor Estoque", "🆕 Cadastrar Novo Produto", "💲 Atualizar Preço"])
    
    with tab1:
        conn = conectar()
        prods = carregar_dataframe("SELECT codigo, nome FROM produtos ORDER BY nome", conn)
        lista = [f"{r['codigo']} - {r['nome']}" for i, r in prods.iterrows()] if not prods.empty else []
        conn.close()
        
        if lista:
            with st.form("entrada"):
                escolha = st.selectbox("Selecione o Produto para repor", lista)
                cx_novas = st.number_input("Quantidade de Caixas/Unidades Recebidas", min_value=1, step=1)
                if st.form_submit_button("Confirmar Entrada"):
                    cod_p = escolha.split(" - ")[0]
                    conn = conectar()
                    m2_cx = conn.execute("SELECT m2_por_caixa FROM produtos WHERE codigo = ?", (cod_p,)).fetchone()[0]
                    conn.execute("UPDATE produtos SET m2_total = m2_total + ? WHERE codigo = ?", (cx_novas * m2_cx, cod_p))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Estoque atualizado na nuvem!")
                    time.sleep(1)
                    st.rerun()
        else:
            st.info("Nenhum produto cadastrado para repor.")

    with tab2:
        st.info("💡 **Dica para Argamassa, Rejunte, etc:** Coloque o **Rendimento** como **1**. O preço será o valor de 1 unidade.")
        with st.form("novo_produto"):
            c1, c2 = st.columns(2)
            with c1:
                novo_codigo = st.text_input("Código do Produto (Ex: ARG01, 0015)")
                novo_nome = st.text_input("Nome do Produto (Ex: Argamassa AC3 20kg)")
            with c2:
                novo_rendimento = st.number_input("Rendimento por Caixa/Unid (m²)", min_value=0.01, step=0.01, value=1.00)
                novo_preco = st.number_input("Preço por m² (ou da Unidade) R$", min_value=0.01, step=0.10, value=10.00)
            
            estoque_inicial = st.number_input("Estoque Inicial (Caixas/Unidades)", min_value=0, step=1, value=0)
            
            if st.form_submit_button("💾 Cadastrar Produto"):
                if novo_codigo and novo_nome:
                    conn = conectar()
                    try:
                        conn.execute("INSERT INTO produtos (codigo, nome, m2_por_caixa, preco_m2, m2_total) VALUES (?,?,?,?,?)", (novo_codigo, novo_nome, novo_rendimento, novo_preco, estoque_inicial * novo_rendimento))
                        conn.commit()
                        st.success(f"✅ Produto '{novo_nome}' cadastrado na nuvem!")
                        time.sleep(1)
                        st.rerun()
                    except Exception:
                        st.error("❌ Erro: Já existe um produto cadastrado com este código.")
                    finally:
                        conn.close()
                else:
                    st.warning("⚠️ Código e Nome são campos obrigatórios.")

    with tab3:
        if lista:
            prod_preco = st.selectbox("Selecione o Produto para alterar o valor:", [""] + lista)
            if prod_preco:
                cod_p2 = prod_preco.split(" - ")[0]
                conn = conectar()
                dados_p = conn.execute("SELECT preco_m2, m2_por_caixa FROM produtos WHERE codigo = ?", (cod_p2,)).fetchone()
                conn.close()
                
                preco_atual = dados_p[0]
                st.info(f"💰 Preço Atual: **R$ {preco_atual:,.2f}** por m²/unidade (Valor da Caixa fechada: R$ {preco_atual * dados_p[1]:,.2f})")
                
                with st.form("form_preco"):
                    novo_valor = st.number_input("Novo Preço por m² / Unidade (R$)", min_value=0.01, step=0.10, value=float(preco_atual))
                    if st.form_submit_button("Atualizar Preço"):
                        conn = conectar()
                        conn.execute("UPDATE produtos SET preco_m2 = ? WHERE codigo = ?", (novo_valor, cod_p2))
                        conn.commit()
                        conn.close()
                        st.success("✅ Preço sincronizado na nuvem!")
                        time.sleep(1)
                        st.rerun()
        else:
            st.info("Nenhum produto cadastrado.")