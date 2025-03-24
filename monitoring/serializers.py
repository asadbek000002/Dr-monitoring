from rest_framework import serializers
from .models import Patient, Appointment, Region, TypeDisease, PatientPayment


# USer ni qaysi viloyatda ekanini aniqlovchi malumot
class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ['id', 'name']


# Userni qaysi kasallik boyicha kelishini aniqlovchi qoshimcha malumot
class TypeDiseaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeDisease
        fields = ['id', 'name']


# User malumotini korikka yoki davolanishga kelishini belgiluvchi malumotlar
class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ['id', 'appointment_time']


# USer malumotlarini listda chiqarish
class PatientSerializer(serializers.ModelSerializer):
    region = RegionSerializer()
    type_disease = TypeDiseaseSerializer()

    class Meta:
        model = Patient
        fields = [
            'id', 'photo', 'full_name', 'type_disease', 'phone_number', 'region', 'status', 'created_at']


# User malumotlarini yaratish
class PatientCreateSerializer(serializers.ModelSerializer):
    appointments = AppointmentSerializer(many=True, required=False)
    remove = serializers.ListField(child=serializers.IntegerField(), required=False, write_only=True)

    class Meta:
        model = Patient
        fields = [
            'id', 'full_name', 'phone_number', 'region', 'address', 'photo',
            'type_disease', 'face_condition', 'medications_taken',
            'home_care_items', 'status', 'appointments', 'remove', 'created_at'
        ]

    def create(self, validated_data):
        appointments_data = validated_data.pop('appointments', [])
        patient = Patient.objects.create(**validated_data)

        # Yangi appointment'larni yaratish
        created_appointments = [
            Appointment(patient=patient, **appointment) for appointment in appointments_data
        ]
        if created_appointments:
            Appointment.objects.bulk_create(created_appointments)

        # 🔥 Appointment'larni qaytadan olib, ularni response uchun serializatsiya qilish
        patient.refresh_from_db()
        return patient

    def to_representation(self, instance):
        """
        Ma'lumotlarni qayta formatlash, appointment'larni qo‘shish
        """
        data = super().to_representation(instance)
        data['appointments'] = AppointmentSerializer(instance.appointments.all(), many=True).data
        return data


# User malumotlarini tahrirlash
class PatientUpdateSerializer(serializers.ModelSerializer):
    appointments = AppointmentSerializer(many=True, required=False, read_only=True)  # Faqat o‘qish uchun
    remove = serializers.ListField(child=serializers.IntegerField(), required=False,
                                   write_only=True)  # O‘chiriladiganlar
    new_appointments = serializers.ListField(child=serializers.DictField(), required=False,
                                             write_only=True)  # Yangi qo‘shiladiganlar

    class Meta:
        model = Patient
        fields = [
            'full_name', 'phone_number', 'region', 'address', 'photo',
            'type_disease', 'face_condition', 'medications_taken',
            'home_care_items', 'status', 'appointments', 'remove', 'new_appointments'
        ]

    def update(self, instance, validated_data):
        # ❌ O‘chirilishi kerak bo‘lgan appointment ID-lari
        remove_ids = validated_data.pop('remove', [])
        if remove_ids:
            instance.appointments.filter(id__in=remove_ids).delete()

        # ➕ Yangi appointmentlar yaratish
        new_appointments_data = validated_data.pop('new_appointments', [])
        if new_appointments_data:
            Appointment.objects.bulk_create([
                Appointment(patient=instance, **appointment) for appointment in new_appointments_data
            ])

        # 🔄 Boshqa maydonlarni yangilash
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance

    def to_representation(self, instance):
        """
        🔄 Ma'lumotlarni frontend uchun formatlash (appointments qo‘shiladi)
        """
        data = super().to_representation(instance)
        data['appointments'] = AppointmentSerializer(instance.appointments.all(), many=True).data
        return data


class PatientPaymentSerializer(serializers.ModelSerializer):
    """
    Bemor tomonidan amalga oshirilgan to‘lovlar tarixi uchun serializer
    """

    class Meta:
        model = PatientPayment
        fields = ['id', 'amount', 'payment_date']


class PatientDetailSerializer(serializers.ModelSerializer):
    """
    Bemorning batafsil ma’lumotlarini qaytaruvchi serializer
    """
    region = RegionSerializer()  # Hudud ma’lumotlari
    type_disease = TypeDiseaseSerializer()  # Kasallik turi haqida ma’lumot
    appointments = AppointmentSerializer(many=True, required=False)  # Bemor uchrashuvlari
    payments = PatientPaymentSerializer(many=True, read_only=True)  # To‘lovlar tarixi
    is_superuser = serializers.SerializerMethodField()  # Admin huquqini tekshirish

    class Meta:
        model = Patient
        fields = ['id', 'full_name', 'phone_number', 'region', 'address', 'photo', 'type_disease',
                  'face_condition', 'medications_taken', 'home_care_items', 'status', 'created_at',
                  'total_payment_due', 'total_paid', 'remaining_debt', 'appointments', 'payments', 'is_superuser']

    def get_is_superuser(self, obj):
        """Foydalanuvchi admin ekanligini tekshirish"""
        request = self.context.get('request', None)
        return request.user.is_superuser if request else False

# class PatientDetailSerializer(serializers.ModelSerializer):
#     region = RegionSerializer()
#     type_disease = TypeDiseaseSerializer()
#     appointments = AppointmentSerializer(many=True, required=False)
#     is_superuser = serializers.SerializerMethodField()
#
#     class Meta:
#         model = Patient
#         fields = [
#             'id', 'full_name', 'phone_number', 'region', 'address', 'photo',
#             'type_disease', 'face_condition', 'medications_taken', 'home_care_items', 'status', 'appointments',
#             'is_superuser'
#         ]
#
#     def get_is_superuser(self, obj):
#         request = self.context.get('request', None)
#         return request.user.is_superuser if request else False
