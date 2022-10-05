# Generated by Django 4.0.7 on 2022-10-05 17:13

from django.db import migrations, models
import django_quill.fields


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0022_alter_base_cover_image_alter_base_profile_image_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=50, verbose_name='titre')),
                ('icon', models.CharField(help_text="nom de l'icone remix icon, type ri-search-line", max_length=50, verbose_name='icone')),
                ('show_in_menu', models.BooleanField(default=False, verbose_name='faire apparaitre la page dans le menu')),
                ('description', models.CharField(max_length=180, verbose_name='description (SEO)')),
                ('content', django_quill.fields.QuillField()),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
