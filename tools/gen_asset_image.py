#!/usr/bin/env python3
# =============================================================================
# gen_asset_image.py  —  sprite generator + cruncher
#
# Quick README
# -----------------------------------------------------------------------------
# What it does
#   • Generates a square transparent PNG via OpenAI (default model: gpt-image-1)
#   • Saves original to ./unshrunk_sprites/<name>.png
#   • Downscales (nearest-neighbor) to pixel-crunchy sprites (e.g., 32, 16)
#   • Optional palette quantization to a .hex palette (nearest-color mapping)
#   • Optional “inspiration” images to steer style/ideas (not base images)
#   • Reprocess-all mode to redo downscaling/quantization for all originals
#
# Install (once)
#   uv add openai pillow python-dotenv
#
# .env
#   OPENAI_API_KEY=sk-...
#   (also accepts: openaikey)
#
# Usage
#   # Generate + crunch (single size), with palette mapping:
#   uv run tools/gen_asset_image.py generate hero "hero character" \
#       "bold silhouette; idle stance; readable at 16px" --out-size 16 --palette cc-29
#
#   # Re-crunch everything in unshrunk_sprites/ (wipes sprites/ first):
#   uv run tools/gen_asset_image.py reprocess-all --out-size 16 --palette cc-29
#
# Output paths
#   Originals: ./unshrunk_sprites/<name>.png
#   Sprites:   ./sprites/<name>[_pal-<palette>][_<size>].png
#     - If multiple sizes are requested, each size gets its own suffix.
#     - If a palette is used, filenames include _pal-<palette>.
#
# Notes
#   • Scaling is nearest-neighbor only (pixely & crunchy).
#   • Images are padded to square (centered) before resizing.
#   • Palette file format: one hex color per line (RRGGBB or RRGGBBAA).
#   • Default palette dir is ./palettes; also checks ./palletes (typo-friendly).
#   • Transparent background is requested when using gpt-image-1.
#     If a permission error occurs, the script will auto-fallback to dall-e-3
#     (without transparency param) and continue.
#   • Agents should not use the inspire feature yet.
# =============================================================================

import argparse
import base64
import os
import sys
from contextlib import ExitStack
from io import BytesIO
from pathlib import Path
from urllib.request import urlopen

import openai  # for exception classes
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image

# --- Config you can tweak -----------------------------------------------------

BASE_PROMPT = (
    "Top-down pixel-art sprite of {thing}. Style: retro, crisp 1px lines, bold silhouette, "
    "limited palette (<=8 colors), centered, square composition, no text, no background. "
    "Extra details: {description}"
)

DEFAULT_MODEL = "gpt-image-1"  # Transparent PNG supported with `background="transparent"`
DEFAULT_ORIG_SIZE = 1024  # API request size (square)
DEFAULT_OUT_SIZE = 32  # default crunchy size
DEFAULT_TRANSPARENT = True  # request transparent BG on supported models

UNSHRUNK_DIR = Path("unshrunk_sprites")
SPRITES_DIR = Path("sprites")
DEFAULT_PALETTE_DIR = Path("palettes")  # will also try ./palletes as fallback

# -----------------------------------------------------------------------------


def load_api_key() -> str:
    load_dotenv()
    key = os.getenv("OPENAI_API_KEY") or os.getenv("openaikey")
    if not key:
        print("Error: OPENAI_API_KEY (or openaikey) not found in env/.env", file=sys.stderr)
        sys.exit(2)
    return key


def ensure_dirs():
    UNSHRUNK_DIR.mkdir(parents=True, exist_ok=True)
    SPRITES_DIR.mkdir(parents=True, exist_ok=True)


def sanitize_filename(name: str) -> str:
    safe = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in name.strip())
    return safe or "sprite"


def center_pad_to_square(img: Image.Image, fill=(0, 0, 0, 0)) -> Image.Image:
    w, h = img.size
    if w == h:
        return img
    side = max(w, h)
    canvas = Image.new("RGBA", (side, side), fill)
    x = (side - w) // 2
    y = (side - h) // 2
    canvas.paste(img, (x, y))
    return canvas


def crunch_to_size(img: Image.Image, size: int) -> Image.Image:
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    img_sq = center_pad_to_square(img)
    return img_sq.resize((size, size), Image.NEAREST)


# ---------- Palette handling --------------------------------------------------


def _parse_hex_color(s: str) -> tuple[int, int, int, int] | None:
    s = s.strip().lstrip("#")
    if not s:
        return None
    if len(s) == 6:
        r = int(s[0:2], 16)
        g = int(s[2:4], 16)
        b = int(s[4:6], 16)
        a = 255
    elif len(s) == 8:
        r = int(s[0:2], 16)
        g = int(s[2:4], 16)
        b = int(s[4:6], 16)
        a = int(s[6:8], 16)
    else:
        return None
    return (r, g, b, a)


def _find_palette_file(name: str, palette_dir: Path) -> Path:
    p = palette_dir / f"{name}.hex"
    if p.exists():
        return p
    if palette_dir.name != "palletes":
        alt = Path("palletes") / f"{name}.hex"
        if alt.exists():
            return alt
    return p  # return default path (even if missing)


def load_palette(name: str, palette_dir: Path) -> list[tuple[int, int, int, int]]:
    pf = _find_palette_file(name, palette_dir)
    if not pf.exists():
        print(f"Error: palette file not found: {pf}", file=sys.stderr)
        sys.exit(3)
    colors: list[tuple[int, int, int, int]] = []
    for line in pf.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("//") or line.startswith(";"):
            continue
        c = _parse_hex_color(line)
        if c:
            colors.append(c)
    if not colors:
        print(f"Error: no colors parsed in palette {pf}", file=sys.stderr)
        sys.exit(3)
    return colors


def apply_palette_nearest(
    img: Image.Image, palette: list[tuple[int, int, int, int]]
) -> Image.Image:
    """Quantize by nearest RGB color in the palette; preserve source alpha."""
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    px = img.load()
    w, h = img.size

    cache: dict[tuple[int, int, int], tuple[int, int, int, int]] = {}
    pal_rgb = [(r, g, b) for (r, g, b, _a) in palette]

    def nearest_color(rgb: tuple[int, int, int]) -> tuple[int, int, int, int]:
        if rgb in cache:
            return cache[rgb]
        rr, gg, bb = rgb
        best_idx = 0
        best_d = 1e18
        for i, (pr, pg, pb) in enumerate(pal_rgb):
            dr = rr - pr
            dg = gg - pg
            db = bb - pb
            d = dr * dr + dg * dg + db * db
            if d < best_d:
                best_d = d
                best_idx = i
        pr, pg, pb, pa = palette[best_idx]
        cache[rgb] = (pr, pg, pb, pa)
        return cache[rgb]

    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            nr, ng, nb, na = nearest_color((r, g, b))
            px[x, y] = (nr, ng, nb, a if na == 255 else min(a, na))
    return img


# ---------- IO helpers --------------------------------------------------------


def save_sprite(img: Image.Image, out_path: Path, force: bool):
    if out_path.exists() and not force:
        print(f"Skip (exists): {out_path}")
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="PNG", optimize=True)


def _sprite_out_path(base_name: str) -> Path:
    # Clean naming: always sprites/<name>.png
    return SPRITES_DIR / f"{base_name}.png"


# ---------- OpenAI calls ------------------------------------------------------


def _client() -> OpenAI:
    return OpenAI(api_key=load_api_key())


def _decode_to_image_b64(b64: str) -> Image.Image:
    raw = base64.b64decode(b64)
    img = Image.open(BytesIO(raw)).convert("RGBA")
    return center_pad_to_square(img)


def _result_to_image(result) -> Image.Image:
    # OpenAI Images API returns either b64_json or url per item
    item = result.data[0]
    b64 = getattr(item, "b64_json", None)
    if b64:
        return _decode_to_image_b64(b64)
    url = getattr(item, "url", None)
    if url:
        with urlopen(url) as resp:
            raw = resp.read()
        img = Image.open(BytesIO(raw)).convert("RGBA")
        return center_pad_to_square(img)
    raise RuntimeError("Image generation returned neither b64_json nor url.")


def _images_generate(client: OpenAI, *, model: str, prompt: str, size_str: str, transparent: bool):
    kwargs = {
        "model": model,
        "prompt": prompt,
        "size": size_str,
        "output_format": "png",
    }
    if transparent:
        kwargs["background"] = "transparent"  # only honored on gpt-image-1
    return client.images.generate(**kwargs)


def _images_edit_with_inspo(
    client: OpenAI,
    *,
    model: str,
    prompt: str,
    size_str: str,
    transparent: bool,
    inspire_paths: list[str],
):
    with ExitStack() as stack:
        files = [stack.enter_context(open(p, "rb")) for p in inspire_paths]
        kwargs = {
            "model": model,
            "image": files,  # up to 10
            "prompt": prompt,
            "size": size_str,
            "output_format": "png",
        }
        if transparent:
            kwargs["background"] = "transparent"
        return client.images.edit(**kwargs)


def generate_original_via_openai(
    file_name: str,
    thing: str,
    description: str,
    model: str,
    orig_px: int,
    transparent: bool,
    force: bool,
    enable_fallback: bool = False,
    inspire_paths: list[str] | None = None,
) -> Path:
    """
    Call OpenAI to create the original PNG; returns saved path.
    Uses images.generate() by default; switches to images.edit() if inspiration files are provided.
    Falls back to DALL·E 3 if gpt-image-1 is blocked by permissions.
    """
    client = _client()

    prompt = BASE_PROMPT.format(thing=thing, description=description or "")
    size_str = f"{orig_px}x{orig_px}"

    ensure_dirs()
    orig_path = UNSHRUNK_DIR / f"{file_name}.png"
    if orig_path.exists() and not force:
        print(f"Original exists (use --force to overwrite): {orig_path}")
        return orig_path

    print(f"[OpenAI] {('EDIT' if inspire_paths else 'GENERATE')} {size_str} {model} for: {thing!r}")

    try:
        if inspire_paths:
            result = _images_edit_with_inspo(
                client,
                model=model,
                prompt=prompt,
                size_str=size_str,
                transparent=transparent,
                inspire_paths=inspire_paths[:10],
            )
        else:
            result = _images_generate(
                client, model=model, prompt=prompt, size_str=size_str, transparent=transparent
            )
    except openai.PermissionDeniedError:
        # Common case: org not verified / model restricted → fallback to DALL·E 3
        if model == "gpt-image-1":
            if not enable_fallback:
                print("[ERROR] Permission denied for gpt-image-1 and fallback disabled.")
                raise
            print(
                "[WARN] Permission denied for gpt-image-1. Falling back to dall-e-3 (no transparency param)."
            )
            try:
                if inspire_paths:
                    result = _images_edit_with_inspo(
                        client,
                        model="dall-e-3",
                        prompt=prompt,
                        size_str=size_str,
                        transparent=False,
                        inspire_paths=inspire_paths[:10],
                    )
                else:
                    result = _images_generate(
                        client,
                        model="dall-e-3",
                        prompt=prompt,
                        size_str=size_str,
                        transparent=False,
                    )
            except openai.BadRequestError as e:
                # DALL·E 3 may not accept output_format/background
                msg = str(e).lower()
                print(f"[WARN] DALL·E 3 request rejected: {msg}")
                # Retry with minimal params
                if inspire_paths:
                    with ExitStack() as stack:
                        files = [stack.enter_context(open(p, "rb")) for p in inspire_paths[:10]]
                        kwargs = {
                            "model": "dall-e-3",
                            "image": files,
                            "prompt": prompt,
                            "size": size_str,
                        }
                        result = client.images.edit(**kwargs)
                else:
                    kwargs = {"model": "dall-e-3", "prompt": prompt, "size": size_str}
                    result = client.images.generate(**kwargs)
        else:
            raise
    except openai.BadRequestError as e:
        # Some models may reject unknown params
        msg = str(e).lower()
        if "background" in msg or "unknown parameter: 'background'" in msg:
            print("[WARN] Removing unsupported 'background' parameter and retrying...")
            if inspire_paths:
                # Retry edit without background
                with ExitStack() as stack:
                    files = [stack.enter_context(open(p, "rb")) for p in inspire_paths[:10]]
                    kwargs = {
                        "model": model,
                        "image": files,
                        "prompt": prompt,
                        "size": size_str,
                        "output_format": "png",
                    }
                    result = client.images.edit(**kwargs)
            else:
                # Retry generate without background
                kwargs = {"model": model, "prompt": prompt, "size": size_str, "output_format": "png"}
                result = client.images.generate(**kwargs)
        elif "output_format" in msg or "unknown parameter: 'output_format'" in msg:
            print("[WARN] Removing unsupported 'output_format' and retrying (model default)...")
            if inspire_paths:
                with ExitStack() as stack:
                    files = [stack.enter_context(open(p, "rb")) for p in inspire_paths[:10]]
                    kwargs = {
                        "model": model,
                        "image": files,
                        "prompt": prompt,
                        "size": size_str,
                    }
                    if transparent:
                        kwargs["background"] = "transparent"
                    result = client.images.edit(**kwargs)
            else:
                kwargs = {"model": model, "prompt": prompt, "size": size_str}
                if transparent:
                    kwargs["background"] = "transparent"
                result = client.images.generate(**kwargs)
        else:
            raise

    img = _result_to_image(result)
    img.save(orig_path, format="PNG")
    print(f"[OK] Saved original: {orig_path}")
    return orig_path


# ---------- Crunch pipeline ---------------------------------------------------


def do_crunch(
    file_name: str,
    out_size: int,
    force: bool,
    palette_name: str | None,
    palette_dir: Path,
):
    orig_path = UNSHRUNK_DIR / f"{file_name}.png"
    if not orig_path.exists():
        print(f"Missing original: {orig_path}", file=sys.stderr)
        return

    img = Image.open(orig_path).convert("RGBA")
    palette = load_palette(palette_name, palette_dir) if palette_name else None

    out_path = _sprite_out_path(file_name)
    spr = crunch_to_size(img, out_size)
    if palette:
        spr = apply_palette_nearest(spr, palette)
    save_sprite(spr, out_path, force)
    print(f"[OK] Wrote: {out_path}")


# ---------- CLI commands ------------------------------------------------------


def cmd_generate(args):
    fname = sanitize_filename(args.file_name)
    ensure_dirs()
    # Normalize inspiration paths if provided
    inspire = [str(Path(p)) for p in (args.inspire or [])]
    generate_original_via_openai(
        file_name=fname,
        thing=args.thing,
        description=args.description or "",
        model=args.model,
        orig_px=args.orig_size,
        transparent=(not args.no_transparent),
        force=args.force,
        enable_fallback=args.enable_fallback,
        inspire_paths=inspire if inspire else None,
    )
    do_crunch(
        fname,
        args.out_size,
        args.force,
        palette_name=args.palette,
        palette_dir=Path(args.palette_dir),
    )


def cmd_reprocess_all(args):
    ensure_dirs()
    # Wipe sprites/ folder for a clean re-output at a single size
    try:
        if SPRITES_DIR.exists() and SPRITES_DIR.is_dir():
            for p in SPRITES_DIR.iterdir():
                try:
                    if p.is_file() or p.is_symlink():
                        p.unlink(missing_ok=True)
                    elif p.is_dir():
                        import shutil

                        shutil.rmtree(p)
                except Exception as e:  # best-effort wipe
                    print(f"[WARN] Could not remove {p}: {e}")
    except Exception as e:
        print(f"[WARN] Could not wipe sprites dir: {e}")
    pngs = sorted(UNSHRUNK_DIR.glob("*.png"))
    if not pngs:
        print(f"No originals in {UNSHRUNK_DIR}/")
        return
    for p in pngs:
        fname = p.stem
        print(f"[Reprocess] {fname}")
        do_crunch(
            fname,
            args.out_size,
            args.force,
            palette_name=args.palette,
            palette_dir=Path(args.palette_dir),
        )


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Generate and crunch sprite assets.")
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("generate", help="Generate a new sprite via OpenAI, then crunch.")
    g.add_argument("file_name", help="Output base name (no extension).")
    g.add_argument("thing", help="Main subject to fill into base prompt.")
    g.add_argument("description", nargs="?", default="", help="Extra details/constraints.")
    g.add_argument(
        "--model", default=DEFAULT_MODEL, help="OpenAI image model (default: gpt-image-1)."
    )
    g.add_argument(
        "--orig-size",
        type=int,
        default=DEFAULT_ORIG_SIZE,
        help="Original square px (default: 1024).",
    )
    g.add_argument("--out-size", type=int, default=DEFAULT_OUT_SIZE, help="Output sprite size (px).")
    g.add_argument("--no-transparent", action="store_true", help="Do NOT request transparent bg.")
    g.add_argument("--force", action="store_true", help="Overwrite existing files if present.")
    g.add_argument(
        "--enable-fallback",
        action="store_true",
        help="Allow fallback to alternative model (e.g., dall-e-3) when blocked.",
    )
    g.add_argument("--palette", help="Palette name (file <palette-dir>/<name>.hex).")
    g.add_argument(
        "--palette-dir",
        default=str(DEFAULT_PALETTE_DIR),
        help="Directory containing *.hex palettes (default: ./palettes; also checks ./palletes).",
    )
    g.add_argument("--inspire", nargs="+", help="Optional inspiration images (max 10).")
    g.set_defaults(func=cmd_generate)

    r = sub.add_parser("reprocess-all", help="Re-crunch every PNG in unshrunk_sprites/ (wipes sprites/)")
    r.add_argument("--out-size", type=int, default=DEFAULT_OUT_SIZE)
    r.add_argument("--force", action="store_true")
    r.add_argument("--palette", help="Palette name (file <palette-dir>/<name>.hex).")
    r.add_argument(
        "--palette-dir",
        default=str(DEFAULT_PALETTE_DIR),
        help="Directory containing *.hex palettes (default: ./palettes; also checks ./palletes).",
    )
    r.set_defaults(func=cmd_reprocess_all)

    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
