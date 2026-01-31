"""
Utility: Compress images in the output folder to WebP and update JSON filenames.
Handles name collisions by appending " (1)", " (2)", etc.
"""

import os
import json
from pathlib import Path
from PIL import Image


def load_config(config_path='config.json'):
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {
            "folders": {"output": "output"},
            "supported_formats": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff"],
            "compression": {
                "enabled": True,
                "quality": 65,
                "max_resolution": [1280, 1280],
                "strip_metadata": True,
                "output_format": "webp"
            }
        }


def get_unique_output_basename(output_folder, base_name, image_ext, reserved_basenames=None):
    reserved_basenames = reserved_basenames or set()
    counter = 0
    candidate = base_name

    while True:
        image_path = os.path.join(output_folder, f"{candidate}{image_ext}")
        json_path = os.path.join(output_folder, f"{candidate}.json")
        if candidate not in reserved_basenames and not os.path.exists(image_path) and not os.path.exists(json_path):
            return candidate
        counter += 1
        candidate = f"{base_name} ({counter})"


def compress_image_to_webp(input_path, output_folder, base_name, compression_settings, reserved_basenames=None):
    quality = compression_settings.get("quality", 65)
    max_resolution = compression_settings.get("max_resolution", [1280, 1280])
    strip_metadata = compression_settings.get("strip_metadata", True)
    output_format = compression_settings.get("output_format", "webp").lower()

    if output_format != "webp":
        output_format = "webp"

    output_ext = ".webp"
    unique_base = get_unique_output_basename(output_folder, base_name, output_ext, reserved_basenames)
    output_filename = f"{unique_base}{output_ext}"
    output_path = os.path.join(output_folder, output_filename)

    img = Image.open(input_path)

    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    if max_resolution:
        img.thumbnail(tuple(max_resolution), Image.LANCZOS)

    save_kwargs = {
        "format": "WEBP",
        "quality": quality,
        "method": 6,
        "lossless": False
    }

    if not strip_metadata and "exif" in img.info:
        save_kwargs["exif"] = img.info["exif"]

    img.save(output_path, **save_kwargs)

    return output_filename


def build_json_index(output_folder):
    json_by_filename = {}
    json_by_stem = {}

    for json_file in Path(output_folder).glob('*.json'):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            filename = data.get('filename')
            if filename:
                json_by_filename[filename] = (json_file, data)
            json_by_stem[json_file.stem] = (json_file, data)
        except Exception:
            continue

    return json_by_filename, json_by_stem


def compress_output_folder():
    config = load_config()
    output_folder = config.get('folders', {}).get('output', 'output')
    supported_formats = config.get('supported_formats', [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff"])
    compression_settings = config.get('compression', {})

    os.makedirs(output_folder, exist_ok=True)

    json_by_filename, json_by_stem = build_json_index(output_folder)
    reserved_basenames = set()

    image_files = [
        f for f in os.listdir(output_folder)
        if Path(f).suffix.lower() in set(supported_formats)
    ]

    if not image_files:
        print(f"No images found in '{output_folder}' folder.")
        return

    for filename in sorted(image_files):
        input_path = os.path.join(output_folder, filename)
        base_name = Path(filename).stem
        ext = Path(filename).suffix.lower()

        try:
            # Compress to WebP
            output_filename = compress_image_to_webp(
                input_path,
                output_folder,
                base_name,
                compression_settings,
                reserved_basenames
            )

            output_base = Path(output_filename).stem
            reserved_basenames.add(output_base)

            # Remove original if different
            if output_filename != filename and os.path.exists(input_path):
                os.remove(input_path)

            # Update JSON metadata
            json_entry = json_by_filename.get(filename) or json_by_stem.get(base_name)
            if json_entry:
                json_path, data = json_entry
                data['filename'] = output_filename
                new_json_path = os.path.join(output_folder, f"{output_base}.json")
                with open(new_json_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                if Path(json_path) != Path(new_json_path) and os.path.exists(json_path):
                    os.remove(json_path)

            print(f"{filename} → {output_filename}")

        except Exception as e:
            print(f"Skipping {filename}: {e}")


if __name__ == "__main__":
    compress_output_folder()
