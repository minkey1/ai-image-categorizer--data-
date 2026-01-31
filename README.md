# AI Image Categorizer

An intelligent image categorization system that uses Google's Gemini AI to analyze images, extract metadata, generate tags, and identify profile mentions.

## Features

- **Smart Tagging**: Automatically generates descriptive one-word tags based on image content, visible objects, text, and context
- **Text Extraction**: Extracts all readable text from images
- **Structured Data**: Intelligently organizes metadata (e.g., profile information from social media screenshots)
- **Profile Mentions**: Detects and lists all @ mentions in images
- **Batch Processing**: Processes all images in the input folder
- **Safe Operations**: Only moves files to output when processing is successful

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure API key:
   - Copy `.env.example` to `.env`
   - Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Add your API key to `.env`:
     ```
     GOOGLE_API_KEY=your_actual_api_key_here
     ```

3. (Optional) Customize settings in `config.json`:
   - `model`: Gemini model to use (default: "gemini-2.0-flash-exp")
   - `folders`: Input/output folder names
   - `supported_formats`: List of image file extensions to process
   - `processing.verbose`: Show detailed progress (true/false)
   - `processing.show_preview_tags`: Number of tags to show in preview
   - `output.json_indent`: JSON formatting indent size
   - `output.ensure_ascii`: Whether to escape non-ASCII characters in JSON

## Usage

1. Place your images in the `input` folder
2. Run the script:
```bash
python main.py
```

3. Processed images and their JSON metadata will be moved to the `output` folder

## Output Format

For each image (e.g., `my_pic.png`), the system generates:
- `my_pic.png` - The original image
- `my_pic.json` - Metadata file with structure:

```json
{
  "filename": "my_pic.png",
  "tags": ["instagram", "profile", "selfie", "dog", "finance"],
  "raw_text": "All text extracted from the image...",
  "structured_data": {
    "name": "John Doe",
    "username": "@johndoe",
    "bio": "Finance enthusiast | Dog lover",
    "followers": "1.2K"
  },
  "profile_mentions": ["@raghav", "@johnny"],
  "additional_metadata": {
    "hashtags": ["#finance", "#dogs"],
    "urls": ["example.com"]
  }
}
```

## Supported Image Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)
- WebP (.webp)
- BMP (.bmp)

## Web Frontend

View and filter your categorized images with the included web interface:

1. Start the web server:
```bash
python server.py
```

2. Open your browser to `http://localhost:8000`

**Features:**
- Browse all processed images in a gallery view
- Filter images by tags (click tags to filter)
- Search through raw text and metadata
- View full details in a modal when clicking images
- Customizable filter logic in `frontend/filter.js`

## Notes

- The AI analyzes all aspects of the image including visible content, text, and context
- Tags are generated based on comprehensive analysis of the entire image
- Failed processing leaves images in the input folder for retry
- Filter logic can be customized by editing `frontend/filter.js`
