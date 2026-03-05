import streamlit as st
import sqlite3
import pandas as pd
import math
from datetime import datetime

# Configuração da Página
st.set_page_config(page_title="Guarnieri Pisos - Oficial", page_icon="🏗️", layout="wide")

def conectar():
    return sqlite3.connect('estoque_piso.db', check_same_thread=False)

# --- ATUALIZAÇÃO AUTOMÁTICA DO BANCO (CORRIGE O ERRO DE COLUNA) ---
def inicializar_banco():
    conn = conectar()
    cursor = conn.cursor()
    # Criação das tabelas base
    cursor.execute('''CREATE TABLE IF NOT EXISTS produtos 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, codigo TEXT UNIQUE, nome TEXT, 
         m2_por_caixa REAL, preco_m2 REAL, m2_total REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS vendas_cabecalho 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, data_venda TEXT, cliente_id INTEGER, total_pago REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS vendas_itens 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, venda_id INTEGER, produto TEXT, qtd REAL, unitario REAL, subtotal REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS clientes 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, cpf TEXT UNIQUE, telefone TEXT, endereco TEXT, bairro TEXT, cep TEXT)''')
    
    # RESOLVE O ERRO: Adiciona a coluna 'caixas' se ela não existir
    cursor.execute("PRAGMA table_info(vendas_itens)")
    colunas = [info[1] for info in cursor.fetchall()]
    if 'caixas' not in colunas:
        cursor.execute("ALTER TABLE vendas_itens ADD COLUMN caixas INTEGER DEFAULT 0")
    
    conn.commit()
    conn.close()

inicializar_banco()

# --- FUNÇÃO DO RECIBO (COM COLUNA DE CAIXAS) ---
@st.dialog("📄 Recibo de Pedido - Guarnieri Pisos")
def exibir_recibo(cliente_info, itens_carrinho, total_geral, pedido_id):
    st.markdown("<h2 style='text-align: center; color: #1e5d2d; margin-bottom:0;'>GUARNIERI PISOS</h2>", unsafe_allow_html=True)
    st.write(f"<p style='text-align: center;'><b>Fone: (19) 9 9473-6066</b><br>Rua Ana Herminia Trento Roque, 902 - Limeira - SP</p>", unsafe_allow_html=True)
    st.write("---")
    
    c1, c2 = st.columns(2)
    c1.write(f"**Data:** {datetime.now().strftime('%d/%m/%Y')}")
    c2.write(f"**PEDIDO Nº:** {pedido_id:04d}")
    st.write(f"**Cliente:** {cliente_info['nome']}")
    st.write(f"**Endereço:** {cliente_info['endereco']}, {cliente_info['bairro']} - **CEP:** {cliente_info['cep']}")
    
    st.write("---")
    df_recibo = pd.DataFrame(itens_carrinho)
    df_recibo = df_recibo.rename(columns={'prod': 'DISCRIMINAÇÃO', 'caixas': 'QTD CAIXAS', 'qtd': 'TOTAL m²', 'unit': 'UNITÁRIO', 'total': 'TOTAL R$'})
    df_recibo['UNITÁRIO'] = df_recibo['UNITÁRIO'].map("R$ {:,.2f}".format)
    df_recibo['TOTAL R$'] = df_recibo['TOTAL R$'].map("R$ {:,.2f}".format)
    
    st.table(df_recibo[['DISCRIMINAÇÃO', 'QTD CAIXAS', 'TOTAL m²', 'UNITÁRIO', 'TOTAL R$']])
    
    st.write("---")
    st.markdown(f"<h2 style='text-align: right;'>TOTAL R$ {total_geral:,.2f}</h2>", unsafe_allow_html=True)
    st.markdown("<div style='text-align: center; border: 3px solid black; padding: 10px; font-weight: bold; background-color: #f0f2f6;'>PAGO</div>", unsafe_allow_html=True)

# --- MENU LATERAL ---
st.title("🏗️ Gestão Guarnieri Pisos")
menu = st.sidebar.selectbox("Navegação", ["🛒 Realizar Venda", "📋 Estoque", "👤 Clientes", "📈 Histórico"])

if menu == "🛒 Realizar Venda":
    st.header("Novo Pedido")
    conn = conectar()
    clientes_df = pd.read_sql("SELECT * FROM clientes", conn)
    conn.close()
    
    if clientes_df.empty:
        st.warning("Cadastre um cliente primeiro.")
    else:
        cli_nome = st.selectbox("Selecione o Cliente", clientes_df['nome'].tolist())
        cli_dados = clientes_df[clientes_df['nome'] == cli_nome].iloc[0]
        
        if 'carrinho' not in st.session_state: st.session_state.carrinho = []
        
        with st.container(border=True):
            cod = st.text_input("Código do Produto")
            if cod:
                conn = conectar()
                p = conn.execute("SELECT nome, m2_por_caixa, preco_m2, m2_total FROM produtos WHERE codigo = ?", (cod,)).fetchone()
                conn.close()
                if p:
                    st.info(f"📦 {p[0]} | Saldo: {p[3]} m²")
                    m2_desejado = st.number_input("Metragem (m²)", min_value=0.0, step=0.01)
                    if m2_desejado > 0:
                        qtd_caixas = math.ceil(m2_desejado / p[1])
                        m2_final = round(qtd_caixas * p[1], 2)
                        v_total = round(m2_final * p[2], 2)
                        st.warning(f"💡 Serão necessárias **{qtd_caixas} caixas** (Total: {m2_final} m²)")
                        
                        if st.button("➕ Adicionar Linha"):
                            st.session_state.carrinho.append({"prod": p[0], "cod": cod, "caixas": qtd_caixas, "qtd": m2_final, "unit": p[2], "total": v_total})
                            st.rerun()

        if st.session_state.carrinho:
            df_c = pd.DataFrame(st.session_state.carrinho)
            st.table(df_c[['prod', 'caixas', 'qtd', 'total']])
            total_pedido = df_c["total"].sum()
            
            if st.button("✅ Finalizar Pedido"):
                conn = conectar()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO vendas_cabecalho (data_venda, cliente_id, total_pago) VALUES (?,?,?)", (datetime.now().strftime("%d/%m/%Y"), int(cli_dados['id']), total_pedido))
                v_id = cursor.lastrowid
                for item in st.session_state.carrinho:
                    cursor.execute("INSERT INTO vendas_itens (venda_id, produto, qtd, unitario, subtotal, caixas) VALUES (?,?,?,?,?,?)",
                                   (v_id, item['prod'], item['qtd'], item['unit'], item['total'], item['caixas']))
                    cursor.execute("UPDATE produtos SET m2_total = m2_total - ? WHERE codigo = ?", (item['qtd'], item['cod']))
                conn.commit()
                conn.close()
                exibir_recibo(cli_dados, st.session_state.carrinho, total_pedido, v_id)
                st.session_state.carrinho = []

# Aba Estoque, Clientes e Histórico seguem o padrão funcional anterior
elif menu == "📋 Estoque":
    st.header("Estoque Atual")
    conn = conectar()
    df_est = pd.read_sql("SELECT codigo as 'Cód', nome as 'Produto', m2_total as 'Saldo (m²)' FROM produtos", conn)
    st.dataframe(df_est, use_container_width=True, hide_index=True)
    conn.close()

elif menu == "👤 Clientes":
    st.header("Novo Cliente")
    with st.form("cli"):
        n = st.text_input("Nome"); c = st.text_input("CPF"); t = st.text_input("Tel")
        e = st.text_input("Endereço"); b = st.text_input("Bairro"); cp = st.text_input("CEP")
        if st.form_submit_button("Salvar"):
            conn = conectar()
            conn.execute("INSERT INTO clientes (nome, cpf, telefone, endereco, bairro, cep) VALUES (?,?,?,?,?,?)", (n,c,t,e,b,cp))
            conn.commit(); conn.close(); st.success("Salvo!")

elif menu == "📈 Histórico":
    st.header("Pedidos Realizados")
    conn = conectar()
    df_h = pd.read_sql('''SELECT v.id as 'Nº', v.data_venda as Data, c.nome as Cliente, v.total_pago as 'Total' 
                          FROM vendas_cabecalho v JOIN clientes c ON v.cliente_id = c.id ORDER BY v.id DESC''', conn)
    conn.close()
    st.dataframe(df_h, use_container_width=True)