import streamlit as st
import sqlite3
import pandas as pd
import math
from datetime import datetime
import time
from fpdf import FPDF
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Guarnieri Pisos - Oficial", page_icon="🏗️", layout="wide")

# --- CAMADA DE DADOS (DATABASE) ---
def conectar():
    return sqlite3.connect('estoque_piso.db', check_same_thread=False)

def inicializar_banco():
    conn = conectar()
    cursor = conn.cursor()
    
    # Tabela de Produtos
    cursor.execute('''CREATE TABLE IF NOT EXISTS produtos 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, codigo TEXT UNIQUE, nome TEXT, 
         m2_por_caixa REAL, preco_m2 REAL, m2_total REAL)''')
    
    # Tabela de Clientes
    cursor.execute('''CREATE TABLE IF NOT EXISTS clientes 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, cpf TEXT UNIQUE, 
         telefone TEXT, endereco TEXT, bairro TEXT, cep TEXT)''')
    
    # Tabela de Vendas (Cabeçalho com Forma de Pagamento)
    cursor.execute('''CREATE TABLE IF NOT EXISTS vendas_cabecalho 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, data_venda TEXT, cliente_id INTEGER, 
         total_pago REAL, forma_pagamento TEXT)''')
    
    # Tabela de Itens da Venda
    cursor.execute('''CREATE TABLE IF NOT EXISTS vendas_itens 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, venda_id INTEGER, produto TEXT, 
         qtd REAL, unitario REAL, subtotal REAL, caixas INTEGER)''')
    
    # MIGRAÇÃO: Garante que colunas novas existam em bancos antigos
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

# Inicia o banco ao abrir o app
inicializar_banco()

# --- COMPONENTES DE INTERFACE ---
@st.dialog("📄 Recibo de Pedido - Guarnieri Pisos")
def exibir_recibo(cliente_info, itens_carrinho, total_geral, pedido_id, forma_paga):
    # --- PARTE 1: O QUE APARECE NA TELA DO NAVEGADOR ---
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

    # --- PARTE 2: CRIAÇÃO DO PDF PARA DOWNLOAD ---
    pdf = FPDF()
    pdf.add_page()
    
    # Cabeçalho do PDF
    pdf.set_font("Arial", "B", 16)
    pdf.set_text_color(30, 93, 45) # Verde Guarnieri
    pdf.cell(190, 10, "GUARNIERI PISOS", ln=True, align="C")
    
    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(190, 7, "Rua Ana Herminia Trento Roque, 902 - Limeira - SP", ln=True, align="C")
    pdf.cell(190, 7, "Fone: (19) 9 9473-6066", ln=True, align="C")
    pdf.ln(10)

    # Dados do Cliente no PDF
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, f"PEDIDO DE VENDA: {pedido_id:04d}", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.cell(190, 7, f"Data: {datetime.now().strftime('%d/%m/%Y')}", ln=True)
    pdf.cell(190, 7, f"Cliente: {cliente_info['nome']}", ln=True)
    pdf.cell(190, 7, f"Endereco: {cliente_info['endereco']}, {cliente_info['bairro']}", ln=True)
    pdf.cell(190, 7, f"Forma de Pagamento: {forma_paga}", ln=True)
    pdf.ln(5)

    # Tabela de Itens no PDF
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

    # Botão de Download do PDF
    pdf_output = pdf.output(dest='S').encode('latin-1', errors='replace')
    st.download_button(
        label="📥 Baixar Recibo em PDF",
        data=pdf_output,
        file_name=f"Recibo_Guarnieri_{pedido_id}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
    
    # --- RECIBO FORMATADO PARA WHATSAPP ---
    # Criamos um texto que parece um recibo físico
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
    
    # Adiciona os itens um por um na mensagem
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
        # Layout de seleção superior
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
                # Salva o cabeçalho com a forma de pagamento
                cursor.execute("""INSERT INTO vendas_cabecalho (data_venda, cliente_id, total_pago, forma_pagamento) 
                               VALUES (?,?,?,?)""", 
                               (datetime.now().strftime("%d/%m/%Y"), int(cli_dados['id']), total_pedido, forma_pago))
                v_id = cursor.lastrowid
                
                # Salva os itens e baixa o estoque
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
    with st.form("cadastro_cli"):
        col1, col2 = st.columns(2)
        with col1:
            n = st.text_input("Nome Completo")
            c = st.text_input("CPF (Somente números)")
            t = st.text_input("Telefone")
        with col2:
            e = st.text_input("Endereço (Rua, Nº)")
            b = st.text_input("Bairro")
            cp = st.text_input("CEP")
        
        if st.form_submit_button("💾 Salvar Cliente"):
            if n and c:
                conn = conectar()
                try:
                    conn.execute("INSERT INTO clientes (nome, cpf, telefone, endereco, bairro, cep) VALUES (?,?,?,?,?,?)", (n,c,t,e,b,cp))
                    conn.commit()
                    st.success("Cliente cadastrado com sucesso!")
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
    st.header("📈 Histórico de Vendas")
    conn = conectar()
    # SQL com JOIN para mostrar o nome do cliente e a forma de pagamento
    query = '''
        SELECT v.id as 'Pedido', v.data_venda as 'Data', c.nome as 'Cliente', 
               v.forma_pagamento as 'Pagamento', v.total_pago as 'Valor Total'
        FROM vendas_cabecalho v 
        JOIN clientes c ON v.cliente_id = c.id 
        ORDER BY v.id DESC
    '''
    df_h = pd.read_sql(query, conn)
    conn.close()
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
                # Busca m2 por caixa para converter
                m2_cx = conn.execute("SELECT m2_por_caixa FROM produtos WHERE codigo = ?", (cod_p,)).fetchone()[0]
                total_entrada = cx_novas * m2_cx
                conn.execute("UPDATE produtos SET m2_total = m2_total + ? WHERE codigo = ?", (total_entrada, cod_p))
                conn.commit()
                conn.close()
                st.success(f"Estoque atualizado: +{total_entrada} m²")
                time.sleep(1)
                st.rerun()
