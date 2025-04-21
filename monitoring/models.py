from django.db import models
from django.db.models import Sum
from decimal import Decimal


class Region(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class TypeDisease(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Patient(models.Model):
    STATUS_CHOICES = [
        ('treated', 'Davolanib bo‘lgan'),
        ('debtor', 'Qarzdor'),
        ('paid', 'tolangan'),
    ]

    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True)
    address = models.TextField(blank=True, null=True)
    photo = models.ImageField(upload_to='patients/photos/', blank=True, null=True)
    type_disease = models.ForeignKey(TypeDisease, on_delete=models.SET_NULL, null=True, related_name='appointments')
    face_condition = models.TextField(blank=True, null=True)
    medications_taken = models.TextField(blank=True, null=True)
    home_care_items = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='debtor')
    total_payment_due = models.DecimalField(max_digits=50, decimal_places=2,
                                            default=0.00)  # Umumiy to‘lanishi kerak bo‘lgan summa
    created_at = models.DateTimeField(auto_now_add=True)

    # Soft delete maydoni
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.full_name if self.full_name else "Nomalum"

    @property
    def total_paid(self):
        """Bemor tomonidan to‘langan jami summa"""
        total = self.payments.aggregate(total=Sum('amount'))['total']
        return Decimal(str(total)) if total is not None else Decimal('0.00')

    @property
    def remaining_debt(self):
        """Bemorning qolgan qarzi (manfiy bo‘lsa ham xato chiqarmaydi)"""
        return self.total_payment_due - self.total_paid  # ✅ TypeError chiqmaydi

    def update_status(self):
        """Agar qarz <= 0 bo‘lsa, statusni `paid`ga o‘zgartirish"""
        if self.remaining_debt <= Decimal('0.00'):
            self.status = 'paid'
        else:
            self.status = 'debtor'
        self.save()

    def delete(self, *args, **kwargs):
        """Soft delete: faqat `is_deleted` ni True qilish"""
        self.is_deleted = True
        self.save()

    @classmethod
    def active_patients(cls):
        """Faol bemorlarni qaytarish"""
        return cls.objects.filter(is_deleted=False)


class Appointment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.SET_NULL, null=True, related_name='appointments')
    appointment_time = models.DateTimeField()

    def __str__(self):
        full_name = self.patient.full_name if self.patient and self.patient.full_name else "Nomalum"
        appointment_time = self.appointment_time if self.appointment_time else "Nomalum"
        return f"{full_name} - {appointment_time}"


class PatientPayment(models.Model):
    """
    Bemor tomonidan amalga oshirilgan to‘lovlar tarixi
    """
    # patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='payments')
    patient = models.ForeignKey(Patient, on_delete=models.SET_NULL, null=True, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # To‘lov summasi
    payment_date = models.DateTimeField(auto_now_add=True)  # To‘lov sanasi

    def __str__(self):
        full_name = self.patient.full_name if self.patient and self.patient.full_name else "Nomalum"
        amount = f"{self.amount} so‘m" if self.amount else "Nomalum"
        payment_date = self.payment_date.strftime("%Y-%m-%d") if self.payment_date else "Nomalum"
        return f"{full_name} - {amount} ({payment_date})"

    def save(self, *args, **kwargs):
        """To‘lov kiritilganda bemorning qarzini va statusini yangilash"""
        super().save(*args, **kwargs)
        self.patient.update_status()
