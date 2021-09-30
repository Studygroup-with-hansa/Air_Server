# Generated by Django 3.2.7 on 2021-09-30 07:02

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('v1', '0004_auto_20210930_1122'),
    ]

    operations = [
        migrations.AddField(
            model_name='daily',
            name='userEmail',
            field=models.EmailField(default='', max_length=254, primary_key=True, serialize=False, verbose_name='Table Owner'),
        ),
        migrations.AlterField(
            model_name='daily',
            name='date',
            field=models.DateField(default=django.utils.timezone.now, verbose_name='Date'),
        ),
        migrations.AlterField(
            model_name='daily',
            name='goal',
            field=models.IntegerField(default=0, verbose_name='Daily goal (sec)'),
        ),
        migrations.AlterField(
            model_name='user',
            name='dailyInfo',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='v1.daily', verbose_name='Information of Daily'),
        ),
        migrations.AlterField(
            model_name='user',
            name='profileImg',
            field=models.URLField(default='https://cdn.discordapp.com/attachments/892970959668129896/892971164807340073/defaultProfileImg.jpg', verbose_name='profile Image URL'),
        ),
    ]
