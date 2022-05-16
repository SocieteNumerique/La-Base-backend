# Generated by Django 4.0.2 on 2022-05-16 08:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0011_resource_creator_bases_alter_resource_root_base'),
    ]

    operations = [
        migrations.AddField(
            model_name='externalproducer',
            name='occupation',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='main.tag'),
        ),
        migrations.AlterField(
            model_name='tagcategory',
            name='name',
            field=models.CharField(max_length=40, verbose_name='nom'),
        ),
        migrations.AlterField(
            model_name='tagcategory',
            name='relates_to',
            field=models.CharField(blank=True, choices=[('Resource', 'Ressources'), ('User', 'Utilisateurs'), ('Base', 'Bases')], max_length=10, null=True, verbose_name='lié aux'),
        ),
    ]
