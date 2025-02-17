# Generated by Django 5.1.1 on 2024-09-19 09:35

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("land_buyers", "0001_initial"),
        ("lawyers", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="landbuyer",
            name="lawyer",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="lawyers.lawyer",
            ),
        ),
    ]
