import sqlite3
import os

def importar_massa():
    try:
        # Deleta o banco antigo para evitar erro de coluna faltando
        if os.path.exists('estoque_piso.db'):
            os.remove('estoque_piso.db')

        conexao = sqlite3.connect('estoque_piso.db')
        cursor = conexao.cursor()

        cursor.execute('''
            CREATE TABLE produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT UNIQUE NOT NULL,
                nome TEXT,
                formato TEXT,
                m2_total REAL NOT NULL,
                m2_por_caixa REAL DEFAULT 0
            )
        ''')

        with open('lista_produtos.txt', 'r', encoding='utf-8') as arquivo:
            for linha in arquivo:
                dados = linha.strip().split(';')
                if len(dados) == 4:
                    cursor.execute('''
                        INSERT INTO produtos (codigo, nome, formato, m2_total)
                        VALUES (?, ?, ?, ?)
                    ''', (dados[0].strip(), dados[1].strip(), dados[2].strip(), float(dados[3])))

        conexao.commit()
        conexao.close()
        print("IMPORTACAO CONCLUIDA COM SUCESSO!")

    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    importar_massa()