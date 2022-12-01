# Generated by Django 4.0.7 on 2022-12-01 13:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0039_auto_20221130_1328'),
    ]

    operations = [
        migrations.AddField(
            model_name='base',
            name='own_resource_count',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='base',
            name='pinned_resources_count',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='base',
            name='visit_count',
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]