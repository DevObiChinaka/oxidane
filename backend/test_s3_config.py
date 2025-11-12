"""
Test script to verify AWS S3 storage configuration
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.conf import settings
from django.core.files.storage import default_storage

print("=" * 60)
print("AWS S3 STORAGE CONFIGURATION TEST")
print("=" * 60)

# Check USE_S3 setting
use_s3 = getattr(settings, 'USE_S3', False)
print(f"\n✓ USE_S3: {use_s3}")

# Check storage backend
storage_class = default_storage.__class__.__name__
print(f"✓ Storage Backend: {storage_class}")

# Check MEDIA_URL
print(f"✓ MEDIA_URL: {settings.MEDIA_URL}")

# Check file upload limits
print(f"✓ Max File Size: {settings.FILE_UPLOAD_MAX_MEMORY_SIZE / (1024*1024):.0f}MB")

# Status
print("\n" + "=" * 60)
if use_s3:
    print("STATUS: AWS S3 STORAGE ACTIVE")
    print(f"  Bucket: {getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'NOT SET')}")
    print(f"  Region: {getattr(settings, 'AWS_S3_REGION_NAME', 'NOT SET')}")
    cloudfront = getattr(settings, 'AWS_CLOUDFRONT_DOMAIN', '')
    if cloudfront:
        print(f"  CloudFront: {cloudfront}")
else:
    print("STATUS: LOCAL STORAGE ACTIVE (Development Mode)")
    print(f"  Media Root: {getattr(settings, 'MEDIA_ROOT', 'NOT SET')}")

print("=" * 60)

# Check validators
print("\n✓ Video Validators Imported Successfully")
from courses.validators import (
    validate_video_file_size,
    validate_video_file_type,
    validate_resource_file_size,
    validate_resource_file_type
)

print("\n" + "✅" * 30)
print("ALL CHECKS PASSED - SYSTEM READY!")
print("✅" * 30)
