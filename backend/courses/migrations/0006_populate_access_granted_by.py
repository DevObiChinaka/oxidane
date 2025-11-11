# Generated data migration for populating access_granted_by field
from django.db import migrations


def populate_access_granted_by(apps, schema_editor):
    """
    Populate access_granted_by field for existing CourseAccess records.
    
    For backward compatibility, we set all existing access records to 'admin'
    since we don't have historical data about how access was originally granted.
    """
    CourseAccess = apps.get_model('courses', 'CourseAccess')
    
    # Update all existing records without access_granted_by
    updated_count = CourseAccess.objects.filter(
        access_granted_by__isnull=True
    ).update(access_granted_by='admin')
    
    print(f"Updated {updated_count} CourseAccess records with access_granted_by='admin'")


def reverse_populate(apps, schema_editor):
    """
    Reverse migration: set access_granted_by back to NULL
    """
    CourseAccess = apps.get_model('courses', 'CourseAccess')
    
    # Only reverse records that were set to 'admin'
    reversed_count = CourseAccess.objects.filter(
        access_granted_by='admin'
    ).update(access_granted_by=None)
    
    print(f"Reversed {reversed_count} CourseAccess records (set access_granted_by to NULL)")


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0005_add_courseaccess_subscription_fields'),
    ]

    operations = [
        migrations.RunPython(
            populate_access_granted_by,
            reverse_code=reverse_populate,
        ),
    ]
