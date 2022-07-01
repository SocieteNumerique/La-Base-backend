# Generated by Django 4.0.2 on 2022-06-30 13:56

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0008_user_cnfs_id_organization_alter_resource_tags'),
    ]

    operations = [
        migrations.AddField(
            model_name='base',
            name='authorized_user_tags',
            field=models.ManyToManyField(blank=True, related_name='authorized_tags_in_bases', to='main.Tag', verbose_name="Tags d'utilisateurs avec accès en lecture"),
        ),
        migrations.AddField(
            model_name='base',
            name='authorized_users',
            field=models.ManyToManyField(blank=True, related_name='authorized_bases', to=settings.AUTH_USER_MODEL, verbose_name='Utilisateurs avec accès en lecture'),
        ),
        migrations.AddField(
            model_name='base',
            name='contributors',
            field=models.ManyToManyField(blank=True, related_name='contributor_in_bases', to=settings.AUTH_USER_MODEL, verbose_name='Contributeurs'),
        ),
        migrations.AddField(
            model_name='resource',
            name='authorized_user_tags',
            field=models.ManyToManyField(blank=True, related_name='authorized_tags_in_resources', to='main.Tag', verbose_name="Tags d'utilisateurs avec accès en lecture"),
        ),
        migrations.AddField(
            model_name='resource',
            name='authorized_users',
            field=models.ManyToManyField(blank=True, related_name='authorized_resources', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='base',
            name='contributor_tags',
            field=models.ManyToManyField(blank=True, related_name='contributor_tags_in_bases', to='main.Tag', verbose_name='Tags de contributeurs'),
        ),
        migrations.AlterField(
            model_name='base',
            name='state',
            field=models.CharField(choices=[('public', 'Public'), ('private', 'Privé'), ('draft', 'Brouillon')], default='draft', max_length=10),
        ),
        migrations.AlterField(
            model_name='resource',
            name='state',
            field=models.CharField(choices=[('public', 'Public'), ('private', 'Privé'), ('draft', 'Brouillon')], default='draft', max_length=10),
        ),
        migrations.AlterField(
            model_name='resource',
            name='tags',
            field=models.ManyToManyField(blank=True, related_name='resources', to='main.Tag'),
        ),
    ]
