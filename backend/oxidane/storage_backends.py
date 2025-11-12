"""
Custom storage backends for AWS S3
Separates static files and media files into different S3 paths
"""
from storages.backends.s3boto3 import S3Boto3Storage


class StaticStorage(S3Boto3Storage):
    """Storage backend for static files (CSS, JS, admin files)"""
    location = 'static'
    default_acl = 'public-read'
    file_overwrite = True


class MediaStorage(S3Boto3Storage):
    """Storage backend for user-uploaded media files (videos, resources)"""
    location = 'media'
    default_acl = 'private'
    file_overwrite = False
    custom_domain = False  # Use CloudFront domain from settings
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set custom domain if CloudFront is configured
        from django.conf import settings
        if hasattr(settings, 'AWS_S3_CUSTOM_DOMAIN'):
            self.custom_domain = settings.AWS_S3_CUSTOM_DOMAIN
