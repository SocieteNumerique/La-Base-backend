# Generated by Django 4.0.7 on 2022-10-05 16:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0021_alter_base_cover_image_alter_base_profile_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='base',
            name='cover_image',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='main.resizableimage'),
        ),
        migrations.AlterField(
            model_name='base',
            name='profile_image',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='profile_base', to='main.resizableimage'),
        ),
        migrations.AlterField(
            model_name='collection',
            name='profile_image',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='main.resizableimage'),
        ),
        migrations.AlterField(
            model_name='resource',
            name='profile_image',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='main.resizableimage'),
        ),
    ]
