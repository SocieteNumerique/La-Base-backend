# Generated by Django 4.0.7 on 2022-12-08 14:24

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0042_auto_20221206_1547'),
    ]

    operations = [
        migrations.CreateModel(
            name='SeenIntroSlug',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.CharField(max_length=50)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'slug')},
            },
        ),
        migrations.RemoveField(
            model_name='intro',
            name='page',
        ),
        migrations.DeleteModel(
            name='SeenPageIntros',
        ),
    ]
