# Generated by Django 5.1.7 on 2025-04-04 20:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0005_alter_patient_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='patient',
            name='address',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='patient',
            name='face_condition',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='patient',
            name='home_care_items',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='patient',
            name='medications_taken',
            field=models.TextField(blank=True, null=True),
        ),
    ]
