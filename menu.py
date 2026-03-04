import tkinter as tk
import os

def abrir_vendas():
    os.system("python vendas.py")

def abrir_cadastro():
    os.system("python cadastro.py")

root = tk.Tk()
root.title("Gestão de Depósito - Pisos e Argamassas")
root.geometry("400x300")

tk.Label(root, text="SISTEMA DE ESTOQUE", font=("Arial", 16, "bold")).pack(pady=20)

btn_vender = tk.Button(root, text="TELA DE VENDAS", command=abrir_vendas, 
                       bg="#007bff", fg="white", font=("Arial", 12, "bold"), width=25, height=2)
btn_vender.pack(pady=10)

btn_cadastrar = tk.Button(root, text="CADASTRAR PRODUTOS", command=abrir_cadastro, 
                          bg="#28a745", fg="white", font=("Arial", 12, "bold"), width=25, height=2)
btn_cadastrar.pack(pady=10)

tk.Label(root, text="v1.0 - Depósito de Pisos", fg="gray").pack(side="bottom", pady=10)

root.mainloop()