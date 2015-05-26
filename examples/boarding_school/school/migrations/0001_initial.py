# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('boardinghouse', '0002_patch_admin'),
    ]

    operations = [
        migrations.CreateModel(
            name='Enrolment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('enrolment_date', models.DateField()),
                ('year', models.IntegerField()),
                ('semester', models.IntegerField(choices=[(0, b'Summer Semester'), (1, b'Semester 1'), (2, b'Semester 2')])),
                ('grade', models.CharField(blank=True, max_length=3, null=True, choices=[(b'HD', b'High Distinction'), (b'D', b'Distinction'), (b'C', b'Credit'), (b'P1', b'Pass, Level 1'), (b'P2', b'Pass, Level 2'), (b'F1', b'Fail, Level 1'), (b'F2', b'Fail, Level 2'), (b'NGP', b'Non-Graded Pass'), (b'NGF', b'Non-Graded Fail')])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='School',
            fields=[
                ('schema_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to=settings.BOARDINGHOUSE_SCHEMA_MODEL)),
            ],
            options={
                'abstract': False,
            },
            bases=('boardinghouse.schema',),
        ),
        migrations.CreateModel(
            name='StaffMember',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64)),
                ('staff_id', models.CharField(unique=True, max_length=16)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Student',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64)),
                ('student_id', models.CharField(unique=True, max_length=16)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=64)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='enrolment',
            name='student',
            field=models.ForeignKey(related_name='enrolments', to='school.Student'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='enrolment',
            name='subject',
            field=models.ForeignKey(related_name='enrolments', to='school.Subject'),
            preserve_default=True,
        ),
    ]
