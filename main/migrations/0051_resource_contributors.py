# Generated by Django 4.0.7 on 2023-01-12 09:54

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0050_filecontent_image_alt'),
    ]

    operations = [
        migrations.AddField(
            model_name='resource',
            name='contributors',
            field=models.ManyToManyField(blank=True, related_name='contributor_in_resources', to=settings.AUTH_USER_MODEL, verbose_name='Contributeurs'),
        ),
    ]
