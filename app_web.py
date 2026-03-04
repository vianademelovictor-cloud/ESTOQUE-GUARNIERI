import streamlit as st
import sqlite3
import pandas as pd
import math
from datetime import datetime

# Configuração da Página
st.set_page_config(page_title="Sistema Guarnieri", page_icon="🏗️", layout="wide")

def conectar():
    """Conecta ao banco de dados SQLite."""
    return sqlite3.connect('estoque_piso.db')

def criar_tabelas():
    """Garante que as tabelas de clientes e histórico existam."""
    conn = conectar()
    cursor = conn.cursor()
    # Tabela de Clientes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf TEXT UNIQUE NOT NULL,
            telefone TEXT,
            endereco TEXT
        )
    ''')
    # Tabela de Histórico Associado
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historico_vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_venda TEXT,
            cliente_nome TEXT,
            produto_nome TEXT,
            quantidade_m2 REAL
        )
    ''')
    conn.commit()
    conn.close()

# Inicializa o banco ao abrir
criar_tabelas()

st.title("🏗️ Guarnieri - Gestão Integrada Web")

# --- MENU LATERAL ---
menu = st.sidebar.selectbox("Navegação", ["🛒 Realizar Venda", "👤 Clientes", "📈 Histórico", "📋 Estoque"])

if menu == "🛒 Realizar Venda":
    st.header("Nova Venda")
    
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
                
                qtd = st.number_input("Metragem Desejada (m²)", min_value=0.0, step=0.1)
                
                if qtd > 0:
                    # --- NOVO MODELO DE CÁLCULO (BLINDADO CONTRA ERRO INFINITY) ---
                    m2_caixa = piso['m2_por_caixa']
                    
                    if m2_caixa and m2_caixa > 0:
                        caixas = math.ceil(qtd / m2_caixa)
                        total_real = round(caixas * m2_caixa, 2)
                        st.warning(f"📦 Sugestão: Entregar {caixas} caixas (Total: {total_real} m²)")
                    else:
                        # Se o m2_caixa for 0 ou nulo, ele não tenta dividir
                        total_real = qtd
                        st.info(f"📦 Item sem m²/caixa definido. Vendendo metragem direta: {total_real} m²")
                    
                    if st.button(f"Confirmar Venda para {cliente_sel}"):
                        if total_real <= piso['m2_total']:
                            novo_est = round(piso['m2_total'] - total_real, 2)
                            dt = datetime.now().strftime("%d/%m/%Y %H:%M")
                            
                            conn = conectar()
                            # 1. Baixa no estoque
                            conn.execute("UPDATE produtos SET m2_total = ? WHERE codigo = ?", (novo_est, cod))
                            # 2. Registra no histórico associando ao cliente
                            conn.execute("INSERT INTO historico_vendas (data_venda, cliente_nome, produto_nome, quantidade_m2) VALUES (?,?,?,?)",
                                         (dt, cliente_sel, piso['nome'], total_real))
                            conn.commit()
                            conn.close()
                            
                            st.success("✅ Venda finalizada com sucesso!")
                            st.rerun()
                        else:
                            st.error("❌ Estoque insuficiente!")
            else:
                st.error("Produto não encontrado.")

elif menu == "👤 Clientes":
    st.header("Cadastro de Clientes")
    with st.form("cad_cli", clear_on_submit=True):
        n = st.text_input("Nome"); c = st.text_input("CPF"); t = st.text_input("Telefone"); e = st.text_input("Endereço")
        if st.form_submit_button("Salvar Cliente"):
            if n and c: