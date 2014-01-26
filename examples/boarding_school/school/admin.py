from django.contrib import admin

from .models import School, Student, StaffMember, Subject, Enrolment

admin.site.register(School)
admin.site.register(Student)
admin.site.register(StaffMember)
admin.site.register(Subject)
admin.site.register(Enrolment)