# Generated by Django 5.1.4 on 2025-04-26 16:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0006_alter_order_status_profile'),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='review_images/'),
        ),
    ]
