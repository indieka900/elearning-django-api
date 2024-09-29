from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import admin_models, CustomUser

# Register your models here.

    
@admin.action(description="activate selected users")
def activate_users(modeladmin, request, queryset):
    queryset.update(is_active=True)


@admin.action(description="deactivate selected users")
def deactivate_users(modeladmin, request, queryset):
    queryset.update(is_active=False)

@admin.register(CustomUser)
class UserAdminConfig(UserAdmin):
    ordering = ('id',)
    search_fields = ('email','first_name','last_name','username')
    list_filter = ('is_active','is_staff','role',)
    list_display = ('id','email','first_name','last_name','phone_number','is_active','username','role')
    fieldsets = (
        (None, {'fields': ('email','first_name','last_name','phone_number','username',)}),
        ("Permissions", {"fields" :('is_staff','is_active','is_superuser',)}),
        ("Personal", {"fields":("role","secret")}),
    )
    add_fieldsets = (
        (None, {
            'classes':('wide',),
            'fields': ('email','username','first_name','last_name','password1','password2','phone_number','is_staff','is_active','is_superuser','role')
        }),
    )
    actions = [activate_users,deactivate_users]
    
for admin_model in admin_models:
    admin.site.register(admin_model)