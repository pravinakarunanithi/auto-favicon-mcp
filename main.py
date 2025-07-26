#!/usr/bin/env python3
"""
MCP FastMCP Server for Automatic Favicon Generation

This server provides tools to generate favicons from PNG images or URLs.
It creates a complete favicon set including various sizes and a manifest.json file.
"""

import asyncio
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import aiohttp
from PIL import Image
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(name="favicon-generator")

FAVICON_SIZES = [16, 32, 48, 64, 128, 256]
ICO_SIZES = [16, 32, 48]
APPLE_SIZES = [180, 152, 144, 120, 114, 76, 72, 60, 57]


def create_favicon_set(image_data: bytes, output_dir: str) -> Dict[str, Any]:
    """Create a complete favicon set from image data."""
    # Write image data to a temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
        temp_file.write(image_data)
        temp_file.flush()
        temp_path = temp_file.name

    try:
        with Image.open(temp_path) as img:
            # Convert to RGBA if needed
            if img.mode != 'RGBA':
                img = img.convert('RGBA')

            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            generated_files = []

            # Generate PNG favicons
            for size in FAVICON_SIZES:
                resized = img.resize((size, size), Image.Resampling.LANCZOS)
                filename = f"favicon-{size}x{size}.png"
                filepath = output_path / filename
                resized.save(filepath, "PNG")
                generated_files.append(str(filepath))

            # Generate ICO file
            ico_images = [img.resize((size, size), Image.Resampling.LANCZOS) for size in ICO_SIZES]
            ico_path = output_path / "favicon.ico"
            ico_images[0].save(ico_path, format='ICO', sizes=[(size, size) for size in ICO_SIZES])
            generated_files.append(str(ico_path))

            # Generate Apple touch icons
            for size in APPLE_SIZES:
                resized = img.resize((size, size), Image.Resampling.LANCZOS)
                filename = f"apple-touch-icon-{size}x{size}.png"
                filepath = output_path / filename
                resized.save(filepath, "PNG")
                generated_files.append(str(filepath))

            # Generate manifest.json
            manifest = {
                "name": "Favicon App",
                "short_name": "Favicon",
                "description": "Generated favicon application",
                "start_url": "/",
                "display": "standalone",
                "background_color": "#ffffff",
                "theme_color": "#000000",
                "icons": [
                    {
                        "src": f"favicon-{size}x{size}.png",
                        "sizes": f"{size}x{size}",
                        "type": "image/png"
                    } for size in FAVICON_SIZES
                ]
            }
            manifest_path = output_path / "manifest.json"
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            generated_files.append(str(manifest_path))

            return {
                "generated_files": generated_files,
                "manifest": manifest,
                "output_directory": str(output_path)
            }
    finally:
        os.unlink(temp_path)


@mcp.tool()
async def generate_favicon_from_png(image_path: str, output_path: str) -> str:
    """
    Generate a complete favicon set from a PNG image file.

    Args:
        image_path: Path to the PNG image file.
        output_path: Directory where favicon files will be generated.
    Returns:
        A message describing the generated files and output directory.
    """
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
        result = create_favicon_set(image_data, output_path)
        return (
            f"Successfully generated favicon set!\n\n"
            f"Output directory: {result['output_directory']}\n"
            f"Generated files:\n" + "\n".join(f"- {f}" for f in result['generated_files'])
        )
    except Exception as e:
        return f"Error generating favicon: {str(e)}"


@mcp.tool()
async def generate_favicon_from_url(image_url: str, output_path: str) -> str:
    """
    Download an image from a URL and generate a complete favicon set.

    Args:
        image_url: URL of the image to download.
        output_path: Directory where favicon files will be generated.
    Returns:
        A message describing the generated files and output directory.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                response.raise_for_status()
                image_data = await response.read()
        result = create_favicon_set(image_data, output_path)
        return (
            f"Successfully downloaded image from {image_url} and generated favicon set!\n\n"
            f"Output directory: {result['output_directory']}\n"
            f"Generated files:\n" + "\n".join(f"- {f}" for f in result['generated_files'])
        )
    except Exception as e:
        return f"Error generating favicon from URL: {str(e)}"

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')