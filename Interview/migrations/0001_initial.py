# Generated by Django 5.1.7 on 2025-04-12 19:46

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('Empjob', '0003_answer_question_text'),
        ('user_account', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='InterviewShedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField()),
                ('selected', models.BooleanField(default=False)),
                ('active', models.BooleanField(default=True)),
                ('status', models.CharField(choices=[('Selected', 'Selected'), ('Rejected', 'Rejected'), ('You missed', 'You missed'), ('Upcoming', 'Upcoming'), ('Canceled', 'Canceled')], default='Upcoming', max_length=20)),
                ('candidate', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='candidate', to='user_account.candidate')),
                ('employer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='employer', to='user_account.employer')),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='job', to='Empjob.jobs')),
            ],
        ),
    ]
