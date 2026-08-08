# --- IMPORTAÇÃO DE BIBLIOTECAS ---
import streamlit as st 
import streamlit.components.v1 as components
import sqlite3 
import pandas as pd
import math 
from datetime import datetime 
import time
from fpdf import FPDF 
import requests 
import json # Usado para enviar o HTML com segurança para o JavaScript

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Guarnieri Pisos - Oficial", page_icon="🏗️", layout="wide")

# --- CAMADA DE DADOS (DATABASE) ---
def conectar():
    return sqlite3.connect('estoque_piso.db', check_same_thread=False) 

def inicializar_banco():
    conn = conectar() 
    cursor = conn.cursor() 
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS produtos 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, codigo TEXT UNIQUE, nome TEXT, 
         m2_por_caixa REAL, preco_m2 REAL, m2_total REAL)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS clientes 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, cpf TEXT UNIQUE, 
         telefone TEXT, endereco TEXT, bairro TEXT, cep TEXT)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS vendas_cabecalho 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, data_venda TEXT, cliente_id INTEGER, 
         total_pago REAL, forma_pagamento TEXT)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS vendas_itens 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, venda_id INTEGER, produto TEXT, 
         qtd REAL, unitario REAL, subtotal REAL, caixas INTEGER)''')
    
    cursor.execute("PRAGMA table_info(vendas_itens)") 
    colunas_itens = [info[1] for info in cursor.fetchall()]
    if 'caixas' not in colunas_itens:
        cursor.execute("ALTER TABLE vendas_itens ADD COLUMN caixas INTEGER DEFAULT 0") 
        
    cursor.execute("PRAGMA table_info(vendas_cabecalho)") 
    colunas_vendas = [info[1] for info in cursor.fetchall()]
    if 'forma_pagamento' not in colunas_vendas:
        cursor.execute("ALTER TABLE vendas_cabecalho ADD COLUMN forma_pagamento TEXT DEFAULT 'Não Informado'") 
    
    conn.commit() 
    conn.close() 

inicializar_banco()

# --- COMPONENTES DE INTERFACE ---
@st.dialog("📄 Recibo de Pedido - Guarnieri Pisos")
def exibir_recibo(cliente_info, itens_carrinho, total_geral, pedido_id, forma_paga):
    st.markdown("<h2 style='text-align: center; color: #1e5d2d; margin-bottom:0;'>GUARNIERI PISOS</h2>", unsafe_allow_html=True)
    st.write(f"<p style='text-align: center;'><b>Fone: (19) 9 9473-6066</b><br>Rua Ana Herminia Trento Roque, 902 - Limeira - SP</p>", unsafe_allow_html=True)
    st.write("---")
    
    c1, c2 = st.columns(2)
    c1.write(f"**Data:** {datetime.now().strftime('%d/%m/%Y')}")
    c2.write(f"**PEDIDO Nº:** {pedido_id:04d}")
    
    st.write(f"**Cliente:** {cliente_info['nome']}")
    st.write(f"**Endereço:** {cliente_info['endereco']}, {cliente_info['bairro']}")
    st.write(f"**Forma de Pagamento:** :blue[{forma_paga}]")
    
    st.write("---")
    df_recibo = pd.DataFrame(itens_carrinho)
    df_recibo = df_recibo.rename(columns={'prod': 'DISCRIMINAÇÃO', 'caixas': 'QTD CAIXAS', 'qtd': 'TOTAL m²', 'unit': 'UNITÁRIO', 'total': 'TOTAL R$'})
    
    st.table(df_recibo[['DISCRIMINAÇÃO', 'QTD CAIXAS', 'TOTAL m²', 'TOTAL R$']])
    st.markdown(f"<h3 style='text-align: right;'>TOTAL R$ {total_geral:,.2f}</h3>", unsafe_allow_html=True)

    # --- SCRIPT WEB (JAVASCRIPT) - IMPRESSÃO PROFISSIONAL BLINDADA ---
    linhas_tabela = ""
    for item in itens_carrinho:
        linhas_tabela += f"""
            <tr>
                <td style='padding: 10px; border-bottom: 1px solid #ddd;'>{item['prod']}</td>
                <td style='text-align: center; padding: 10px; border-bottom: 1px solid #ddd;'>{item['caixas']}</td>
                <td style='text-align: center; padding: 10px; border-bottom: 1px solid #ddd;'>{item['qtd']:.2f}</td>
                <td style='text-align: right; padding: 10px; border-bottom: 1px solid #ddd;'>R$ {item['total']:,.2f}</td>
            </tr>
        """

    html_recibo = f"""
    <html>
    <head>
        <title>Recibo - Pedido {pedido_id:04d} - Guarnieri</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; color: #000; max-width: 800px; margin: auto; }}
            .header {{ text-align: center; color: #1e5d2d; margin-bottom: 0; font-size: 24px; }}
            .sub {{ text-align: center; font-size: 12px; margin-top: 5px; }}
            .info {{ margin: 25px 0; font-size: 14px; line-height: 1.6; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #ccc; padding: 10px; font-size: 14px; }}
            th {{ background-color: #f2f2f6; text-align: left; }}
            .total {{ text-align: right; font-size: 18px; font-weight: bold; margin-top: 20px; }}
            .pago {{ text-align: center; border: 3px solid black; padding: 12px; font-weight: bold; font-size: 22px; margin-top: 30px; background-color: #f0f2f6; }}
        </style>
    </head>
    <body>
        <h2 class="header">GUARNIERI PISOS</h2>
        <div class="sub">
            PISOS E REVESTIMENTOS - ARGAMASSA E REJUNTO TODAS AS CORES<br>
            <b>Fone: (19) 9 9473-6066</b><br>
            Rua Ana Herminia Trento Roque, 902 - Limeira - SP
        </div>
        <hr style="margin: 20px 0;">
        <div class="info">
            <p><b>Data:</b> {datetime.now().strftime('%d/%m/%Y')} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>PEDIDO Nº:</b> {pedido_id:04d}</p>
            <p><b>Cliente:</b> {cliente_info['nome']}<br>
            <b>Endereço:</b> {cliente_info['endereco']}, {cliente_info['bairro']}<br>
            <b>Pagamento:</b> {forma_paga}</p>
        </div>
        <hr style="margin: 20px 0;">
        <table>
            <thead>
                <tr>
                    <th>DISCRIMINAÇÃO</th>
                    <th style='text-align: center;'>QTD CAIXAS</th>
                    <th style='text-align: center;'>TOTAL m²</th>
                    <th style='text-align: right;'>TOTAL R$</th>
                </tr>
            </thead>
            <tbody>
                {linhas_tabela}
            </tbody>
        </table>
        <div class="total">VALOR TOTAL: R$ {total_geral:,.2f}</div>
        <div class="pago">PAGO VIA {forma_paga.upper()}</div>
    </body>
    </html>
    """
    
    # Codifica o HTML para JSON para não quebrar o JavaScript
    conteudo_safe = json.dumps(html_recibo)
    
    html_js = f"""
    <div>
        <button onclick="imprimirRecibo()" style="width: 100%; background-color: #ff9900; color: white; padding: 12px; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; font-size: 16px; font-family: sans-serif;">
            🖨️ Imprimir / Salvar Recibo
        </button>
    </div>
    <script>
        function imprimirRecibo() {{
            const janela = window.open('', '', 'width=800,height=600');
            janela.document.write({conteudo_safe});
            janela.document.close();
            janela.focus();
            setTimeout(() => {{
                janela.print();
                janela.close();
            }}, 500);
        }}
    </script>
    """
    components.html(html_js, height=60)

    # --- GERADOR DE PDF ---
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font("Arial", "B", 16)
    pdf.set_text_color(30, 93, 45) 
    pdf.cell(190, 10, "GUARNIERI PISOS", ln=True, align="C")
    
    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(190, 7, "Rua Ana Herminia Trento Roque, 902 - Limeira - SP", ln=True, align="C")
    pdf.cell(190, 7, "Fone: (19) 9 9473-6066", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, f"PEDIDO DE VENDA: {pedido_id:04d}", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.cell(190, 7, f"Data: {datetime.now().strftime('%d/%m/%Y')}", ln=True)
    pdf.cell(190, 7, f"Cliente: {cliente_info['nome']}", ln=True)
    pdf.cell(190, 7, f"Endereco: {cliente_info['endereco']}, {cliente_info['bairro']}", ln=True)
    pdf.cell(190, 7, f"Forma de Pagamento: {forma_paga}", ln=True)
    pdf.ln(5)

    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(80, 8, "PRODUTO", 1, 0, "C", True)
    pdf.cell(30, 8, "CAIXAS", 1, 0, "C", True)
    pdf.cell(40, 8, "TOTAL m2", 1, 0, "C", True)
    pdf.cell(40, 8, "TOTAL R$", 1, 1, "C", True)

    pdf.set_font("Arial", "", 10)
    for i in itens_carrinho:
        pdf.cell(80, 8, str(i['prod']), 1)
        pdf.cell(30, 8, str(i['caixas']), 1, 0, "C")
        pdf.cell(40, 8, f"{i['qtd']:.2f}", 1, 0, "C")
        pdf.cell(40, 8, f"R$ {i['total']:,.2f}", 1, 1, "R")

    pdf.ln(10)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(190, 10, f"VALOR TOTAL: R$ {total_geral:,.2f}", ln=True, align="R")

    pdf_output = pdf.output(dest='S').encode('latin-1', errors='replace')
    st.download_button(
        label="📥 Baixar Recibo em PDF",
        data=pdf_output,
        file_name=f"Recibo_Guarnieri_{pedido_id}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
    
    # --- GERADOR DE LINK WHATSAPP ---
    msg_recibo = (
        f"*📄 RECIBO DE PEDIDO - GUARNIERI PISOS*\n"
        f"-------------------------------------------\n"
        f"*PEDIDO Nº:* {pedido_id:04d}\n"
        f"*DATA:* {datetime.now().strftime('%d/%m/%Y')}\n"
        f"-------------------------------------------\n"
        f"*CLIENTE:* {cliente_info['nome']}\n"
        f"*PAGAMENTO:* {forma_paga}\n"
        f"-------------------------------------------\n"
    )
    
    for item in itens_carrinho:
        msg_recibo += f"• {item['prod']}: {item['caixas']} cx ({item['qtd']}m²)\n"
    
    msg_recibo += (
        f"-------------------------------------------\n"
        f"*VALOR TOTAL: R$ {total_geral:,.2f}*\n"
        f"-------------------------------------------\n"
        f"Agradecemos a preferência! 🏗️"
    )
    
    import urllib.parse 
    msg_url = urllib.parse.quote(msg_recibo)
    
    link_wa = f"https://wa.me/55{cliente_info['telefone']}?text={msg_url}" 
    
    st.link_button("📲 Enviar Recibo via WhatsApp", link_wa, use_container_width=True)

# --- NAVEGAÇÃO LATERAL ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/609/609803.png", width=100)
st.sidebar.title("Navegação")
menu = st.sidebar.selectbox("Selecione a Opção", 
    ["🛒 Realizar Venda", "📋 Estoque", "👤 Clientes", "🔍 Buscar Cliente", "📈 Histórico", "📥 Entrada de Material"])

# --- LÓGICA DAS TELAS ---
if menu == "🛒 Realizar Venda":
    st.header("🛒 Novo Pedido de Venda")
    conn = conectar()
    clientes_df = pd.read_sql("SELECT * FROM clientes", conn) 
    conn.close()
    
    if clientes_df.empty:
        st.warning("⚠️ Nenhum cliente cadastrado. Vá até a aba 'Clientes' primeiro.") 
    else: 
        col_c1, col_c2 = st.columns([2, 1])
        with col_c1:
            cli_nome = st.selectbox("Selecione o Cliente", clientes_df['nome'].tolist())
        with col_c2:
            forma_pago = st.selectbox("Forma de Pagamento", ["Pix", "Dinheiro", "Cartão de Crédito", "Cartão de Débito"])
            
        cli_dados = clientes_df[clientes_df['nome'] == cli_nome].iloc[0]
        
        if 'carrinho' not in st.session_state: 
            st.session_state.carrinho = []
        
        with st.container(border=True):
            st.subheader("Adicionar Produto")
            cod = st.text_input("Digite o Código do Produto")
            if cod:
                conn = conectar() 
                p = conn.execute("SELECT nome, m2_por_caixa, preco_m2, m2_total FROM produtos WHERE codigo = ?", (cod,)).fetchone()
                conn.close()
                if p:
                    st.info(f"📦 **{p[0]}** | Estoque: {p[3]} m² | Caixa: {p[1]} m²") 
                    m2_desejado = st.number_input("Quantos m² o cliente precisa?", min_value=0.0, step=0.1) 
                    
                    if m2_desejado > 0:
                        qtd_caixas = math.ceil(m2_desejado / p[1]) 
                        m2_final = round(qtd_caixas * p[1], 2)
                        v_total = round(m2_final * p[2], 2)
                        st.warning(f"💡 Venda mínima: **{qtd_caixas} caixas** ({m2_final} m²)")
                        
                        if st.button("➕ Adicionar ao Carrinho"):
                            st.session_state.carrinho.append({
                                "prod": p[0], "cod": cod, "caixas": qtd_caixas, 
                                "qtd": m2_final, "unit": p[2], "total": v_total
                            })
                            st.success("Adicionado!")
                            time.sleep(0.5)
                            st.rerun()
                else:
                    st.error("Produto não encontrado.")

        if st.session_state.carrinho: 
            st.subheader("Itens do Pedido")
            df_c = pd.DataFrame(st.session_state.carrinho)
            st.table(df_c[['prod', 'caixas', 'qtd', 'total']])
            total_pedido = df_c["total"].sum()
            st.subheader(f"Total Geral: R$ {total_pedido:,.2f}")
            
            if st.button("✅ Finalizar Venda e Gerar Recibo"):
                conn = conectar()
                cursor = conn.cursor()
                cursor.execute("""INSERT INTO vendas_cabecalho (data_venda, cliente_id, total_pago, forma_pagamento) 
                               VALUES (?,?,?,?)""", 
                               (datetime.now().strftime("%d/%m/%Y"), int(cli_dados['id']), total_pedido, forma_pago)) 
                v_id = cursor.lastrowid
                
                for item in st.session_state.carrinho:
                    cursor.execute("""INSERT INTO vendas_itens (venda_id, produto, qtd, unitario, subtotal, caixas) 
                                   VALUES (?,?,?,?,?,?)""",
                                   (v_id, item['prod'], item['qtd'], item['unit'], item['total'], item['caixas']))
                    cursor.execute("UPDATE produtos SET m2_total = m2_total - ? WHERE codigo = ?", (item['qtd'], item['cod'])) 
                
                conn.commit()
                conn.close()
                exibir_recibo(cli_dados, st.session_state.carrinho, total_pedido, v_id, forma_pago)
                st.session_state.carrinho = []

elif menu == "📋 Estoque":
    st.header("📋 Controle de Estoque")
    conn = conectar()
    df_est = pd.read_sql("SELECT codigo as 'Cód', nome as 'Produto', m2_por_caixa as 'm²/Cx', preco_m2 as 'Preço/m²', m2_total as 'Saldo Total (m²)' FROM produtos", conn)
    st.dataframe(df_est, use_container_width=True, hide_index=True)
    conn.close()

elif menu == "👤 Clientes":
    st.header("👤 Cadastro de Clientes")
    
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
            t = st.text_input("Telefone")
        with col2:
            e = st.text_input("Endereço (Rua, Nº)", value=st.session_state.endereco_api.get('logradouro', ''))
            b = st.text_input("Bairro", value=st.session_state.endereco_api.get('bairro', ''))
            cp = st.text_input("CEP", value=cep_busca if cep_busca else '')
        
        if st.form_submit_button("💾 Salvar Cliente"):
            if n and c:
                conn = conectar()
                try:
                    conn.execute("INSERT INTO clientes (nome, cpf, telefone, endereco, bairro, cep) VALUES (?,?,?,?,?,?)", (n,c,t,e,b,cp))
                    conn.commit()
                    st.success("Cliente cadastrado com sucesso!")
                    st.session_state.endereco_api = {"logradouro": "", "bairro": "", "localidade": "", "uf": ""}
                except:
                    st.error("Erro: CPF já cadastrado.")
                finally:
                    conn.close()
            else:
                st.warning("Nome e CPF são obrigatórios.")

elif menu == "🔍 Buscar Cliente":
    st.header("🔍 Detalhes do Cliente")
    cpf_busca = st.text_input("Digite o CPF para pesquisa")
    
    if st.button("Buscar"):
        if cpf_busca:
            conn = conectar()
            st.session_state['dados_cliente'] = pd.read_sql("SELECT * FROM clientes WHERE cpf = ?", conn, params=(cpf_busca,))
            conn.close()
    
    if 'dados_cliente' in st.session_state and not st.session_state['dados_cliente'].empty:
        cli = st.session_state['dados_cliente'].iloc[0]
        with st.container(border=True):
            st.subheader(f"Dados de {cli['nome']}")
            c1, c2, c3 = st.columns(3)
            c1.write(f"**CPF:** {cli['cpf']}")
            c2.write(f"**Fone:** {cli['telefone']}")
            c3.write(f"**CEP:** {cli['cep']}")
            st.write(f"**Endereço:** {cli['endereco']} - **Bairro:** {cli['bairro']}")
            
            st.divider()
            if st.button("🗑️ Excluir este cadastro"):
                conn = conectar()
                conn.execute("DELETE FROM clientes WHERE id = ?", (int(cli['id']),))
                conn.commit()
                conn.close()
                st.success("Excluído.")
                st.session_state['dados_cliente'] = pd.DataFrame()
                time.sleep(1)
                st.rerun()

elif menu == "📈 Histórico":
    st.header("📈 Dashboard e Histórico de Vendas")
    conn = conectar()
    
    query = '''
        SELECT v.id as 'Pedido', v.data_venda as 'Data', c.nome as 'Cliente', 
               v.forma_pagamento as 'Pagamento', v.total_pago as 'Valor Total'
        FROM vendas_cabecalho v 
        JOIN clientes c ON v.cliente_id = c.id 
        ORDER BY v.id DESC
    '''
    df_h = pd.read_sql(query, conn)
    conn.close()
    
    if not df_h.empty:
        st.subheader("📊 Indicadores de Desempenho")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de Pedidos", len(df_h))
        col2.metric("Faturamento Total", f"R$ {df_h['Valor Total'].sum():,.2f}")
        ticket_medio = df_h['Valor Total'].mean()
        col3.metric("Ticket Médio", f"R$ {ticket_medio:,.2f}")
        
        st.write("---")
        
        col_graf1, col_graf2 = st.columns(2)
        
        with col_graf1:
            st.write("**Faturamento por Forma de Pagamento**")
            df_pagamento = df_h.groupby('Pagamento')['Valor Total'].sum()
            st.bar_chart(df_pagamento, color="#1e5d2d") 
            
        with col_graf2:
            st.write("**Evolução de Vendas por Data**")
            df_data = df_h.groupby('Data')['Valor Total'].sum()
            st.line_chart(df_data, color="#ff9900")
            
        st.write("---")
        st.subheader("📋 Detalhamento dos Pedidos")
        
    st.dataframe(df_h, use_container_width=True, hide_index=True)

elif menu == "📥 Entrada de Material":
    st.header("📥 Entrada de Estoque")
    conn = conectar()
    prods = pd.read_sql("SELECT codigo, nome FROM produtos", conn)
    lista = [f"{r['codigo']} - {r['nome']}" for i, r in prods.iterrows()]
    conn.close()

    if lista:
        with st.form("entrada"):
            escolha = st.selectbox("Selecione o Produto", lista)
            cx_novas = st.number_input("Quantidade de Caixas Recebidas", min_value=1)
            if st.form_submit_button("Confirmar Entrada"):
                cod_p = escolha.split(" - ")[0]
                conn = conectar()
                m2_cx = conn.execute("SELECT m2_por_caixa FROM produtos WHERE codigo = ?", (cod_p,)).fetchone()[0]
                total_entrada = cx_novas * m2_cx
                conn.execute("UPDATE produtos SET m2_total = m2_total + ? WHERE codigo = ?", (total_entrada, cod_p))
                conn.commit()
                conn.close()
                st.success(f"Estoque atualizado: +{total_entrada} m²")
                time.sleep(1)
                st.rerun()