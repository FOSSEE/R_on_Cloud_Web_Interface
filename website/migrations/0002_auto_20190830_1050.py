# Generated by Django 2.2.2 on 2019-08-30 10:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TextbookCompanionChapter',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('number', models.IntegerField()),
                ('name', models.CharField(max_length=255)),
                ('cloud_chapter_err_status', models.CharField(max_length=255)),
            ],
            options={
                'db_table': 'textbook_companion_chapter',
            },
        ),
        migrations.CreateModel(
            name='TextbookCompanionExample',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('approver_uid', models.IntegerField()),
                ('number', models.CharField(max_length=10)),
                ('caption', models.CharField(max_length=255)),
                ('approval_date', models.IntegerField()),
                ('approval_status', models.IntegerField()),
                ('timestamp', models.IntegerField()),
                ('cloud_err_status', models.IntegerField()),
                ('chapter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='website.TextbookCompanionChapter')),
            ],
            options={
                'db_table': 'textbook_companion_example',
            },
        ),
        migrations.CreateModel(
            name='TextbookCompanionProposal',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False, unique=True)),
                ('uid', models.IntegerField()),
                ('approver_uid', models.IntegerField()),
                ('full_name', models.CharField(max_length=50)),
                ('mobile', models.CharField(max_length=15)),
                ('gender', models.CharField(max_length=10)),
                ('how_project', models.CharField(max_length=50)),
                ('course', models.CharField(max_length=50)),
                ('branch', models.CharField(max_length=50)),
                ('university', models.CharField(max_length=100)),
                ('faculty', models.CharField(max_length=100)),
                ('reviewer', models.CharField(max_length=100)),
                ('completion_date', models.IntegerField()),
                ('creation_date', models.IntegerField()),
                ('approval_date', models.IntegerField()),
                ('proposal_status', models.IntegerField()),
                ('message', models.TextField()),
                ('scilab_version', models.CharField(max_length=20)),
                ('operating_system', models.CharField(max_length=20)),
                ('teacher_email', models.CharField(max_length=20)),
            ],
            options={
                'db_table': 'textbook_companion_proposal',
            },
        ),
        migrations.CreateModel(
            name='TextbookCompanionPreference',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False, unique=True)),
                ('pref_number', models.IntegerField()),
                ('book', models.CharField(max_length=100)),
                ('author', models.CharField(max_length=100)),
                ('isbn', models.CharField(max_length=25)),
                ('publisher', models.CharField(max_length=50)),
                ('edition', models.CharField(max_length=2)),
                ('year', models.IntegerField()),
                ('category', models.IntegerField()),
                ('approval_status', models.IntegerField()),
                ('cloud_pref_err_status', models.IntegerField()),
                ('proposal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='website.TextbookCompanionProposal')),
            ],
            options={
                'db_table': 'textbook_companion_preference',
            },
        ),
        migrations.CreateModel(
            name='TextbookCompanionExampleFiles',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('filename', models.CharField(max_length=255)),
                ('filepath', models.CharField(max_length=500)),
                ('filemime', models.CharField(max_length=255)),
                ('filesize', models.IntegerField()),
                ('filetype', models.CharField(max_length=1)),
                ('caption', models.CharField(max_length=100)),
                ('timestamp', models.IntegerField()),
                ('example', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='website.TextbookCompanionExample')),
            ],
            options={
                'db_table': 'textbook_companion_example_files',
            },
        ),
        migrations.AddField(
            model_name='textbookcompanionchapter',
            name='preference',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='website.TextbookCompanionPreference'),
        ),
    ]