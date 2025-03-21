# Generated by Django 5.0.2 on 2025-03-18 06:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Quote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(help_text='Enter the quote text')),
                ('author', models.CharField(help_text='Enter the quote author', max_length=100)),
                ('category', models.CharField(blank=True, help_text='Optional category for the quote', max_length=50)),
                ('date_added', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
