# Generated by Django 4.0.2 on 2022-05-30 14:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0020_remove_linkcontent_display_mode_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resource',
            name='creator_bases',
            field=models.ManyToManyField(related_name='created_resources', to='main.Base', verbose_name='Bases qui ont créé la ressource'),
        ),
        migrations.AlterField(
            model_name='resource',
            name='root_base',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='resources', to='main.base', verbose_name='Base à laquelle la ressource est rattachée'),
        ),
        migrations.AlterField(
            model_name='tag',
            name='name',
            field=models.CharField(max_length=60, verbose_name='nom'),
        ),
    ]
