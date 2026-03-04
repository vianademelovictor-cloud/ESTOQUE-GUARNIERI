import streamlit as st
import sqlite3
import pandas as pd
import math
from datetime import datetime

# Configuração da Página
st.set_page_config(page_title="Sistema Guarnieri", page_icon="🏗️", layout="wide")

def conectar():
    return sqlite3.connect('estoque_piso.db')

# Criação das tabelas (Clientes e Histórico)
def inicializar_banco():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS clientes 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, cpf TEXT UNIQUE NOT NULL, telefone TEXT, endereco TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS historico_vendas 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, data_venda TEXT, cliente_nome TEXT, produto_nome TEXT, quantidade_m2 REAL)''')
    conn.commit()
    conn.close()

inicializar_banco()

st.sidebar.title("Menu Guarnieri")
menu = st.sidebar.selectbox("Navegação", ["🛒 Vendas", "👤 Clientes", "📊 Histórico", "📋 Estoque"])

if menu == "🛒 Vendas":
    st.header("Realizar Venda")
    conn = conectar()
    clientes_df = pd.read_sql("SELECT nome FROM clientes", conn)
    conn.close()
    
    if clientes_df.empty:
        st.warning("⚠️ Cadastre um cliente primeiro na aba 'Clientes'!")
    else:
        cliente_sel = st.selectbox("Selecione o Cliente:", clientes_df['nome'].tolist())
        cod = st.text_input("Código do Produto")
        
        if cod:
            conn = conectar()
            piso_df = pd.read_sql(f"SELECT nome, m2_total, m2_por_caixa FROM produtos WHERE codigo = '{cod}'", conn)
            conn.close()
            
            if not piso_df.empty:
                piso = piso_df.iloc[0]
                st.info(f"**Piso:** {piso['nome']} | **Estoque:** {piso['m2_total']} m²")
                qtd = st.number_input("Metragem Desejada (m²)", min_value=0.0)
                
                if qtd > 0:
                    # --- PROTEÇÃO CONTRA O ERRO DE INFINITO (DIVISÃO POR ZERO) ---
                    m2_caixa = piso['m2_por_caixa']
                    if m2_caixa and m2_caixa > 0:
                        caixas = math.ceil(qtd / m2_caixa)
                        total_real = round(caixas * m2_caixa, 2)
                        st.warning(f"📦 Entregar {caixas} caixas (Total: {total_real} m²)")
                    else:
                        total_real = qtd
                        st.info(f"📦 Item sem metragem por caixa. Total: {total_real} m²")
                    
                    if st.button("Confirmar Venda"):
                        if total_real <= piso['m2_total']:
                            novo_est = round(piso['m2_total'] - total_real, 2)
                            dt = datetime.now().strftime("%d/%m/%Y %H:%M")
                            conn = conectar()
                            conn.execute("UPDATE produtos SET m2_total = ? WHERE codigo = ?", (novo_est, cod))
                            conn.execute("INSERT INTO historico_vendas (data_venda, cliente_nome, produto_nome, quantidade_m2) VALUES (?,?,?,?)",
                                         (dt, cliente_sel, piso['nome'], total_real))
                            conn.commit()
                            conn.close()
                            st.success("✅ Venda realizada!")
                            st.rerun()
                        else:
                            st.error("Estoque insuficiente!")

elif menu == "👤 Clientes":
    st.header("Cadastro de Clientes")
    with st.form("cad_cli", clear_on_submit=True):
        n = st.text_input("Nome"); c = st.text_input("CPF"); t = st.text_input("Tel"); e = st.text_input("End")
        if st.form_submit_button("Salvar"):
            try:
                conn = conectar(); conn.execute("INSERT INTO clientes (nome, cpf, telefone, endereco) VALUES (?,?,?,?)", (n,c,t,e)); conn.commit(); conn.close()
                st.success("Cliente cadastrado!")
            except: st.error("CPF já cadastrado ou erro no banco.")

elif menu == "📊 Histórico":
    st.header("Relatório de Vendas")
    conn = conectar()
    df_h = pd.read_sql("SELECT data_venda as Data, cliente_nome as Cliente, produto_nome as Produto, quantidade_m2 as M2 FROM historico_vendas ORDER BY id DESC", conn)
    conn.close()
    st.dataframe(df_h, use_container_width=True)

elif menu == "📋 Estoque":
    st.header("Estoque Geral")
    conn = conectar()
    df_e = pd.read_sql("SELECT codigo, nome, m2_total, m2_por_caixa FROM produtos", conn)
    conn.close()
    st.dataframe(df_e, use_container_width=True)