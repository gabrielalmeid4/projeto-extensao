# Gerador de Crachás - IFPI

Sistema para geração de crachás em PDF para alunos esportistas do IFPI.

## Requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

## Instalação

1. Clone o repositório:
```
git clone [URL_DO_REPOSITÓRIO]
cd projeto-extensao
```

2. Crie um ambiente virtual:
```
python -m venv venv
```

3. Ative o ambiente virtual:
- Windows:
```
venv\Scripts\activate
```
- Linux/Mac:
```
source venv/bin/activate
```

4. Instale as dependências:
```
pip install -r requirements.txt
```

## Executando o Projeto

1. Com o ambiente virtual ativado, execute:
```
uvicorn app.main:app --reload
```

2. Acesse o sistema no navegador:
```
http://localhost:8000
```

## Estrutura de Diretórios

- app/
  - api/         # Rotas da API
  - services/    # Serviços (geração de PDF)
  - static/      # Arquivos estáticos (CSS, JS)
  - templates/   # Templates HTML
- venv/          # Ambiente virtual
- requirements.txt
- README.md