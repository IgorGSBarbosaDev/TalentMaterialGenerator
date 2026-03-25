# Plano Técnico v2 — Rebuild do USI Generator no mesmo repositório

Este arquivo registra o plano de reconstrução do projeto em PySide6 com suporte a OneDrive com cache local, geração de ficha, geração de carômetro e UI multitela.

## Diretriz principal

- Substituição direta da base antiga em CustomTkinter
- MVP utilizável antes de refinamentos extras
- Fonte oficial de dados: OneDrive com fallback para cache local
- Foto real removida do escopo; usar placeholder circular branco

## Macroetapas

1. Reestruturar stack, bootstrap e tema
2. Refatorar core de leitura e geração
3. Implementar UI multitela em PySide6
4. Atualizar testes, scripts e documentação
