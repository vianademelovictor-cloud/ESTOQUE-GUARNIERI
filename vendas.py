import tkinter as tk
from tkinter import messagebox
import sqlite3
import math

def buscar_produto():
    cod = entry_busca.get().strip()
    if not cod: return

    conexao = sqlite3.connect('estoque_piso.db')
    cursor = conexao.cursor()
    # Busca nome, estoque total, m2 por caixa e formato
    cursor.execute("SELECT nome, m2_total, m2_por_caixa, formato FROM produtos WHERE codigo = ?", (cod,))
    resultado = cursor.fetchone()
    conexao.close()

    if resultado:
        global m2_caixa_atual, estoque_atual, nome_piso
        nome_piso = resultado[0]
        estoque_atual = resultado[1]
        m2_caixa_atual = resultado[2]
        formato = resultado[3] if resultado[3] else "N/A"
        
        lbl_info["text"] = f"Produto: {nome_piso}\nFormato: {formato}\nEstoque: {estoque_atual} m2\nCada caixa tem: {m2_caixa_atual} m2"
    else:
        lbl_info["text"] = ""
        messagebox.showwarning("Aviso", "Codigo nao encontrado!")

def calcular_e_vender():
    try:
        m2_pedido = float(entry_venda.get().replace(',', '.'))
        
        if m2_pedido > estoque_atual:
            messagebox.showerror("Erro", "Estoque insuficiente!")
            return

        # LOGICA DO CALCULO
        if m2_caixa_atual > 0:
            # Arredonda para cima para dar caixas fechadas
            caixas = math.ceil(m2_pedido / m2_caixa_atual)
            m2_real = round(caixas * m2_caixa_atual, 2)
            msg = f"Venda sugerida: {caixas} caixas\nTotal Real: {m2_real} m2\n\nConfirma a baixa no estoque?"
        else:
            # Se for argamassa ou item unitario (m2_por_caixa = 0)
            m2_real = m2_pedido
            msg = f"Venda de {m2_real} unidades/m2.\n\nConfirma a baixa?"

        if messagebox.askyesno("Confirmar Venda", msg):
            novo_estoque = round(estoque_atual - m2_real, 2)
            
            conexao = sqlite3.connect('estoque_piso.db')
            cursor = conexao.cursor()
            cursor.execute("UPDATE produtos SET m2_total = ? WHERE codigo = ?", (novo_estoque, entry_busca.get().strip()))
            conexao.commit()
            conexao.close()
            
            messagebox.showinfo("Sucesso", "Estoque atualizado!")
            entry_venda.delete(0, tk.END)
            buscar_produto() # Atualiza a tela com o novo estoque
            
    except ValueError:
        messagebox.showerror("Erro", "Digite um valor numerico valido.")
    except NameError:
        messagebox.showerror("Erro", "Busque um produto primeiro!")

# --- INTERFACE ---
root = tk.Tk()
root.title("Terminal de Vendas - Guarnieri")
root.geometry("450x550")

tk.Label(root, text="CAIXA / VENDAS", font=("Arial", 16, "bold")).pack(pady=20)

tk.Label(root, text="Codigo do Piso:").pack()
entry_busca = tk.Entry(root, font=("Arial", 12), width=20)
entry_busca.pack(pady=5)
tk.Button(root, text="BUSCAR", command=buscar_produto, bg="blue", fg="white", width=15).pack(pady=5)

lbl_info = tk.Label(root, text="", font=("Arial", 11), fg="darkblue", justify="left", bg="#eee", width=40, height=5)
lbl_info.pack(pady=20)

tk.Label(root, text="Quantos m2 o cliente quer?").pack()
entry_venda = tk.Entry(root, font=("Arial", 14), width=15)
entry_venda.pack(pady=5)

tk.Button(root, text="CALCULAR E FINALIZAR", command=calcular_e_vender, 
          bg="green", fg="white", font=("Arial", 12, "bold"), height=2, width=25).pack(pady=30)

root.mainloop()