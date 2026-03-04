import tkinter as tk
from tkinter import messagebox
import sqlite3

# --- FUNCAO PARA SALVAR ---
def salvar_produto():
    cod = entry_codigo.get()
    nom = entry_nome.get()
    m2_t = entry_m2_total.get()
    m2_c = entry_m2_caixa.get()

    if not cod or not m2_t:
        messagebox.showerror("Erro", "Codigo e Metragem Total sao obrigatorios!")
        return

    try:
        conexao = sqlite3.connect('estoque_piso.db')
        cursor = conexao.cursor()
        
        # Cria a tabela se nao existir
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT UNIQUE NOT NULL,
                nome TEXT,
                m2_total REAL NOT NULL,
                m2_por_caixa REAL
            )
        ''')

        # Converte virgula para ponto para o banco aceitar
        valor_total = float(m2_t.replace(',', '.'))
        valor_caixa = float(m2_c.replace(',', '.')) if m2_c else 0

        cursor.execute('''
            INSERT INTO produtos (codigo, nome, m2_total, m2_por_caixa)
            VALUES (?, ?, ?, ?)
        ''', (cod, nom, valor_total, valor_caixa))
        
        conexao.commit()
        conexao.close()
        
        messagebox.showinfo("Sucesso", "Produto cadastrado com sucesso!")
        entry_codigo.delete(0, tk.END)
        entry_nome.delete(0, tk.END)
        entry_m2_total.delete(0, tk.END)
        entry_m2_caixa.delete(0, tk.END)
        
    except sqlite3.IntegrityError:
        messagebox.showerror("Erro", "Este codigo ja existe!")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro: {e}")

# --- INTERFACE ---
root = tk.Tk()
root.title("Cadastro de Estoque")
root.geometry("400x400")

tk.Label(root, text="CADASTRO DE PISOS", font=("Arial", 12, "bold")).pack(pady=10)

tk.Label(root, text="Codigo:").pack()
entry_codigo = tk.Entry(root)
entry_codigo.pack(pady=5)

tk.Label(root, text="Nome:").pack()
entry_nome = tk.Entry(root)
entry_nome.pack(pady=5)

tk.Label(root, text="Metragem Total em Estoque:").pack()
entry_m2_total = tk.Entry(root)
entry_m2_total.pack(pady=5)

tk.Label(root, text="M2 por Caixa:").pack()
entry_m2_caixa = tk.Entry(root)
entry_m2_caixa.pack(pady=5)

tk.Button(root, text="SALVAR", command=salvar_produto, bg="green", fg="white").pack(pady=20)

root.mainloop()