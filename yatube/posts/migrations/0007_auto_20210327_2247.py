# Generated by Django 2.2.9 on 2021-03-27 22:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0006_auto_20210327_2134'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='post',
            options={'ordering': ['-pub_date']},
        ),
    ]
