# 🏗️ Sistema de Gestão de Estoque Guarnieri (Web v2.0)

Este sistema foi migrado para uma interface Web utilizando **Python** e **Streamlit**, facilitando o controle de estoque de pisos, cadastro de clientes e histórico de vendas diretamente pelo navegador.

## 🚀 Como Rodar o Sistema

1. **Abra o Terminal (CMD)** na pasta do projeto:
   `cd Documents\guarnieri`

2. **Inicie o servidor do sistema**:
   `python -m streamlit run app_web.py`

3. **Acesse no Navegador**:
   O sistema abrirá automaticamente no endereço: `http://localhost:8501`

## 📋 Funcionalidades Atuais

* **🛒 Realizar Venda**: Baixa automática no estoque com cálculo inteligente de caixas (evita erro de divisão por zero).
* **👤 Gestão de Clientes**: Cadastro completo de clientes associados às vendas.
* **📈 Relatório de Vendas**: Histórico detalhado de todas as saídas com opção de cancelamento e devolução de estoque.
* **📦 Inventário**: Visualização em tempo real do saldo de metros quadrados (m²) disponível.

## 🛠️ Tecnologias Utilizadas

* **Linguagem**: Python 3.x
* **Interface**: Streamlit
* **Banco de Dados**: SQLite3 (Arquivo `estoque_piso.db`)
* **Versionamento**: Git & GitHub