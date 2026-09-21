# Sistema de Gestão de Vendas e Controle de Estoque - Guarnieri

Este é um sistema web desenvolvido em **Python** (utilizando **Streamlit**) com banco de dados em nuvem (**Turso / SQLite**) para gerenciar o estoque, as vendas e as entregas de um depósito de materiais de construção. O projeto atende aos requisitos do **Projeto Integrador (PI II) da UNIVESP**.

## Funcionalidades
* **Painel Web Moderno**: Interface responsiva e integrada baseada em Streamlit.
* **Gestão de Vendas (PDV)**: Suporte a venda por caixas fechadas/m² e por peças/unidades avulsas, com cálculo dinâmico de preços por modelo e abatimento automático do estoque.
* **Controle de Clientes**: Cadastro completo com consulta de endereço via API ViaCEP e histórico de compras.
* **Controle de Entregas e Logística**: Gestão de entregas pendentes e histórico, com opção de envio de rotas e dados diretamente para o entregador via WhatsApp (`+55 19 99685-2018`).
* **Comprovantes e Recibos**: Geração de recibos estilizados para impressão otimizada em preto, exportação em PDF e envio direto pelo WhatsApp para o cliente.
* **Alertas e Indicadores**: Alerta automático de estoque crítico e dashboards de desempenho financeiro.

## Estrutura do Projeto
* `app_web.py`: Aplicação web principal contendo toda a lógica de interface, controle de estoque e fluxo de vendas.
* `test_app.py`: Módulo de testes automatizados implementado para validar as funcionalidades do sistema e os requisitos técnicos do projeto.
* `requirements.txt`: Dependências e bibliotecas do projeto (Streamlit, FPDF, Libsql, Pandas, etc.).

## Tecnologias Utilizadas
* **Python** e **Streamlit** (Desenvolvimento da aplicação web)
* **Turso / SQLite** (Banco de dados relacional em nuvem)
* **JavaScript** (Manipulação de componentes de impressão e eventos de navegador)
* **API ViaCEP** (Consulta automatizada de endereços por CEP)
* **Git e GitHub** (Controle de versão e deploy)

## Como Executar
1. Certifique-se de ter o Python instalado e as dependências do `requirements.txt` configuradas.
2. Defina as credenciais de acesso ao banco de dados Turso no ambiente de segredos.
3. Inicie o sistema executando o comando no terminal:
   ```bash
   streamlit run app_web.py