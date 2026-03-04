import sqlite3
from tkinter import *
from tkinter import messagebox

class CadastroCliente:
    def __init__(self, master):
        self.janela = master
        self.janela.title("Sistema Guarnieri - Cadastro de Clientes")
        self.janela.geometry("450x400")
        self.janela.configure(padx=20, pady=20)

        # Criar a tabela ao iniciar a classe
        self.criar_tabela()

        # --- Elementos da Interface ---
        Label(self.janela, text="CADASTRO DE CLIENTE", font=("Arial", 14, "bold")).pack(pady=10)

        self.label_nome = Label(self.janela, text="Nome Completo:")
        self.label_nome.pack(anchor=W)
        self.entry_nome = Entry(self.janela, width=50)
        self.entry_nome.pack(pady=5)

        self.label_cpf = Label(self.janela, text="CPF:")
        self.label_cpf.pack(anchor=W)
        self.entry_cpf = Entry(self.janela, width=50)
        self.entry_cpf.pack(pady=5)

        self.label_tel = Label(self.janela, text="Telefone:")
        self.label_tel.pack(anchor=W)
        self.entry_tel = Entry(self.janela, width=50)
        self.entry_tel.pack(pady=5)

        self.label_end = Label(self.janela, text="Endereço:")
        self.label_end.pack(anchor=W)
        self.entry_end = Entry(self.janela, width=50)
        self.entry_end.pack(pady=5)

        # Botão de Ação
        self.btn_salvar = Button(
            self.janela, 
            text="SALVAR CLIENTE", 
            command=self.salvar_dados,
            bg="#2ecc71", 
            fg="white", 
            font=("Arial", 10, "bold"),
            height=2
        )
        self.btn_salvar.pack(fill=X, pady=20)

    def criar_tabela(self):
        """Cria a tabela de clientes no banco existente se não houver."""
        conexao = sqlite3.connect('estoque_piso.db')
        cursor = conexao.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                cpf TEXT UNIQUE NOT NULL,
                telefone TEXT,
                endereco TEXT
            )
        ''')
        conexao.commit()
        conexao.close()

    def salvar_dados(self):
        """Extrai os dados dos inputs e salva no SQLite."""
        nome = self.entry_nome.get()
        cpf = self.entry_cpf.get()
        tel = self.entry_tel.get()
        end = self.entry_end.get()

        if not nome or not cpf:
            messagebox.showwarning("Atenção", "Nome e CPF são campos obrigatórios!")
            return

        try:
            conexao = sqlite3.connect('estoque_piso.db')
            cursor = conexao.cursor()
            cursor.execute('''
                INSERT INTO clientes (nome, cpf, telefone, endereco) 
                VALUES (?, ?, ?, ?)
            ''', (nome, cpf, tel, end))
            
            conexao.commit()
            conexao.close()
            
            messagebox.showinfo("Sucesso", f"Cliente {nome} cadastrado com sucesso!")
            self.limpar_campos()
            
        except sqlite3.IntegrityError:
            messagebox.showerror("Erro", "Este CPF já está cadastrado!")
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro: {e}")

    def limpar_campos(self):
        """Limpa as entradas de texto."""
        self.entry_nome.delete(0, END)
        self.entry_cpf.delete(0, END)
        self.entry_tel.delete(0, END)
        self.entry_end.delete(0, END)

# Para testar o arquivo individualmente:
if __name__ == "__main__":
    root = Tk()
    app = CadastroCliente(root)
    root.mainloop()