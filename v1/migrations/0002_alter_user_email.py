# Generated by Django 3.2.7 on 2021-09-24 18:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('v1', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(max_length=64, unique=True, verbose_name='email'),
        ),
    ]
