from django.contrib import admin, auth

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

class SchemaUserAdmin(UserAdmin):
    inlines = UserAdmin.inlines + [SchemaInline]
    
admin.site.unregister(User)
admin.site.register(User, SchemaUserAdmin)



# Patch ModelAdmin
ModelAdmin_queryset = admin.ModelAdmin.queryset

def queryset(self, request):
    queryset = ModelAdmin_queryset(self, request)
    if self.model._is_schema_aware and not request.session.get('schema'):
        return queryset.none()
    return queryset

admin.ModelAdmin.queryset = queryset