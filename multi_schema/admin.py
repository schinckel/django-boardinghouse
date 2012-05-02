from django.contrib import admin, auth
from models import Schema, UserSchema

class SchemaAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        if obj is not None:
            return ('schema',)
        return ()

admin.site.register(Schema, SchemaAdmin)

class SchemaInline(admin.StackedInline):
    model = UserSchema

# Inject SchemeInline into UserAdmin
UserAdmin = admin.site._registry[auth.models.User].__class__

class SchemaUserAdmin(UserAdmin):
    inlines = UserAdmin.inlines + [SchemaInline]
    
admin.site.unregister(auth.models.User)
admin.site.register(auth.models.User, SchemaUserAdmin)