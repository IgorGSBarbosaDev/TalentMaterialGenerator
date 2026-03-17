from __future__ import annotations

from pathlib import Path

from PIL import Image

from app.core.image_utils import (
    generate_avatar,
    make_circular_image,
    resize_image,
    save_temp_png,
)


def _fixture_image_path() -> Path:
    return (
        Path(__file__).resolve().parents[2] / "fixtures" / "fotos" / "avatar_test.png"
    )


def test_make_circular_image_returns_rgba_image_for_valid_path() -> None:
    image_path = _fixture_image_path()

    result = make_circular_image(str(image_path))

    assert result is not None
    assert result.mode == "RGBA"


def test_make_circular_image_returns_none_for_invalid_path() -> None:
    result = make_circular_image("tests/fixtures/fotos/does_not_exist.png")

    assert result is None


def test_make_circular_image_returns_none_for_non_image_file(tmp_path: Path) -> None:
    non_image_path = tmp_path / "file.txt"
    non_image_path.write_text("not an image", encoding="utf-8")

    result = make_circular_image(str(non_image_path))

    assert result is None


def test_make_circular_image_returns_none_for_unexpected_exception(monkeypatch) -> None:
    def _raise_runtime_error(*args, **kwargs):
        raise RuntimeError("unexpected failure")

    monkeypatch.setattr("app.core.image_utils.Image.open", _raise_runtime_error)

    result = make_circular_image("tests/fixtures/fotos/avatar_test.png")

    assert result is None


def test_make_circular_image_preserves_alpha_channel(tmp_path: Path) -> None:
    image_path = tmp_path / "rgba_input.png"
    source = Image.new("RGBA", (10, 10), (120, 140, 160, 64))
    source.save(image_path)

    result = make_circular_image(str(image_path))

    assert result is not None
    assert result.mode == "RGBA"
    assert result.getpixel((5, 5))[3] == 64


def test_generate_avatar_returns_rgba_image() -> None:
    result = generate_avatar("Ana Martins")

    assert result.mode == "RGBA"


def test_generate_avatar_is_deterministic_for_same_name() -> None:
    first = generate_avatar("Ana Martins")
    second = generate_avatar("Ana Martins")
    center = (first.width // 2, first.height // 2)

    assert first.getpixel(center) == second.getpixel(center)


def test_generate_avatar_produces_different_colors_for_different_names() -> None:
    first = generate_avatar("Ana Martins")
    second = generate_avatar("Pedro Souza")
    center = (first.width // 2, first.height // 2)

    assert first.getpixel(center) != second.getpixel(center)


def test_generate_avatar_with_empty_string_does_not_raise() -> None:
    result = generate_avatar("")

    assert result.mode == "RGBA"


def test_generate_avatar_contains_initials_as_text() -> None:
    result = generate_avatar("Ana Martins")

    unique_pixels = set(result.getdata())
    assert len(unique_pixels) > 1


def test_generate_avatar_with_single_name_returns_rgba_image() -> None:
    result = generate_avatar("Ana")

    assert result.mode == "RGBA"


def test_resize_image_returns_correct_dimensions() -> None:
    source = Image.new("RGBA", (50, 30), (255, 0, 0, 255))

    result = resize_image(source, 100, 60)

    assert result.size == (100, 60)


def test_save_temp_png_creates_file_on_disk() -> None:
    source = Image.new("RGBA", (20, 20), (0, 0, 0, 255))

    saved_path = save_temp_png(source)

    try:
        assert Path(saved_path).exists()
    finally:
        Path(saved_path).unlink(missing_ok=True)


def test_save_temp_png_file_is_valid_png() -> None:
    source = Image.new("RGBA", (20, 20), (10, 20, 30, 255))

    saved_path = save_temp_png(source)

    try:
        with Image.open(saved_path) as opened:
            opened.verify()
    finally:
        Path(saved_path).unlink(missing_ok=True)
