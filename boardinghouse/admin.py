from django.contrib import admin, auth
from django.http import Http404

from .models import Schema, User

class SchemaAdmin(admin.ModelAdmin):
    exclude = ('users',)
    
    def get_readonly_fields(self, request, obj=None):
        if obj is not None:
            return ('schema',)
        return ()

admin.site.register(Schema, SchemaAdmin)

class SchemaInline(admin.TabularInline):
    model = Schema.users.through
    extra = 0

# Inject SchemeInline into UserAdmin
UserAdmin = admin.site._registry[User].__class__

def schemata(obj):
    return '<br>'.join(obj.schemata.values_list('name', flat=True))
schemata.allow_tags = True

class SchemaUserAdmin(UserAdmin):
    inlines = UserAdmin.inlines + [SchemaInline]
    list_display = ('username', 'is_active', 'first_name', 'last_name', 'email', schemata, )
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'schemata')
    
admin.site.unregister(User)
admin.site.register(User, SchemaUserAdmin)



# # Patch ModelAdmin
# ModelAdmin_queryset = admin.ModelAdmin.queryset
# 
# def queryset(self, request):
#     if self.model._is_schema_aware and not request.session.get('schema'):
#         raise Http404()
#         return ModelAdmin_queryset(self, request).none()
#     return ModelAdmin_queryset(self, request)
# 
# admin.ModelAdmin.queryset = queryset