# Generated by Django 2.1.1 on 2018-10-10 17:50

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0010_auto_20181007_0319'),
    ]

    operations = [
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.PositiveIntegerField(default=0)),
                ('is_approved', models.BooleanField(default=False)),
                ('is_complete', models.BooleanField(default=False)),
                ('request_time', models.DateTimeField(default=django.utils.timezone.now)),
                ('complete_time', models.DateTimeField(null=True)),
                ('from_account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transaction_from', to='app.Account')),
                ('to_account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transaction_to', to='app.Account')),
            ],
        ),
        migrations.CreateModel(
            name='UserRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('request_type', models.PositiveSmallIntegerField(blank=True, choices=[(1, 'Create'), (2, 'Read'), (3, 'Update'), (4, 'Delete')], null=True)),
                ('is_approved', models.BooleanField(default=False)),
                ('from_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='request_from', to=settings.AUTH_USER_MODEL)),
                ('to_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='request_to', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]