# PWA Icons for FacultyFinder

This directory contains the Progressive Web App (PWA) icons for FacultyFinder.

## 📱 Required Icon Sizes

The following icon sizes are needed for full PWA support:

### Android Chrome
- `icon-72x72.png`
- `icon-96x96.png`
- `icon-128x128.png`
- `icon-144x144.png`
- `icon-192x192.png`
- `icon-384x384.png`
- `icon-512x512.png`

### iOS Safari
- `icon-152x152.png`
- `icon-180x180.png`

### Windows
- `icon-70x70.png`
- `icon-150x150.png`
- `icon-310x310.png`
- `icon-310x150.png` (wide tile)

### App Shortcuts
- `shortcut-search.png` (192x192)
- `shortcut-ai.png` (192x192)
- `shortcut-university.png` (192x192)

## 🛠️ How to Generate Icons

### Option 1: Use the provided script (recommended)
```bash
# Install Pillow
pip install Pillow

# Run the icon generator
python3 create_pwa_icons.py
```

### Option 2: Manual creation
1. Create a 512x512 base logo
2. Use an online PWA icon generator like:
   - https://www.pwabuilder.com/imageGenerator
   - https://app-manifest.firebaseapp.com/
3. Place all generated icons in this directory

### Option 3: Use existing favicon
If you have a `favicon.ico` or logo, you can:
1. Convert it to PNG format
2. Resize to all required dimensions
3. Ensure consistent branding across all sizes

## 🎨 Design Guidelines

- **Theme Color**: #0066cc (FacultyFinder blue)
- **Background**: White (#ffffff) or transparent
- **Style**: Clean, professional, academic
- **Logo**: Should be recognizable at small sizes (72x72)

## ✅ Current Status

After running `create_pwa_icons.py`, you should have all required icons for:
- ✅ Safari "Add to Home Screen" (iOS)
- ✅ Chrome "Install App" (Android)
- ✅ Edge/Windows "Pin to Start"
- ✅ App shortcuts and quick actions

## 🔍 Testing

To test PWA installation:

### iOS Safari
1. Open https://facultyfinder.io in Safari
2. Tap the Share button
3. Look for "Add to Home Screen"
4. The app icon should appear correctly

### Android Chrome
1. Open https://facultyfinder.io in Chrome
2. Look for the install prompt or tap the menu
3. Select "Install app" or "Add to Home screen"
4. The app should install with the correct icon

### Desktop
1. Open https://facultyfinder.io in Chrome/Edge
2. Look for the install icon in the address bar
3. Click to install as a desktop app 