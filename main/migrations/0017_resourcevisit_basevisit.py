# Generated by Django 4.0.6 on 2022-09-02 14:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0016_alter_resource_resource_created_on'),
    ]

    operations = [
        migrations.CreateModel(
            name='ResourceVisit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(auto_now=True)),
                ('ip_hash', models.CharField(max_length=80)),
                ('instance', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.resource')),
            ],
            options={
                'unique_together': {('instance', 'date', 'ip_hash')},
            },
        ),
        migrations.CreateModel(
            name='BaseVisit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(auto_now=True)),
                ('ip_hash', models.CharField(max_length=80)),
                ('instance', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.base')),
            ],
            options={
                'unique_together': {('instance', 'date', 'ip_hash')},
            },
        ),
    ]