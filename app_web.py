import streamlit as st
import sqlite3
import pandas as pd
import math
from datetime import datetime
import time

# Configuração da Página
st.set_page_config(page_title="Guarnieri Pisos - Oficial", page_icon="🏗️", layout="wide")

def conectar():
    return sqlite3.connect('estoque_piso.db', check_same_thread=False)

# --- INICIALIZAÇÃO DO BANCO ---
def inicializar_banco():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS produtos 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, codigo TEXT UNIQUE, nome TEXT, 
         m2_por_caixa REAL, preco_m2 REAL, m2_total REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS vendas_cabecalho 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, data_venda TEXT, cliente_id INTEGER, total_pago REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS vendas_itens 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, venda_id INTEGER, produto TEXT, qtd REAL, unitario REAL, subtotal REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS clientes 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, cpf TEXT UNIQUE, telefone TEXT, endereco TEXT, bairro TEXT, cep TEXT)''')
    conn.commit()
    conn.close()

inicializar_banco()

# --- FUNÇÃO DO RECIBO (USA DADOS DA MEMÓRIA PARA NÃO DAR ERRO) ---
@st.dialog("📄 Recibo de Pedido - Guarnieri Pisos")
def exibir_recibo_imediato(cliente_info, itens_carrinho, total_geral, pedido_id):
    st.markdown("<h2 style='text-align: center; color: #1e5d2d; margin-bottom:0;'>GUARNIERI PISOS</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 14px;'>PISOS E REVESTIMENTOS - ARGAMASSA E REJUNTO TODAS AS CORES</p>", unsafe_allow_html=True)
    st.write(f"<p style='text-align: center;'><b>Fone: (19) 9 9473-6066</b><br>Rua Ana Herminia Trento Roque, 902 - Limeira - SP</p>", unsafe_allow_html=True)
    st.write("---")
    
    c1, c2 = st.columns(2)
    c1.write(f"**Data:** {datetime.now().strftime('%d/%m/%Y')}")
    c2.write(f"**PEDIDO Nº:** {pedido_id:04d}")
    
    st.write(f"**Nome:** {cliente_info['nome']}")
    st.write(f"**Endereço:** {cliente_info['endereco']}, {cliente_info['bairro']} - **CEP:** {cliente_info['cep']}")
    st.write(f"**Fone:** {cliente_info['telefone']}")
    
    st.write("---")
    # Tabela formatada igual ao bloco verde
    df_recibo = pd.DataFrame(itens_carrinho)
    df_recibo = df_recibo.rename(columns={'prod': 'DISCRIMINAÇÃO', 'qtd': 'QUANT. m²', 'unit': 'UNITÁRIO', 'total': 'TOTAL R$'})
    
    # Formatação de Moeda
    df_recibo['UNITÁRIO'] = df_recibo['UNITÁRIO'].map("R$ {:,.2f}".format)
    df_recibo['TOTAL R$'] = df_recibo['TOTAL R$'].map("R$ {:,.2f}".format)
    
    st.table(df_recibo[['DISCRIMINAÇÃO', 'QUANT. m²', 'UNITÁRIO', 'TOTAL R$']])
    
    st.write("---")
    st.markdown(f"<h2 style='text-align: right;'>VALOR TOTAL R$ {total_geral:,.2f}</h2>", unsafe_allow_html=True)
    st.markdown("<div style='text-align: center; border: 3px solid black; padding: 10px; font-weight: bold; font-size: 20px; background-color: #f0f2f6;'>PAGO</div>", unsafe_allow_html=True)
    st.caption("CONFIRA SUA MERCADORIA NO ATO DA ENTREGA")

# --- INTERFACE ---
st.title("🏗️ Gestão Guarnieri Pisos")
menu = st.sidebar.selectbox("Menu", ["🛒 Realizar Venda", "📋 Estoque", "👤 Clientes", "📈 Histórico"])

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
                    m2 = st.number_input("Metragem (m²)", min_value=0.0)
                    if m2 > 0:
                        cxs = math.ceil(m2 / p[1])
                        total_m2 = round(cxs * p[1], 2)
                        total_rs = round(total_m2 * p[2], 2)
                        if st.button("➕ Adicionar Linha"):
                            st.session_state.carrinho.append({"prod": p[0], "cod": cod, "qtd": total_m2, "unit": p[2], "total": total_rs})
                            st.rerun()

        if st.session_state.carrinho:
            df_c = pd.DataFrame(st.session_state.carrinho)
            total_pedido = df_c["total"].sum()
            st.table(df_c[['prod', 'qtd', 'total']])
            
            if st.button("✅ Finalizar Pedido"):
                conn = conectar()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO vendas_cabecalho (data_venda, cliente_id, total_pago) VALUES (?,?,?)", 
                               (datetime.now().strftime("%d/%m/%Y"), int(cli_dados['id']), total_pedido))
                v_id = cursor.lastrowid
                for item in st.session_state.carrinho:
                    cursor.execute("INSERT INTO vendas_itens (venda_id, produto, qtd, unitario, subtotal) VALUES (?,?,?,?,?)",
                                   (v_id, item['prod'], item['qtd'], item['unit'], item['total']))
                    cursor.execute("UPDATE produtos SET m2_total = m2_total - ? WHERE codigo = ?", (item['qtd'], item['cod']))
                conn.commit()
                conn.close()
                
                # EXIBE O RECIBO USANDO OS DADOS DA MEMÓRIA (NÃO DÁ ERRO)
                exibir_recibo_imediato(cli_dados, st.session_state.carrinho, total_pedido, v_id)
                st.session_state.carrinho = []

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