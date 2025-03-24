from django.db import models
from django.db.models import Sum

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
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    address = models.TextField()
    photo = models.ImageField(upload_to='patients/photos/', blank=True, null=True)
    type_disease = models.ForeignKey(TypeDisease, on_delete=models.CASCADE, related_name='appointments')
    face_condition = models.TextField()
    medications_taken = models.TextField()
    home_care_items = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='debtor')

    total_payment_due = models.DecimalField(max_digits=10, decimal_places=2,
                                            default=0.00)  # Umumiy to‘lanishi kerak bo‘lgan summa
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name

    @property
    def total_paid(self):
        """Bemor tomonidan to‘langan jami summa"""
        return self.payments.aggregate(total=Sum('amount'))['total'] or 0.00

    @property
    def remaining_debt(self):
        """Bemorning qolgan qarzi (manfiy bo‘lsa ham xato chiqarmaydi)"""
        return self.total_payment_due - self.total_paid

    def update_status(self):
        """Agar qarz <= 0 bo‘lsa, statusni `paid`ga o‘zgartirish"""
        if self.remaining_debt <= 0:
            self.status = 'paid'
        else:
            self.status = 'debtor'
        self.save()


class Appointment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    appointment_time = models.DateTimeField()

    def __str__(self):
        return f"{self.patient.full_name} - {self.appointment_time}"


class PatientPayment(models.Model):
    """
    Bemor tomonidan amalga oshirilgan to‘lovlar tarixi
    """
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # To‘lov summasi
    payment_date = models.DateTimeField(auto_now_add=True)  # To‘lov sanasi

    def __str__(self):
        return f"{self.patient.full_name} - {self.amount} so‘m ({self.payment_date})"

    def save(self, *args, **kwargs):
        """To‘lov kiritilganda bemorning qarzini va statusini yangilash"""
        super().save(*args, **kwargs)
        self.patient.update_status()
