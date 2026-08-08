import math

# --- REGRA DE NEGÓCIO DO SISTEMA ---
# Esta função simula exatamente o cálculo que fazemos no app_web.py
def calcular_caixas(m2_desejado, m2_por_caixa):
    if m2_desejado <= 0 or m2_por_caixa <= 0:
        return 0
    return math.ceil(m2_desejado / m2_por_caixa)

# --- TESTES AUTOMATIZADOS (O que a banca quer ver) ---
def test_calculo_de_caixas_exato():
    # Cenário 1: A metragem desejada dá uma quantidade exata de caixas.
    # Ex: Cliente quer 10m², a caixa tem 2.5m². Resultado esperado: 4 caixas.
    resultado = calcular_caixas(10, 2.5)
    assert resultado == 4

def test_calculo_de_caixas_arredondado():
    # Cenário 2: A metragem desejada sobra um pouco, o sistema PRECISA arredondar para cima.
    # Ex: Cliente quer 11m², a caixa tem 2.5m². Resultado esperado: 5 caixas.
    resultado = calcular_caixas(11, 2.5)
    assert resultado == 5

def test_calculo_protecao_zero():
    # Cenário 3: Evitar erros se o usuário digitar 0m².
    resultado = calcular_caixas(0, 2.5)
    assert resultado == 0