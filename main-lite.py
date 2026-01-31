import os
import json
import shutil
import time
import base64
import requests
import argparse
import sys
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image

# Load environment variables
load_dotenv()

# Global flag for verbose API output
VERBOSE_API = False

# Load configuration
def load_config(config_path='config.json'):
    """Load configuration from JSON file."""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: {config_path} not found. Using default configuration.")
        return {
            "model": "gemini-2.0-flash-exp",
            "folders": {"input": "input", "output": "output"},
            "supported_formats": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"],
            "processing": {"verbose": True, "show_preview_tags": 5, "max_consecutive_failures": 3, "failure_mode": "retry_every_minute"},
            "output": {"json_indent": 2, "ensure_ascii": False},
            "compression": {
                "enabled": True,
                "quality": 65,
                "max_resolution": [1280, 1280],
                "strip_metadata": True,
                "output_format": "webp"
            }
        }
    except json.JSONDecodeError as e:
        print(f"Error parsing {config_path}: {e}")
        print("Using default configuration.")
        return {
            "model": "gemini-2.0-flash-exp",
            "folders": {"input": "input", "output": "output"},
            "supported_formats": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"],
            "processing": {"verbose": True, "show_preview_tags": 5, "max_consecutive_failures": 3, "failure_mode": "retry_every_minute"},
            "output": {"json_indent": 2, "ensure_ascii": False},
            "compression": {
                "enabled": True,
                "quality": 65,
                "max_resolution": [1280, 1280],
                "strip_metadata": True,
                "output_format": "webp"
            }
        }

CONFIG = load_config()


def process_image(image_path, api_key, model_name):
    """
    Process a single image with Gemini AI REST API to extract tags, text, and metadata.
    
    Args:
        image_path: Path to the image file
        api_key: Google API key
        model_name: Name of the Gemini model to use
        
    Returns:
        dict: Structured metadata dictionary or None if processing fails
    """
    try:
        # Read image bytes and encode to base64
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Determine mime type by detecting actual image format with PIL
        try:
            img = Image.open(image_path)
            format_to_mime = {
                'JPEG': 'image/jpeg',
                'JPG': 'image/jpeg',
                'PNG': 'image/png',
                'GIF': 'image/gif',
                'WEBP': 'image/webp',
                'BMP': 'image/bmp'
            }
            mime_type = format_to_mime.get(img.format, 'image/jpeg')
        except Exception:
            # Fallback to extension-based detection if PIL fails
            ext = Path(image_path).suffix.lower()
            mime_types = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp',
                '.bmp': 'image/bmp'
            }
            mime_type = mime_types.get(ext, 'image/jpeg')
        
        # Load prompt from file
        prompt_path = os.path.join(os.path.dirname(__file__), 'prompt.txt')
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt = f.read().strip()
        except FileNotFoundError:
            print(f"Warning: prompt.txt not found at {prompt_path}")
            return None
        
        # Construct the REST API endpoint
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        
        # Prepare the request payload
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": image_base64
                            }
                        },
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
        }
        
        # Make the API request
        headers = {
            "Content-Type": "application/json"
        }
        
        # Print verbose API output if enabled
        if VERBOSE_API:
            print("\n" + "="*60)
            print("VERBOSE API OUTPUT")
            print("="*60)
            print(f"URL: {api_url}")
            print(f"\nRequest Headers:")
            print(json.dumps(headers, indent=2))
            print(f"\nRequest Payload:")
            # Create a copy of payload for display, truncating base64 data
            display_payload = json.loads(json.dumps(payload))
            if display_payload['contents'][0]['parts'][0]['inline_data']['data']:
                display_payload['contents'][0]['parts'][0]['inline_data']['data'] = f"[BASE64_DATA_{len(image_base64)} chars]"
            print(json.dumps(display_payload, indent=2))
            print("="*60 + "\n")
        
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()
        
        # Parse the response
        response_json = response.json()
        
        # Print verbose API response if enabled
        if VERBOSE_API:
            print("\n" + "="*60)
            print("VERBOSE API RESPONSE")
            print("="*60)
            print(json.dumps(response_json, indent=2))
            print("="*60 + "\n")
        
        # Extract text from response
        if 'candidates' not in response_json or len(response_json['candidates']) == 0:
            print(f"Error: No candidates in response for {image_path}")
            return None
        
        candidate = response_json['candidates'][0]
        if 'content' not in candidate or 'parts' not in candidate['content']:
            print(f"Error: Invalid response structure for {image_path}")
            return None
        
        response_text = candidate['content']['parts'][0].get('text', '').strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        elif response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Parse JSON
        metadata = json.loads(response_text)
        
        # Validate required keys
        required_keys = ['tags', 'raw_text', 'structured_data', 'profile_mentions']
        for key in required_keys:
            if key not in metadata:
                metadata[key] = [] if key in ['tags', 'profile_mentions'] else ({} if key == 'structured_data' else "")
        
        return metadata
        
    except requests.exceptions.RequestException as e:
        error_text = str(e)
        short_error = error_text.split("\n", 1)[0]
        short_error = short_error.split("{", 1)[0].strip()
        print(f"Error processing {image_path}: {short_error}")
        return None
    except Exception as e:
        error_text = str(e)
        short_error = error_text.split("\n", 1)[0]
        short_error = short_error.split("{", 1)[0].strip()
        print(f"Error processing {image_path}: {short_error}")
        return None


# ===== FAILURE CONDITION 1: Stop after N consecutive failures =====
def check_failure_condition_stop_on_consecutive(consecutive_failures, max_consecutive_failures, idx, image_files):
    """
    Check if the failure threshold has been reached and determine if processing should stop.
    Stops processing after N consecutive failures.
    
    Args:
        consecutive_failures: Current count of consecutive failures
        max_consecutive_failures: Maximum allowed consecutive failures
        idx: Current image index (1-based)
        image_files: List of all image files
        
    Returns:
        tuple: (should_stop: bool, consecutive_failures: int)
               - should_stop: True if processing should halt
               - consecutive_failures: Updated failure count (incremented)
    """
    consecutive_failures += 1
    
    if consecutive_failures >= max_consecutive_failures:
        print(f"\n⚠️  Stopping: {consecutive_failures} consecutive failures reached.")
        print(f"Processed {idx - consecutive_failures}/{len(image_files)} images successfully.\n")
        return True, consecutive_failures
    
    return False, consecutive_failures


# ===== FAILURE CONDITION 2: Retry every minute on failure =====
def check_failure_condition_retry_every_minute(consecutive_failures, max_consecutive_failures, idx, image_files):
    """
    Retry failed image processing every minute.
    Keeps retrying the image indefinitely until it succeeds.
    
    Args:
        consecutive_failures: Current count of consecutive failures (unused in this implementation)
        max_consecutive_failures: Retry delay in seconds (default from config)
        idx: Current image index (1-based)
        image_files: List of all image files
        
    Returns:
        tuple: (should_stop: bool, consecutive_failures: int)
               - should_stop: Always False (never stops, keeps retrying)
               - consecutive_failures: 0 (reset counter)
    """
    # Wait before retrying
    retry_delay = max_consecutive_failures if isinstance(max_consecutive_failures, (int, float)) and max_consecutive_failures > 10 else 60
    print(f"    Retrying in {retry_delay} seconds...")
    time.sleep(retry_delay)
    
    return False, consecutive_failures


def reset_failure_counter():
    """
    Reset the consecutive failure counter to 0 after a successful processing.
    
    Returns:
        int: 0 (reset counter)
    """
    return 0


def get_unique_output_basename(output_folder, base_name, image_ext, reserved_basenames=None):
    """
    Generate a unique base name for image + json pair in the output folder.

    Args:
        output_folder: Output directory path
        base_name: Desired base name
        image_ext: Image file extension (e.g., .webp)
        reserved_basenames: Optional set of basenames reserved in this run

    Returns:
        str: Unique base name
    """
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
    """
    Compress an image to WebP and return the output filename.

    Args:
        input_path: Path to the input image
        output_folder: Output directory
        base_name: Desired base name
        compression_settings: Compression config dict
        reserved_basenames: Optional set of basenames reserved in this run

    Returns:
        str: Output filename (e.g., cat.webp)
    """
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

    # WebP requires RGB
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


def categorize_images():
    """
    Process all images in the input folder and move them to output with JSON metadata.
    Uses settings from config.json and API key from .env file.
    Uses REST API directly without Google libraries.
    """
    # Get API key from environment
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("Error: GOOGLE_API_KEY not found in environment variables.")
        print("Please create a .env file with your API key (see .env.example)")
        return
    
    # Get settings from config
    input_folder = CONFIG['folders']['input']
    output_folder = CONFIG['folders']['output']
    model_name = CONFIG['model']
    verbose = CONFIG['processing']['verbose']
    show_preview_tags = CONFIG['processing']['show_preview_tags']
    max_consecutive_failures = CONFIG['processing']['max_consecutive_failures']
    failure_mode = CONFIG['processing'].get('failure_mode', 'retry_every_minute')
    json_indent = CONFIG['output']['json_indent']
    ensure_ascii = CONFIG['output']['ensure_ascii']
    compression_settings = CONFIG.get('compression', {
        "enabled": True,
        "quality": 65,
        "max_resolution": [1280, 1280],
        "strip_metadata": True,
        "output_format": "webp"
    })
    compression_enabled = compression_settings.get('enabled', True)
    reserved_basenames = set()
    
    # Select failure condition function based on config
    if failure_mode == 'stop_on_consecutive':
        check_failure = check_failure_condition_stop_on_consecutive
    elif failure_mode == 'retry_every_minute':
        check_failure = check_failure_condition_retry_every_minute
    else:
        print(f"Unknown failure_mode '{failure_mode}'. Using 'retry_every_minute'.")
        check_failure = check_failure_condition_retry_every_minute
    
    # Track consecutive failures
    consecutive_failures = 0
    
    # Create folders if they don't exist
    os.makedirs(input_folder, exist_ok=True)
    os.makedirs(output_folder, exist_ok=True)
    
    # Supported image extensions from config
    image_extensions = set(CONFIG['supported_formats'])
    
    # Get all image files from input folder
    image_files = [
        f for f in os.listdir(input_folder)
        if Path(f).suffix.lower() in image_extensions
    ]
    
    if not image_files:
        print(f"No images found in '{input_folder}' folder.")
        return
    
    if verbose:
        print(f"Found {len(image_files)} image(s) to process.")
        print(f"Using model: {model_name}")
        print(f"Using REST API directly\n")
    
    # Process each image
    for idx, filename in enumerate(image_files, 1):
        if verbose:
            print(f"[{idx}/{len(image_files)}] Processing: {filename}")
        
        input_path = os.path.join(input_folder, filename)
        
        # Keep retrying until successful
        while True:
            # Process the image with AI using REST API
            metadata = process_image(input_path, api_key, model_name)
            
            if metadata is None:
                print(f"[{idx}/{len(image_files)}]  ❌ Failed to process {filename}.")
                should_stop, consecutive_failures = check_failure(
                    consecutive_failures, max_consecutive_failures, idx, image_files
                )
                # Keep retrying (should_stop only True if stop_on_consecutive mode)
                if should_stop:
                    break
                continue
            
            # Success - break out of retry loop
            break
        
        file_stem = Path(filename).stem

        # Compress image after successful AI processing
        try:
            if compression_enabled:
                output_filename = compress_image_to_webp(
                    input_path,
                    output_folder,
                    file_stem,
                    compression_settings,
                    reserved_basenames
                )
            else:
                output_filename = filename
                unique_base = get_unique_output_basename(output_folder, file_stem, Path(filename).suffix, reserved_basenames)
                output_filename = f"{unique_base}{Path(filename).suffix}"
                shutil.move(input_path, os.path.join(output_folder, output_filename))
        except Exception as e:
            print(f"  ❌ Compression failed for {filename}: {e}")
            # Fallback: move original file with unique name
            unique_base = get_unique_output_basename(output_folder, file_stem, Path(filename).suffix, reserved_basenames)
            output_filename = f"{unique_base}{Path(filename).suffix}"
            shutil.move(input_path, os.path.join(output_folder, output_filename))

        # Ensure input file is removed if compressed (we didn't move it)
        if os.path.exists(input_path) and compression_enabled:
            try:
                os.remove(input_path)
            except Exception:
                pass

        reserved_basenames.add(Path(output_filename).stem)

        # Add filename to the metadata
        final_metadata = {
            'filename': output_filename,
            **metadata
        }

        # Create output paths
        output_json_path = os.path.join(output_folder, f"{Path(output_filename).stem}.json")
        
        try:
            # Save JSON metadata
            with open(output_json_path, 'w', encoding='utf-8') as f:
                json.dump(final_metadata, f, indent=json_indent, ensure_ascii=ensure_ascii)
            
            # Reset failure counter on success
            consecutive_failures = reset_failure_counter()
            
            if verbose:
                print(f"  ✓ Successfully processed!")
                tag_preview = metadata.get('tags', [])[:show_preview_tags]
                print(f"    - Tags: {', '.join(tag_preview)}{'...' if len(metadata.get('tags', [])) > show_preview_tags else ''}")
                print(f"    - Profile mentions: {len(metadata.get('profile_mentions', []))}")
                print(f"    - Saved: {output_filename} + {Path(output_filename).stem}.json\n")
            
        except Exception as e:
            print(f" ❌ Error saving files: {str(e)}\n")
            # Clean up JSON if it was created but image move failed
            if os.path.exists(output_json_path):
                os.remove(output_json_path)
            continue
    
    print("=" * 50)
    print("Processing complete!")
    remaining = len([f for f in os.listdir(input_folder) if Path(f).suffix.lower() in image_extensions])
    if remaining > 0:
        print(f"Note: {remaining} image(s) failed to process and remain in input folder.")


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='AI Image Categorizer - Lite Version')
    parser.add_argument('--verbose-api', action='store_true', help='Show full API request and response details')
    args = parser.parse_args()
    
    # Set global verbose API flag
    VERBOSE_API = args.verbose_api
    
    if CONFIG['processing']['verbose']:
        print("=" * 50)
        print("AI Image Categorizer (Lite Version)")
        print("=" * 50)
        if VERBOSE_API:
            print("🔍 Verbose API output enabled")
        print()
    
    categorize_images()
