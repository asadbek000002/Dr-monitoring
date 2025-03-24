from django.contrib import admin
from django.contrib.admin import TabularInline
from .models import Patient, Appointment, TypeDisease, Region, PatientPayment


# Appointment modelini Patient admin panelida Inline ko‘rinishda qo‘shish
class AppointmentInline(admin.TabularInline):  # yoki admin.StackedInline
    model = Appointment
    extra = 1  # Qo‘shimcha maydon chiqarish (1 bo‘lsa, bitta bo‘sh qator qo‘shadi)

# Patient Admin paneli
@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone_number', 'region', 'status')  # Bemor haqida asosiy info
    search_fields = ('full_name', 'phone_number')
    list_filter = ('status', 'region')
    inlines = [AppointmentInline]  # Appointment larni ichiga qo‘shish

# Appointment ni ham alohida qo‘shish mumkin
@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'appointment_time')
    search_fields = ('patient__full_name',)
    list_filter = ('appointment_time',)

admin.site.register(TypeDisease)
admin.site.register(Region)
admin.site.register(PatientPayment)