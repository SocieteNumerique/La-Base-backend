# Generated by Django 4.0.2 on 2022-05-03 08:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0007_alter_contentblock_options_contentblock_index_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='contentblock',
            options={'ordering': ['order'], 'verbose_name': 'Bloc de contenu', 'verbose_name_plural': 'Blocs de contenu'},
        ),
        migrations.RenameField(
            model_name='contentblock',
            old_name='index',
            new_name='order',
        ),
        migrations.RenameField(
            model_name='tagcategory',
            old_name='maximum_tag_number',
            new_name='maximum_tag_count',
        ),
        migrations.AddField(
            model_name='tagcategory',
            name='description',
            field=models.CharField(max_length=100, null=True, verbose_name='description'),
        ),
        migrations.AlterField(
            model_name='linkcontent',
            name='link',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='tag',
            name='definition',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='textcontent',
            name='text',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='contentblock',
            unique_together={('resource', 'order')},
        ),
    ]