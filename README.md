# USI Generator v2

Aplicativo desktop em PySide6 para geracao de fichas de curriculo e carometros a partir de planilhas locais ou de um link do OneDrive com cache local automatico.

## Stack

- Python 3.11+
- PySide6
- python-pptx
- openpyxl
- pandas
- requests

## Fluxo de dados

- Arquivo local `.xlsx`
- Link do OneDrive com cache local automatico
- TTL padrao do cache: 24 horas
- Atualizacao manual da base disponivel na tela de configuracoes

## Colunas padrao da planilha

- `Matricula`
- `Nome`
- `Idade`
- `Cargo`
- `Antiguidade`
- `Formacao`
- `Resumo do perfil`
- `Trajetoria`
- `Nota 2025`
- `Nota 2024`
- `Nota 2023`

O sistema continua aceitando aliases conhecidos por auto-deteccao.
Quando as colunas `Nota 2025`, `Nota 2024` e `Nota 2023` estiverem mapeadas, o campo interno `performance` sera montado automaticamente como historico multilinha.

## Saida

- Fichas em `Documents/Usi Generator/fichas`
- Carometros em `Documents/Usi Generator/carometros`
- Os slides usam placeholder circular branco com borda verde para fotos

## Setup

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
python main.py
```

## Limitacoes do MVP

- Exportacao PDF continua desacoplada da UI principal
- Preview visual em tempo real ainda e simplificado
- Historico exibido na home e resumido
