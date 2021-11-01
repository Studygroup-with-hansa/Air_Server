# Generated by Django 3.2.7 on 2021-10-31 07:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('v1', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='daily',
            name='memo',
            field=models.TextField(default=''),
        ),
        migrations.CreateModel(
            name='todoList',
            fields=[
                ('primaryKey', models.BigAutoField(db_column='pk', primary_key=True, serialize=False, verbose_name='pk')),
                ('isItDone', models.BooleanField(default=False)),
                ('todo', models.TextField(default='')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subject', to='v1.dailysubject')),
            ],
        ),
    ]