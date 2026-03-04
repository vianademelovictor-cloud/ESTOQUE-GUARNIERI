# Sistema de Controle de Estoque - Guarnieri

Este é um sistema desenvolvido em **Python** com banco de dados **SQLite** para gerenciar o estoque de um depósito de pisos e materiais de construção.

## Funcionalidades
* **Menu Principal**: Central de acesso para todas as operações.
* **Vendas Automáticas**: Busca por código, cálculo de caixas fechadas e baixa automática no estoque.
* **Cálculo de Metragem**: Converte a necessidade do cliente (m²) para quantidade de caixas real.
* **Importação em Massa**: Lê arquivos `.txt` para cadastrar centenas de produtos de uma vez.
* **Cadastro Manual**: Tela para adicionar novos itens individualmente.

## Estrutura do Projeto
* `menu.py`: Tela principal do sistema.
* `vendas.py`: Módulo de saídas e cálculos de venda.
* `cadastro.py`: Módulo de entrada de novos produtos.
* `importar.py`: Script de automação para carga de dados.
* `estoque_piso.db`: Banco de dados SQLite.
* `lista_produtos.txt`: Arquivo mestre de importação.

## Como usar
1. Certifique-se de ter o Python instalado.
2. Execute o arquivo `menu.py` para abrir o sistema.
3. Para importar novos dados, edite o `lista_produtos.txt` seguindo o padrão:
   `Código;Nome;Formato;Estoque_Total;M2_por_Caixa`