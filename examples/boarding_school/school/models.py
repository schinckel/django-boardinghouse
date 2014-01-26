from django.db import models

from boardinghouse.base import SchemaAwareModel
from boardinghouse.models import Schema


class School(Schema):
    pass


class StaffMember(SchemaAwareModel):
    name = models.CharField(max_length=64)
    staff_id = models.CharField(unique=True, max_length=16)
    
    def __unicode__(self):
        return u"%s (%s)" % (self.name, self.staff_id)

class Student(SchemaAwareModel):
    name = models.CharField(max_length=64)
    student_id = models.CharField(unique=True, max_length=16)

    def __unicode__(self):
        return u"%s (%s)" % (self.name, self.student_id)


class Subject(SchemaAwareModel):
    name = models.CharField(unique=True, max_length=64)

    def __unicode__(self):
        return self.name

SEMESTERS = (
    (0, 'Summer Semester'),
    (1, 'Semester 1'),
    (2, 'Semester 2'),
)

GRADES = (
    ('HD', 'High Distinction'),
    ('D', 'Distinction'),
    ('C', 'Credit'),
    ('P1', 'Pass, Level 1'),
    ('P2', 'Pass, Level 2'),
    ('F1', 'Fail, Level 1'),
    ('F2', 'Fail, Level 2'),
    ('NGP', 'Non-Graded Pass'),
    ('NGF', 'Non-Graded Fail'),
)


class Enrolment(SchemaAwareModel):
    student = models.ForeignKey(Student, related_name='enrolments')
    subject = models.ForeignKey(Subject, related_name='enrolments')
    enrolment_date = models.DateField()
    year = models.IntegerField()
    semester = models.IntegerField(choices=SEMESTERS)
    grade = models.CharField(choices=GRADES, max_length=3, null=True, blank=True)
    
    def __unicode__(self):
        if self.grade:
            return u'%s studied %s in %s %s. Grade was %s' % (
                self.student.name,
                self.subject.name,
                self.get_semester_display(),
                self.year,
                self.get_grade_display()
            )
        return u'%s enrolled in %s in %s %s.' % (
            self.student.name,
            self.subject.name,
            self.get_semester_display(), 
            self.year,
        )