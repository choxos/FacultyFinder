#!/usr/bin/env python3
"""
PWA Icon Generator for FacultyFinder
Creates all required PWA icons from a source image
"""

import os
from PIL import Image, ImageDraw, ImageFont
import sys

def create_text_icon(text, size, bg_color="#0066cc", text_color="white", font_size=None):
    """Create an icon with text (fallback if no logo available)"""
    # Create image
    img = Image.new('RGB', (size, size), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Calculate font size if not provided
    if font_size is None:
        font_size = int(size * 0.4)
    
    try:
        # Try to use a system font
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
    except:
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
    
    # Get text size
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Center text
    x = (size - text_width) // 2
    y = (size - text_height) // 2
    
    # Draw text
    draw.text((x, y), text, fill=text_color, font=font)
    
    return img

def create_pwa_icons():
    """Create all PWA icons"""
    # Create icons directory
    icons_dir = "webapp/static/icons"
    os.makedirs(icons_dir, exist_ok=True)
    
    # Icon sizes needed for PWA
    sizes = [
        (72, 72),       # Android Chrome
        (96, 96),       # Android Chrome
        (128, 128),     # Android Chrome
        (144, 144),     # Android Chrome
        (152, 152),     # iOS
        (180, 180),     # iOS
        (192, 192),     # Android Chrome
        (384, 384),     # Android Chrome
        (512, 512),     # Android Chrome
        (70, 70),       # Windows
        (150, 150),     # Windows
        (310, 310),     # Windows
        (310, 150),     # Windows Wide
    ]
    
    # Check if source logo exists
    source_logo = "logo.png"  # You can replace this with your actual logo
    
    if os.path.exists(source_logo):
        print(f"📱 Using source logo: {source_logo}")
        source_img = Image.open(source_logo)
        
        for width, height in sizes:
            # Resize maintaining aspect ratio
            img = source_img.resize((width, height), Image.Resampling.LANCZOS)
            
            # Add background if image has transparency
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, '#0066cc')
                background.paste(img, mask=img.split()[-1])
                img = background
            
            # Save icon
            if width == 310 and height == 150:
                filename = f"icon-{width}x{height}.png"
            else:
                filename = f"icon-{width}x{height}.png"
            
            filepath = os.path.join(icons_dir, filename)
            img.save(filepath, 'PNG', quality=95)
            print(f"✅ Created: {filename}")
    
    else:
        print("📱 No source logo found, creating text-based icons")
        
        for width, height in sizes:
            if width == 310 and height == 150:
                # Wide tile - use full text
                img = create_text_icon("FacultyFinder", height, font_size=int(height * 0.25))
            else:
                # Square tiles - use abbreviation
                img = create_text_icon("FF", width)
            
            # Save icon
            if width == 310 and height == 150:
                filename = f"icon-{width}x{height}.png"
            else:
                filename = f"icon-{width}x{width}.png"
            
            filepath = os.path.join(icons_dir, filename)
            img.save(filepath, 'PNG', quality=95)
            print(f"✅ Created: {filename}")
    
    # Create shortcut icons
    shortcut_icons = [
        ("shortcut-search.png", "🔍"),
        ("shortcut-ai.png", "🤖"),
        ("shortcut-university.png", "🏛️"),
    ]
    
    for filename, emoji in shortcut_icons:
        # Create 192x192 shortcut icon
        img = create_text_icon(emoji, 192, font_size=120)
        filepath = os.path.join(icons_dir, filename)
        img.save(filepath, 'PNG', quality=95)
        print(f"✅ Created shortcut: {filename}")
    
    print(f"\n🎉 PWA icons created successfully in {icons_dir}/")
    print("\n📱 Your app will now support:")
    print("   • Add to Home Screen (iOS Safari)")
    print("   • Install as PWA (Android Chrome)")
    print("   • Pin to Start (Windows)")
    print("   • App shortcuts with quick actions")

def main():
    print("🚀 FacultyFinder PWA Icon Generator")
    print("=" * 50)
    
    try:
        create_pwa_icons()
    except Exception as e:
        print(f"❌ Error creating icons: {e}")
        print("\n💡 Make sure you have Pillow installed:")
        print("   pip install Pillow")
        return False
    
    return True

if __name__ == "__main__":
    main() 