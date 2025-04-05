from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User
from .forms import CustomUserCreationForm, CustomUserChangeForm
from django.contrib.auth.models import Group

# Bu orqali Group modelini admin paneldan olib tashlaymiz
admin.site.unregister(Group)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User

    list_display = ("username", "role", "is_staff", "is_superuser")
    search_fields = ("username",)
    list_filter = ("role", "is_staff", "is_superuser")
    ordering = ("username",)

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Rol", {"fields": ("role",)}),
        ("Ruxsatlar", {"fields": ("is_staff", "is_superuser")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "role", "password1", "password2", "is_staff", "is_superuser")}
        ),
    )

    # Bu orqali 'groups' va 'user_permissions' ko‘rinmaydi
    filter_horizontal = ()
