#!/usr/bin/env python3
"""
Flask Secret Key Generator for FacultyFinder
Generates cryptographically secure secret keys for Flask applications
"""

import os
import secrets
import base64
import hashlib
from datetime import datetime

def generate_secret_key_method1():
    """Generate secret key using secrets module (Python 3.6+) - Most Secure"""
    return secrets.token_hex(32)  # 32 bytes = 256 bits

def generate_secret_key_method2():
    """Generate secret key using os.urandom - Very Secure"""
    return base64.b64encode(os.urandom(32)).decode('utf-8')

def generate_secret_key_method3():
    """Generate secret key using secrets.token_urlsafe - URL Safe"""
    return secrets.token_urlsafe(32)

def generate_secret_key_method4():
    """Generate deterministic secret key from system info (Less secure, for consistency)"""
    # WARNING: Only use this if you need the same key across deployments
    # This is less secure than random generation
    import platform
    system_info = f"{platform.node()}-{platform.system()}-facultyfinder"
    return hashlib.sha256(system_info.encode()).hexdigest()

def generate_multiple_keys():
    """Generate multiple secret keys for different purposes"""
    return {
        'main_secret_key': generate_secret_key_method1(),
        'csrf_secret_key': generate_secret_key_method2(),
        'session_key': generate_secret_key_method3(),
        'backup_key': generate_secret_key_method1()
    }

def main():
    print("🔐 Flask Secret Key Generator for FacultyFinder")
    print("=" * 55)
    print()
    
    # Generate primary secret key
    secret_key = generate_secret_key_method1()
    
    print("✅ PRIMARY SECRET KEY (Recommended):")
    print(f"SECRET_KEY={secret_key}")
    print()
    
    # Show alternative methods
    print("🔄 Alternative Generation Methods:")
    print(f"Method 1 (secrets.token_hex):    {generate_secret_key_method1()}")
    print(f"Method 2 (base64 + urandom):     {generate_secret_key_method2()}")
    print(f"Method 3 (URL-safe):             {generate_secret_key_method3()}")
    print()
    
    # Generate multiple keys for different purposes
    keys = generate_multiple_keys()
    print("🔑 Multiple Keys for Different Purposes:")
    for key_name, key_value in keys.items():
        print(f"{key_name.upper()}={key_value}")
    print()
    
    # Show .env format
    print("📝 Add to your .env file:")
    print("-" * 30)
    print(f"SECRET_KEY={secret_key}")
    print(f"CSRF_SECRET_KEY={keys['csrf_secret_key']}")
    print()
    
    # Show Flask config format
    print("🐍 Flask app.config format:")
    print("-" * 25)
    print(f"app.config['SECRET_KEY'] = '{secret_key}'")
    print()
    
    # Security recommendations
    print("🛡️  SECURITY RECOMMENDATIONS:")
    print("1. Use the PRIMARY SECRET KEY above")
    print("2. Keep this key SECRET - never commit to git")
    print("3. Use different keys for development/production")
    print("4. Store in environment variables, not in code")
    print("5. Regenerate if compromised")
    print("6. Key length: minimum 32 characters (256 bits)")
    print()
    
    # Verification
    print("✅ Key Quality Check:")
    print(f"   Length: {len(secret_key)} characters")
    print(f"   Entropy: ~{len(secret_key) * 4} bits")
    print(f"   Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main() 