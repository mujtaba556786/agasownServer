# Generated by Django 3.0.5 on 2021-07-27 03:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('odata', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='categories',
            name='category_name_de',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='description_de',
            field=models.TextField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='product_highlight_de',
            field=models.TextField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='title_de',
            field=models.CharField(blank=True, max_length=1024, null=True),
        ),
    ]
