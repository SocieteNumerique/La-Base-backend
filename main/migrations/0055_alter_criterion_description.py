# Generated by Django 4.0.9 on 2023-02-16 08:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0054_remove_usergroup_users_remove_resource_groups_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='criterion',
            name='description',
            field=models.TextField(verbose_name='description'),
        ),
    ]