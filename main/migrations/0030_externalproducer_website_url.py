# Generated by Django 4.0.7 on 2022-10-28 08:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0029_alter_resource_producer_state'),
    ]

    operations = [
        migrations.AddField(
            model_name='externalproducer',
            name='website_url',
            field=models.CharField(blank=True, max_length=150, null=True),
        ),
    ]