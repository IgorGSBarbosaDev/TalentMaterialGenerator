# Project Guidelines

## Code Style
- Keep changes focused and small; avoid broad refactors when not required by the task.
- Preserve existing naming and module layout patterns in app/config, app/core, and app/ui.
- Follow the existing test style in tests/unit and tests/integration: clear fixture setup, explicit assertions, and deterministic inputs.

## Architecture
- Entry point is main.py: create QApplication, load persisted config, apply stylesheet, then open AppWindow.
- app/config owns persisted settings and theme/QSS generation.
- app/core owns spreadsheet reading, schema validation, OneDrive cache/download behavior, PPTX generation, and worker-thread orchestration.
- app/ui owns widgets, screens, navigation, and user interaction flow.
- Keep boundaries strict: app/core must not import app/ui.

## Build and Test
- Environment setup:
  - python -m venv .venv
  - .venv\Scripts\activate
  - pip install -r requirements.txt
  - pip install -r requirements-dev.txt
- Run application:
  - python main.py
- Run tests:
  - python -m pytest
- Full delivery check (format, lint, typing, tests, architecture checks):
  - scripts\delivery_check.bat
- Build Windows executable:
  - build.bat

## Conventions
- Keep long-running generation and lookup tasks in QThread workers in app/core/worker.py, and communicate status/results through Qt Signals.
- Reuse the schema detection/remapping pipeline in app/core/reader.py for spreadsheet fields; do not bypass required-column validation.
- Preserve OneDrive cache behavior in app/core/reader.py (TTL-based cache reuse, force refresh support, local fallback on fetch failure).
- Keep settings backward compatible in app/config/settings.py, including runtime defaults and config key cleanup.

## Pitfalls
- Tests run headless by default via QT_QPA_PLATFORM=offscreen in tests/conftest.py; do not add tests that require a visible desktop session unless explicitly isolated.
- Architecture guardrails are enforced by scripts/check_architecture.py:
  - No legacy imports: customtkinter, PIL, app.core.image_utils
  - No app/core importing app/ui
  - app/core/worker.py must preserve QThread and Signal contract
- Repository automation and packaging scripts are Windows-oriented; prefer Windows-compatible commands when editing scripts and docs.

## References
- Project overview and setup: [README.md](../README.md)
- Rebuild roadmap: [docs/rebuild_v2_plan.md](../docs/rebuild_v2_plan.md)
- Current architecture/context snapshot: [docs/estado_atual_projeto_para_ia.md](../docs/estado_atual_projeto_para_ia.md)
- Extended project context for agents: [.github/instructions/USI_Generator_Contexto_Completo_v2.md](instructions/USI_Generator_Contexto_Completo_v2.md)
- Review workflow agent: [.github/agents/pragmatic-code-review-subagent.md](agents/pragmatic-code-review-subagent.md)
