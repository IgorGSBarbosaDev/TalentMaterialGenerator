from __future__ import annotations

import hashlib
import tempfile

from PIL import Image, ImageChops, ImageDraw, ImageFont

AVATAR_SIZE = 256
TEXT_COLOR = (255, 255, 255, 255)


def _extract_initials(name: str) -> str:
    parts = [part for part in name.strip().split() if part]
    if not parts:
        return "?"

    if len(parts) == 1:
        return parts[0][0].upper()

    return f"{parts[0][0]}{parts[-1][0]}".upper()


def _color_from_name(name: str) -> tuple[int, int, int, int]:
    normalized_name = name.strip() or "avatar"
    digest = hashlib.md5(normalized_name.encode("utf-8")).hexdigest()
    red = int(digest[0:2], 16)
    green = int(digest[2:4], 16)
    blue = int(digest[4:6], 16)
    return (red, green, blue, 255)


def _draw_centered_initials(img: Image.Image, initials: str) -> None:
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    text_bbox = draw.textbbox((0, 0), initials, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    text_x = (img.width - text_width) // 2
    text_y = int(img.height * 0.62) - (text_height // 2)
    draw.text((text_x, text_y), initials, fill=TEXT_COLOR, font=font)


def make_circular_image(path: str) -> Image.Image | None:
    try:
        with Image.open(path) as source:
            rgba_image = source.convert("RGBA")

        circle_mask = Image.new("L", rgba_image.size, 0)
        mask_draw = ImageDraw.Draw(circle_mask)
        mask_draw.ellipse((0, 0, rgba_image.width, rgba_image.height), fill=255)

        alpha_channel = rgba_image.getchannel("A")
        combined_alpha = ImageChops.multiply(alpha_channel, circle_mask)
        rgba_image.putalpha(combined_alpha)
        return rgba_image
    except (FileNotFoundError, OSError, ValueError):
        return None
    except Exception:
        return None


def generate_avatar(name: str) -> Image.Image:
    avatar = Image.new("RGBA", (AVATAR_SIZE, AVATAR_SIZE), (0, 0, 0, 0))
    avatar_draw = ImageDraw.Draw(avatar)
    avatar_draw.ellipse(
        (0, 0, AVATAR_SIZE - 1, AVATAR_SIZE - 1), fill=_color_from_name(name)
    )

    initials = _extract_initials(name)
    _draw_centered_initials(avatar, initials)
    return avatar


def resize_image(img: Image.Image, width: int, height: int) -> Image.Image:
    return img.resize((width, height), Image.LANCZOS)


def save_temp_png(img: Image.Image) -> str:
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
        img.save(temp_file.name, format="PNG")
        return temp_file.name
