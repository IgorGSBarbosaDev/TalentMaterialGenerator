from __future__ import annotations

import unicodedata
from pathlib import Path

from openpyxl import load_workbook

COLUMN_VARIATIONS: dict[str, tuple[str, ...]] = {
    "nome": ("nome", "name", "nome_completo", "colaborador", "funcionario"),
    "idade": ("idade", "age", "anos"),
    "cargo": ("cargo", "funcao", "funcao", "role", "posicao", "posicao"),
    "antiguidade": ("antiguidade", "tempo_empresa", "anos_empresa", "admissao"),
    "formacao": ("formacao", "formacao", "graduacao", "escolaridade", "education"),
    "resumo_perfil": ("resumo", "perfil", "resumo_perfil", "descricao", "bio"),
    "trajetoria": ("trajetoria", "trajetoria", "historico", "historico", "carreira"),
    "performance": (
        "performance",
        "avaliacao",
        "avaliacao",
        "resultado",
        "nota_historico",
    ),
    "foto": ("foto", "photo", "imagem", "image", "arquivo_foto"),
    "area": ("area", "area", "departamento", "setor", "gerencia"),
    "potencial": ("potencial", "potential"),
    "nota": ("nota", "score", "avaliacao_atual", "resultado_atual"),
}

_NORMALIZED_VARIATIONS: dict[str, set[str]] = {
    field: {variation for variation in variations}
    for field, variations in COLUMN_VARIATIONS.items()
}


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    return ascii_only.strip().lower().replace(" ", "_")


for _field, _variations in COLUMN_VARIATIONS.items():
    _NORMALIZED_VARIATIONS[_field] = {_normalize_text(item) for item in _variations}


def read_spreadsheet(path: str) -> list[dict[str, str]]:
    """Read an .xlsx file and return one dict per row."""
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(path)

    workbook = load_workbook(filename=file_path, data_only=True)
    worksheet = workbook.active
    if worksheet is None:
        return []

    rows = worksheet.iter_rows(values_only=True)
    headers_row = next(rows, None)

    if headers_row is None:
        return []

    headers = ["" if header is None else str(header).strip() for header in headers_row]
    if not any(headers):
        return []

    parsed_rows: list[dict[str, str]] = []
    for row in rows:
        row_data: dict[str, str] = {}
        has_value = False

        for index, header in enumerate(headers):
            if header == "":
                continue

            value = row[index] if index < len(row) else None
            text_value = "" if value is None else str(value)
            row_data[header] = text_value
            if text_value != "":
                has_value = True

        if row_data and has_value:
            parsed_rows.append(row_data)

    return parsed_rows


def detect_columns(headers: list[str]) -> dict[str, str | None]:
    """Map incoming headers into known application fields."""
    mapping: dict[str, str | None] = {
        "nome": None,
        "idade": None,
        "cargo": None,
        "antiguidade": None,
        "formacao": None,
        "resumo_perfil": None,
        "trajetoria": None,
        "performance": None,
        "foto": None,
        "area": None,
        "potencial": None,
        "nota": None,
    }

    for header in headers:
        normalized_header = _normalize_text(str(header))
        for field, accepted in _NORMALIZED_VARIATIONS.items():
            if mapping[field] is None and normalized_header in accepted:
                mapping[field] = header
                break

    return mapping


def validate_required_columns(mapping: dict[str, str | None]) -> list[str]:
    """Return required fields that are missing from the mapping."""
    required = ("nome", "cargo")
    missing = [field for field in required if not mapping.get(field)]
    return missing


def parse_multiline_field(value: str) -> list[str]:
    """Split text by semicolon/newline, trim, and remove empty entries."""
    if value == "":
        return []

    normalized = value.replace("\r\n", "\n").replace("\r", "\n")
    items: list[str] = []
    for line in normalized.split("\n"):
        for chunk in line.split(";"):
            cleaned = chunk.strip()
            if cleaned:
                items.append(cleaned)

    return items


def normalize_filename(name: str) -> str:
    """Remove accents and replace spaces with underscores."""
    if name == "":
        return ""

    normalized = unicodedata.normalize("NFKD", name)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    return ascii_only.replace(" ", "_")
