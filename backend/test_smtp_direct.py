#!/usr/bin/env python
"""Test SMTP connection directly to diagnose timeout issues."""
import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from subscriptions.models import EmailConfiguration
import smtplib
import socket

def test_smtp():
    config = EmailConfiguration.get_instance()
    password = config.decrypt_field('smtp_password') if config.smtp_password else ''
    
    print("=" * 60)
    print("SMTP CONFIGURATION TEST")
    print("=" * 60)
    print(f"Host: {config.smtp_host}")
    print(f"Port: {config.smtp_port}")
    print(f"Username: {config.smtp_username}")
    print(f"Password length: {len(password)} chars")
    print(f"Use TLS: {config.use_tls}")
    print(f"Use SSL: {config.use_ssl}")
    print(f"From Email: {config.from_email}")
    print("=" * 60)
    
    # Test 1: Check DNS resolution
    print("\n[1/4] Testing DNS resolution...")
    try:
        ip = socket.gethostbyname(config.smtp_host)
        print(f"✓ DNS OK: {config.smtp_host} resolves to {ip}")
    except Exception as e:
        print(f"✗ DNS FAILED: {e}")
        return
    
    # Test 2: Check port connectivity
    print("\n[2/4] Testing port connectivity...")
    try:
        sock = socket.create_connection((config.smtp_host, config.smtp_port), timeout=10)
        sock.close()
        print(f"✓ PORT OK: Can connect to {config.smtp_host}:{config.smtp_port}")
    except Exception as e:
        print(f"✗ PORT FAILED: {e}")
        print("\nPossible causes:")
        print("  - Firewall blocking port 587")
        print("  - Network restrictions")
        print("  - ISP blocking SMTP ports")
        return
    
    # Test 3: SMTP connection and STARTTLS
    print("\n[3/4] Testing SMTP connection and TLS...")
    try:
        server = smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=10)
        server.ehlo()
        print(f"✓ SMTP OK: Connected to server")
        
        if config.use_tls:
            server.starttls()
            server.ehlo()
            print(f"✓ TLS OK: TLS handshake successful")
    except Exception as e:
        print(f"✗ SMTP/TLS FAILED: {e}")
        server.quit()
        return
    
    # Test 4: Authentication
    print("\n[4/4] Testing authentication...")
    try:
        server.login(config.smtp_username, password)
        print(f"✓ AUTH OK: Successfully authenticated as {config.smtp_username}")
        server.quit()
        print("\n" + "=" * 60)
        print("SUCCESS: All tests passed! ✓")
        print("=" * 60)
    except smtplib.SMTPAuthenticationError as e:
        print(f"✗ AUTH FAILED: {e}")
        print("\nPossible causes:")
        print("  - Incorrect App Password")
        print("  - App Password not generated correctly")
        print("  - 2FA not enabled on Google account")
        server.quit()
    except Exception as e:
        print(f"✗ AUTH FAILED: {e}")
        server.quit()

if __name__ == '__main__':
    test_smtp()
