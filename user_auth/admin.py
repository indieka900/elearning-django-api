from django.contrib import admin
from .models import admin_models

# Register your models here.
for admin_model in admin_models:
    admin.site.register(admin_model)