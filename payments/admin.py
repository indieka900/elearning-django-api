# payments/admin.py

from django.contrib import admin
from .models import admin_model

for model in admin_model:
    admin.site.register(model)