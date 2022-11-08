# Generated by Django 4.0.7 on 2022-11-04 17:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0031_intro'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='intro',
            options={'ordering': ('order',), 'verbose_name': 'bulle de didacticiel', 'verbose_name_plural': 'bulles de didacticiel'},
        ),
        migrations.AlterField(
            model_name='intro',
            name='order',
            field=models.IntegerField(verbose_name='ordre dans la page'),
        ),
        migrations.AddField(
            model_name='intro',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to=''),
        ),
    ]