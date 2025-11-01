# Generated migration for adding is_public and invite_link fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('settings_app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='telegramgroup',
            name='is_public',
            field=models.BooleanField(default=False, help_text='Public groups show invite link; private groups are bot-invite only'),
        ),
        migrations.AddField(
            model_name='telegramgroup',
            name='invite_link',
            field=models.URLField(blank=True, help_text='Telegram invite link (only for public groups)'),
        ),
    ]
