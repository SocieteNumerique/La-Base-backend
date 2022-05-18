# Generated by Django 4.0.2 on 2022-05-09 14:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0009_rename_parent_folder_contentblock_section_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contentblock',
            name='section',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='contents', to='main.contentsection'),
        ),
        migrations.AlterField(
            model_name='contentsection',
            name='resource',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sections', to='main.resource'),
        ),
    ]