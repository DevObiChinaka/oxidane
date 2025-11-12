"""
File validators for course content uploads
"""
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile


def validate_video_file_size(file: UploadedFile):
    """
    Validate video file size (max 500MB)
    """
    max_size = 500 * 1024 * 1024  # 500MB in bytes
    
    if file.size > max_size:
        size_mb = file.size / (1024 * 1024)
        raise ValidationError(
            f'Video file too large. Maximum size is 500MB. '
            f'Your file is {size_mb:.1f}MB. '
            f'Consider using YouTube or Vimeo for longer videos.'
        )


def validate_video_file_type(file: UploadedFile):
    """
    Validate video file type based on extension and MIME type
    """
    allowed_extensions = ['.mp4', '.mov', '.avi', '.webm', '.mkv']
    allowed_mime_types = [
        'video/mp4',
        'video/quicktime',
        'video/x-msvideo',
        'video/webm',
        'video/x-matroska',
    ]
    
    # Check file extension
    file_extension = None
    if hasattr(file, 'name') and file.name:
        file_extension = '.' + file.name.split('.')[-1].lower()
        
        if file_extension not in allowed_extensions:
            raise ValidationError(
                f'Invalid file type "{file_extension}". '
                f'Allowed formats: {", ".join(allowed_extensions)}'
            )
    
    # Check MIME type if available
    if hasattr(file, 'content_type') and file.content_type:
        if file.content_type not in allowed_mime_types:
            raise ValidationError(
                f'Invalid video format. Detected type: {file.content_type}. '
                f'Please upload MP4, MOV, AVI, or WebM files.'
            )


def validate_resource_file_size(file: UploadedFile):
    """
    Validate resource file size (max 50MB for PDFs, documents, etc.)
    """
    max_size = 50 * 1024 * 1024  # 50MB in bytes
    
    if file.size > max_size:
        size_mb = file.size / (1024 * 1024)
        raise ValidationError(
            f'Resource file too large. Maximum size is 50MB. '
            f'Your file is {size_mb:.1f}MB.'
        )


def validate_resource_file_type(file: UploadedFile):
    """
    Validate resource file type (PDFs, docs, images, archives)
    """
    allowed_extensions = [
        '.pdf', '.doc', '.docx', '.ppt', '.pptx', 
        '.xls', '.xlsx', '.txt', '.zip', '.rar',
        '.jpg', '.jpeg', '.png', '.gif', '.svg'
    ]
    
    if hasattr(file, 'name') and file.name:
        file_extension = '.' + file.name.split('.')[-1].lower()
        
        if file_extension not in allowed_extensions:
            raise ValidationError(
                f'Invalid resource file type "{file_extension}". '
                f'Allowed formats: PDF, Office documents, images, or ZIP archives.'
            )
