# USI Generator v2

Aplicativo desktop em PySide6 para geração de fichas de currículo e carômetros a partir de planilhas locais ou de um link do OneDrive com cache local automático.

## Stack

- Python 3.11+
- PySide6
- python-pptx
- openpyxl
- pandas
- requests

## Fluxo de dados

- Arquivo local `.xlsx`
- Link do OneDrive com cache local automático
- TTL padrão do cache: 24 horas
- Atualização manual da base disponível na tela de configurações

## Saída

- Fichas em `output_dir/fichas`
- Carômetros em `output_dir/carometros`
- Os slides usam placeholder circular branco com borda verde para fotos

## Setup

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
python main.py
```

## Limitações do MVP

- Exportação PDF continua desacoplada da UI principal
- Preview visual em tempo real ainda é simplificado
- Histórico exibido na home é resumido
