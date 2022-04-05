# Generated by Django 4.0.2 on 2022-04-05 11:56

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('main', '0002_ressourcecategory_category_ressources_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContributorProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
            ],
            options={
                'verbose_name': 'Profil de contributeur',
            },
        ),
        migrations.CreateModel(
            name='ExternalProducer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('email_contact', models.EmailField(max_length=254)),
                ('validated', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Producteur sans compte sur la plateforme',
                'verbose_name_plural': 'Producteurs sans compte sur la plateforme',
            },
        ),
        migrations.CreateModel(
            name='Resource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateField(auto_now=True)),
                ('title', models.CharField(max_length=100)),
                ('content', models.TextField()),
                ('is_draft', models.BooleanField(default=True)),
                ('description', models.CharField(max_length=60)),
                ('zip_code', models.IntegerField(blank=True, null=True)),
                ('url', models.URLField(blank=True, null=True)),
                ('thumbnail', models.ImageField(blank=True, null=True, upload_to='')),
                ('creator', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='creator', to=settings.AUTH_USER_MODEL)),
                ('internal_producer', models.ManyToManyField(blank=True, null=True, related_name='internal_producers', to=settings.AUTH_USER_MODEL)),
                ('linked_resources', models.ManyToManyField(blank=True, null=True, to='main.Resource')),
            ],
            options={
                'verbose_name': 'Ressource',
            },
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateField(auto_now=True)),
                ('name', models.CharField(max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='TagCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateField(auto_now=True)),
                ('name', models.CharField(max_length=20)),
                ('relates_to', models.CharField(choices=[('Resource', 'Ressource'), ('User', 'Utilisateur'), ('Base', 'Base')], max_length=10)),
            ],
            options={
                'verbose_name': 'Catégorie de tags',
                'verbose_name_plural': 'Catégories de tags',
            },
        ),
        migrations.RemoveField(
            model_name='ressource',
            name='author',
        ),
        migrations.RemoveField(
            model_name='ressourcecategory',
            name='category',
        ),
        migrations.RemoveField(
            model_name='ressourcecategory',
            name='ressource',
        ),
        migrations.AddField(
            model_name='base',
            name='admins',
            field=models.ManyToManyField(related_name='admins', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='base',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='owner', to=settings.AUTH_USER_MODEL),
        ),
        migrations.DeleteModel(
            name='Category',
        ),
        migrations.DeleteModel(
            name='Ressource',
        ),
        migrations.DeleteModel(
            name='RessourceCategory',
        ),
        migrations.AddField(
            model_name='tagcategory',
            name='base',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='main.base'),
        ),
        migrations.AddField(
            model_name='tag',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.tagcategory'),
        ),
        migrations.AddField(
            model_name='tag',
            name='parent_tag',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='main.tag'),
        ),
        migrations.AddField(
            model_name='resource',
            name='root_base',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='main.base'),
        ),
        migrations.AddField(
            model_name='externalproducer',
            name='resource',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='external_producer', to='main.resource'),
        ),
        migrations.AddField(
            model_name='contributorprofile',
            name='base',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contributor_profiles', to='main.base'),
        ),
        migrations.AddField(
            model_name='contributorprofile',
            name='contributors',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='tagcategory',
            unique_together={('name', 'base')},
        ),
        migrations.AlterUniqueTogether(
            name='tag',
            unique_together={('name', 'category')},
        ),
    ]
