# Generated by Django 5.1 on 2024-08-20 23:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_alter_criterios_deducao_imposto'),
    ]

    operations = [
        migrations.AddField(
            model_name='empresa',
            name='regime_apuracao',
            field=models.CharField(default=1, max_length=100),
            preserve_default=False,
        ),
    ]