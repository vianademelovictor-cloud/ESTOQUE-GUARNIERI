import sqlite3

def atualizar_banco_produtos():
    conn = sqlite3.connect('estoque_piso.db')
    cursor = conn.cursor()
    
    # Recria a tabela com as novas colunas para o PI da UNIVESP
    cursor.execute('DROP TABLE IF EXISTS produtos')
    cursor.execute('''CREATE TABLE produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT UNIQUE,
        nome TEXT,
        m2_total REAL,
        m2_por_caixa REAL,
        preco_m2 REAL
    )''')
    
    try:
        # Lendo com separador de PONTO E VÍRGULA
        with open('lista_produtos.txt', 'r', encoding='utf-8') as f:
            for linha in f:
                if linha.strip():
                    partes = linha.strip().split(';') # <--- MUDANÇA AQUI
                    if len(partes) == 5:
                        cod, nome, est, cx, preco = partes
                        cursor.execute('''INSERT INTO produtos 
                            (codigo, nome, m2_total, m2_por_caixa, preco_m2) 
                            VALUES (?,?,?,?,?)''',
                            (cod.strip(), nome.strip(), float(est), float(cx), float(preco)))
        conn.commit()
        print("✅ Banco atualizado usando o separador ';'!")
    except Exception as e:
        print(f"❌ Erro na importação: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    atualizar_banco_produtos()