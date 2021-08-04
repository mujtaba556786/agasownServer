# Generated by Django 3.0.5 on 2021-08-03 11:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('odata', '0003_auto_20210803_1635'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='msrp',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='ranking',
            field=models.CharField(blank=True, choices=[('promoted', 'Promoted'), ('best_seller', 'Best Seller')], max_length=15, null=True),
        ),
    ]
