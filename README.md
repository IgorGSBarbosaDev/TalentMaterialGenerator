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
- `Cargo`
- `Idade`
- `Antiguidade`
- `Formacao`
- `Resumo do perfil`
- `Trajetoria`
- `Avaliação 2025`
- `Avaliação 2024`
- `Avaliação 2023`
- `Nota 2025`
- `Potencial 2025`
- `Nota 2024`
- `Potencial 2024`
- `Nota 2023`
- `Potencial 2023`
- `CEO1`
- `CEO2`
- `CEO3`
- `CEO4`

O sistema continua aceitando aliases conhecidos por auto-deteccao.
Na ficha, os campos anuais exibidos (`nota_2025`, `nota_2024`, `nota_2023`) podem vir diretamente das colunas consolidadas `Avaliação <ano>` ou ser derivados de `Nota <ano>` + `Potencial <ano>`.
As colunas `CEO1` a `CEO4` sao aceitas no contrato da planilha; a ficha nao usa esses campos no layout, enquanto templates de carometro usam `CEO3` e `CEO4` quando exigidos.
Quando os valores anuais estiverem disponiveis, o campo interno `performance` sera montado automaticamente como historico multilinha.

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
