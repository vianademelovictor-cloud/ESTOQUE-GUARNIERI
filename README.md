Sistema de Gestão Guarnieri Pisos (Web v2.0)
Este sistema foi migrado para uma interface Web utilizando Python e Streamlit, facilitando o controle de estoque de pisos, cadastro de clientes e a geração de recibos digitais diretamente pelo navegador.

Passo 1: Instalação do Ambiente (Preparação)
Antes de rodar o sistema pela primeira vez, é necessário instalar as bibliotecas no seu computador:

Abra o CMD (Prompt de Comando):

Pressione Windows + R, digite cmd e aperte Enter.

Instale o Streamlit e o Pandas:

Copie e cole o comando abaixo no terminal e aperte Enter:

pip install streamlit pandas

Passo 2: Como Abrir e Rodar o Sistema
Siga estes passos detalhados para iniciar o programa:

Abra o CMD.

Acesse a pasta do projeto:

cd Documents\guarnieri

Inicie o sistema com o comando Python:

python -m streamlit run app_web.py

Acesse no Navegador:

O sistema abrirá automaticamente no endereço: http://localhost:8501.

Novas Funcionalidades e Cálculos
O sistema foi atualizado para automatizar os processos da loja:

Cálculo Automático de Venda: O sistema solicita a metragem (m²) e calcula sozinho a quantidade de caixas fechadas necessária, eliminando erros de conta manual.

Recibo Digital Fiel: Gera um recibo na tela com o layout idêntico ao bloco verde físico, contendo o cabeçalho da Guarnieri Pisos (Limeira-SP) e o status de "PAGO".

Controle de Inventário: Visualização em tempo real do saldo de metros quadrados disponível no estoque.

Cadastro Completo: Registro de clientes com campos específicos para Bairro e CEP, fundamentais para a entrega e emissão do recibo.
