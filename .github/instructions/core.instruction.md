# Core Layer Instructions — USI Generator

> Instruções específicas para desenvolvimento em `app/core/`

---

## Responsabilidade da Camada Core

A camada `app/core/` contém **toda a lógica de negócio** do USI Generator. É completamente independente da interface gráfica.

**Regra absoluta:** nenhum arquivo em `app/core/` pode importar de `app/ui/` ou de `customtkinter`.

---

## Módulos e suas Responsabilidades

### `reader.py`

Responsável por toda interação com a planilha Excel.

**Funções públicas obrigatórias:**

```python
def read_spreadsheet(path: str) -> list[dict]:
    """
    Lê o .xlsx e retorna lista de dicts, um por linha.
    Lança FileNotFoundError se o arquivo não existir.
    Células vazias retornam string vazia, nunca None.
    """

def detect_columns(headers: list[str]) -> dict[str, str | None]:
    """
    Mapeia cabeçalhos reais da planilha para campos esperados pelo app.
    Retorna None para campos não encontrados.
    Usa comparação case-insensitive e sem acentos.
    """

def validate_required_columns(mapping: dict) -> list[str]:
    """
    Retorna lista de campos obrigatórios que não foram mapeados.
    Campos obrigatórios: nome, cargo.
    """

def parse_multiline_field(value: str) -> list[str]:
    """
    Separa um campo de texto em lista por ';' ou quebra de linha.
    Remove itens vazios e faz strip() em cada item.
    """

def normalize_filename(name: str) -> str:
    """
    Remove acentos, substitui espaços por underline.
    Ex: "Ana Bárbara" → "Ana_Barbara"
    """
```

**Mapeamento de colunas (heurística):**

| Campo | Variações aceitas |
|---|---|
| `nome` | nome, name, nome_completo, colaborador, funcionario |
| `idade` | idade, age, anos |
| `cargo` | cargo, funcao, função, role, posição, posicao |
| `antiguidade` | antiguidade, tempo_empresa, anos_empresa, admissao |
| `formacao` | formacao, formação, graduacao, escolaridade, education |
| `resumo_perfil` | resumo, perfil, resumo_perfil, descricao, bio |
| `trajetoria` | trajetoria, trajetória, historico, histórico, carreira |
| `performance` | performance, avaliacao, avaliação, resultado, nota_historico |
| `foto` | foto, photo, imagem, image, arquivo_foto |
| `area` | area, área, departamento, setor, gerencia |
| `potencial` | potencial, potential |
| `nota` | nota, score, avaliacao_atual, resultado_atual |

---

### `image_utils.py`

Responsável por processamento de imagens com Pillow.

**Funções públicas obrigatórias:**

```python
def make_circular_image(path: str) -> Image | None:
    """
    Abre a imagem e aplica máscara circular RGBA.
    Retorna None (sem exceção) se o arquivo não existir ou for inválido.
    """

def generate_avatar(name: str) -> Image:
    """
    Gera avatar circular com iniciais do nome.
    Cor de fundo derivada de hash do nome (sempre consistente para o mesmo nome).
    Nunca lança exceção — usa fallback se name for vazio.
    """

def resize_image(img: Image, width: int, height: int) -> Image:
    """Redimensiona mantendo proporção via LANCZOS."""

def save_temp_png(img: Image) -> str:
    """
    Salva imagem como PNG temporário e retorna o caminho.
    Usar tempfile.NamedTemporaryFile com delete=False.
    """
```

**Regra do recorte circular:**

`python-pptx` não suporta crop circular nativo. O fluxo correto é:

1. Carregar imagem com Pillow
2. Criar máscara circular em canal alpha
3. Salvar como PNG temporário com canal RGBA
4. Inserir o PNG temporário no slide com `add_picture()`
5. Limpar o temporário após o slide ser salvo

---

### `generator_ficha.py`

Responsável por montar slides de Ficha de Currículo com `python-pptx`.

**Dimensões obrigatórias do slide:**

```python
from pptx.util import Inches

SLIDE_WIDTH  = Inches(13.271)   # WIDE format Usiminas — NUNCA usar 10"
SLIDE_HEIGHT = Inches(7.500)
```

**Posições exatas dos elementos (em inches):**

| Elemento | left | top | width | height |
|---|---|---|---|---|
| Título (nome) | 0.397 | 0.251 | 11.833 | 0.477 |
| Box verde canto dir. | 12.358 | 0.364 | 0.778 | 0.477 |
| Fundo cinza grande | 0.149 | 2.427 | 11.214 | 4.921 |
| Fundo cinza menor | 1.908 | 0.922 | 10.966 | 6.417 |
| Acento esq. | 2.309 | 0.980 | 0.202 | 1.279 |
| Foto (circular) | 0.385 | 1.000 | 1.382 | 1.344 |
| Nome+Cargo+Antiguidade | 1.922 | 1.009 | 3.740 | 0.791 |
| Label FORMAÇÃO | 0.240 | 3.075 | 4.400 | 0.337 |
| Texto formação | 0.240 | 3.361 | 4.739 | 0.303 |
| Label TRAJETÓRIA | 0.332 | 4.186 | 1.455 | 0.337 |
| Texto trajetória | 0.326 | 4.640 | 5.411 | 2.128 |
| Linha divisória vertical | 5.719 | 1.009 | 0 | 6.220 |
| Label RESUMO PERFIL | 5.737 | 1.022 | 1.817 | 0.337 |
| Texto resumo | 5.737 | 1.423 | 6.898 | 1.745 |
| Label PERFORMANCE | 5.775 | 3.341 | 1.860 | 0.337 |
| Texto performance | 5.867 | 3.694 | 1.835 | 0.505 |
| Barra rodapé | 0.000 | 7.118 | 4.797 | 0.388 |

**Cores:**

```python
VERDE_TITULO     = "#92D050"   # título e labels de seção da ficha
CINZA_TRAJETORIA = "#666666"   # texto de trajetória
```

**Busca de foto (ordem de prioridade):**

1. Coluna `foto` da planilha → busca arquivo na pasta de fotos
2. Nome normalizado do colaborador → busca `nome_sobrenome.jpg` / `.png`
3. Avatar com iniciais gerado via `image_utils.generate_avatar(name)`

**Função principal:**

```python
def generate_ficha_pptx(
    employees: list[dict],
    photos_dir: str,
    output_dir: str,
    callback: callable | None = None
) -> list[str]:
    """
    Gera um .pptx por colaborador em output_dir/fichas/.
    Chama callback({"type": "progress", "current": n, "total": total, "name": nome})
    a cada slide concluído.
    Retorna lista de caminhos dos arquivos gerados.
    """
```

---

### `generator_carom.py`

Responsável por montar slides de Carômetro.

**Cores por potencial:**

```python
CORES_POTENCIAL = {
    "alto":  "#84BD00",   # verde
    "médio": "#F59E0B",   # âmbar
    "medio": "#F59E0B",
    "baixo": "#EF4444",   # vermelho
}
```

**Cores por nota (numérica):**

```python
def get_score_color(score: float) -> str:
    if score >= 4.0:    return "#84BD00"
    if score >= 3.0:    return "#F59E0B"
    return "#EF4444"
```

**Configuração do carômetro:**

```python
CaromConfig = TypedDict("CaromConfig", {
    "colunas": int,           # 3, 4 ou 5
    "agrupamento": str | None, # campo da planilha ou None
    "titulo": str,
    "show_nota": bool,
    "show_potencial": bool,
    "show_cargo": bool,
    "cores_automaticas": bool,
})
```

**Regras de layout:**
- 1 slide por grupo quando agrupamento ativo
- Ordenação dentro do grupo: decrescente por nota
- Cabeçalho: fundo verde escuro, título branco

---

### `pdf_exporter.py`

Responsável pela conversão PPTX → PDF.

**Estratégia:**
1. Tentar LibreOffice headless (primário)
2. Fallback: comtypes COM do Windows (se Office instalado)
3. Se nenhum disponível: retornar `False` e logar aviso

```python
def export_to_pdf(pptx_path: str, output_dir: str) -> bool:
    """
    Retorna True se exportou com sucesso, False caso contrário.
    Nunca lança exceção — tudo tratado internamente.
    """
```

**Comando LibreOffice:**

```python
cmd = [
    libreoffice_path,
    "--headless",
    "--convert-to", "pdf",
    "--outdir", output_dir,
    pptx_path
]
subprocess.run(cmd, timeout=60, check=True)
```

---

## Padrão de Callback para Progresso

Todas as funções de geração recebem um `callback` opcional para comunicar progresso à UI:

```python
# Tipos de mensagem na fila
{"type": "log",      "message": "✓ Gerando slide: Ana Martins", "level": "success"}
{"type": "log",      "message": "⚠ Foto não encontrada: João",  "level": "warning"}
{"type": "log",      "message": "✗ Erro no colaborador: Pedro", "level": "error"}
{"type": "progress", "current": 3, "total": 10, "name": "Ana Martins"}
{"type": "complete", "output_dir": "/caminho/saida", "count": 10, "elapsed": "00:08"}
{"type": "error",    "message": "Planilha não encontrada"}
```

---

## TDD — Requisitos para Core

Antes de implementar qualquer função pública do core, o arquivo de teste correspondente deve existir e falhar.

Toda função pública deve ter testes cobrindo:

- **Happy path:** comportamento esperado com dados válidos
- **Edge cases:** campos vazios, listas vazias, valores nulos
- **Error cases:** arquivos inexistentes, dados inválidos
- **Determinismo:** mesmos inputs → mesmos outputs (especialmente avatar e normalize)

Cobertura mínima em `app/core/`: **100% das funções públicas**

---

*USI Generator · Core Layer · Talent Development · Usiminas · 2026*