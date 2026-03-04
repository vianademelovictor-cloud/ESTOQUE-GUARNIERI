import streamlit as st
import sqlite3
import pandas as pd
import math
from datetime import datetime

# Configuração da Página
st.set_page_config(page_title="Guarnieri Estoque", page_icon="🏗️", layout="wide")

def conectar():
    return sqlite3.connect('estoque_piso.db')

# --- INICIALIZAÇÃO DO BANCO (Cria ou ajusta as tabelas) ---
def inicializar_banco():
    conn = conectar()
    cursor = conn.cursor()
    # Tabela de Clientes
    cursor.execute('''CREATE TABLE IF NOT EXISTS clientes 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, cpf TEXT UNIQUE, telefone TEXT, endereco TEXT)''')
    
    # Tabela de Histórico - PADRONIZADA
    # Se a tabela já existir com erro, os comandos abaixo garantem a estrutura correta
    cursor.execute('''CREATE TABLE IF NOT EXISTS historico_vendas 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, data_venda TEXT, cliente TEXT, cpf TEXT, produto TEXT, qtd REAL)''')
    conn.commit()
    conn.close()

inicializar_banco()

st.title("🏗️ Gestão Guarnieri")

menu = st.sidebar.selectbox("Navegação", ["🛒 Realizar Venda", "👤 Clientes", "📈 Relatório de Vendas", "📋 Estoque"])

if menu == "🛒 Realizar Venda":
    st.header("Nova Venda")
    conn = conectar()
    clientes_df = pd.read_sql("SELECT nome, cpf FROM clientes", conn)
    conn.close()
    
    if clientes_df.empty:
        st.warning("Cadastre um cliente primeiro na aba 'Clientes'!")
    else:
        cli_sel = st.selectbox("Selecione o Cliente:", clientes_df['nome'].tolist())
        cpf_sel = clientes_df[clientes_df['nome'] == cli_sel]['cpf'].values[0]
        
        cod = st.text_input("Código do Produto")
        if cod:
            conn = conectar()
            piso_df = pd.read_sql(f"SELECT nome, m2_total, m2_por_caixa FROM produtos WHERE codigo = '{cod}'", conn)
            conn.close()
            
            if not piso_df.empty:
                piso = piso_df.iloc[0]
                st.info(f"**Piso:** {piso['nome']} | **Estoque:** {piso['m2_total']} m²")
                qtd_pedida = st.number_input("Metragem (m²)", min_value=0.0)
                
                if qtd_pedida > 0:
                    # Proteção contra divisão por zero (Erro Infinity)
                    m2_cx = piso['m2_por_caixa']
                    if m2_cx and m2_cx > 0:
                        caixas = math.ceil(qtd_pedida / m2_cx)
                        total_real = round(caixas * m2_cx, 2)
                        st.warning(f"Sugerido: {caixas} caixas (Total: {total_real} m²)")
                    else:
                        total_real = qtd_pedida
                    
                    if st.button("Finalizar Venda"):
                        if total_real <= piso['m2_total']:
                            dt = datetime.now().strftime("%d/%m/%Y %H:%M")
                            conn = conectar()
                            conn.execute("UPDATE produtos SET m2_total = m2_total - ? WHERE codigo = ?", (total_real, cod))
                            conn.execute("INSERT INTO historico_vendas (data_venda, cliente, cpf, produto, qtd) VALUES (?,?,?,?,?)", 
                                           (dt, cli_sel, cpf_sel, piso['nome'], total_real))
                            conn.commit()
                            conn.close()
                            st.success("Venda registrada com sucesso!")
                            st.rerun()
                        else:
                            st.error("Estoque insuficiente!")

elif menu == "👤 Clientes":
    st.header("Cadastro de Clientes")
    with st.form("form_cliente", clear_on_submit=True):
        n = st.text_input("Nome Completo")
        c = st.text_input("CPF")
        t = st.text_input("Telefone")
        e = st.text_input("Endereço")
        if st.form_submit_button("Salvar Cliente"):
            if n and c:
                try:
                    conn = conectar()
                    conn.execute("INSERT INTO clientes (nome, cpf, telefone, endereco) VALUES (?,?,?,?)", (n, c, t, e))
                    conn.commit()
                    conn.close()
                    st.success("Cliente cadastrado!")
                except:
                    st.error("Erro: CPF já cadastrado.")
            else:
                st.warning("Nome e CPF são obrigatórios!")

elif menu == "📈 Relatório de Vendas":
    st.header("Histórico de Vendas Realizadas")
    conn = conectar()
    try:
        # Busca padronizada com os nomes de colunas corretos
        df = pd.read_sql("SELECT id as 'Nº Pedido', data_venda as Data, cliente as Cliente, produto as Produto, qtd as 'M² Vendido' FROM historico_vendas ORDER BY id DESC", conn)
        
        if df.empty:
            st.info("Nenhuma venda registrada ainda.")
        else:
            st.dataframe(df, use_container_width=True)
            
            st.subheader("❌ Cancelar Venda")
            id_cancelar = st.number_input("Digite o número do pedido para excluir:", min_value=1, step=1)
            if st.button("Excluir Pedido e Devolver ao Estoque"):
                venda = conn.execute("SELECT produto, qtd FROM historico_vendas WHERE id = ?", (id_cancelar,)).fetchone()
                if venda:
                    conn.execute("UPDATE produtos SET m2_total = m2_total + ? WHERE nome = ?", (venda[1], venda[0]))
                    conn.execute("DELETE FROM historico_vendas WHERE id = ?", (id_cancelar,))
                    conn.commit()
                    st.success(f"Venda #{id_cancelar} cancelada!")
                    st.rerun()
                else:
                    st.error("Pedido não encontrado.")
    except Exception as e:
        st.error(f"Erro ao carregar histórico: {e}")
    finally:
        conn.close()

elif menu == "📋 Estoque":
    st.header("Inventário Atual")
    conn = conectar()
    st.dataframe(pd.read_sql("SELECT codigo, nome, m2_total FROM produtos", conn), use_container_width=True)
    conn.close()