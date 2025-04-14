from collections import defaultdict

from django.utils.timezone import now, timedelta
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView, CreateAPIView, DestroyAPIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated

from .models import Patient, PatientPayment, TypeDisease, Region, Appointment
from .serializers import PatientSerializer, PatientCreateSerializer, PatientDetailSerializer, PatientUpdateSerializer, \
    PatientPaymentSerializer, RegionSerializer, TypeDiseaseSerializer


class PatientPagination(PageNumberPagination):
    """
    Bemorlar ro‘yxati uchun pagination
    """
    page_size = 10  # Har bir sahifada 10 ta bemor chiqadi
    page_size_query_param = 'page_size'  # Foydalanuvchi o‘zi sonni belgilashi mumkin
    max_page_size = 100  # Maksimal 100 ta bemor


# Regionlar ro‘yxatini olish uchun API
class RegionListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        regions = Region.objects.all()
        serializer = RegionSerializer(regions, many=True)
        return Response(serializer.data)


# Kasallik turlari ro‘yxatini olish uchun API
class TypeDiseaseListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        diseases = TypeDisease.objects.all()
        serializer = TypeDiseaseSerializer(diseases, many=True)
        return Response(serializer.data)


class BasePatientListView(ListAPIView):
    """
    Bemorlarni status bo‘yicha filterlaydigan bazaviy klass
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PatientSerializer
    pagination_class = PatientPagination  # Pagination qo‘shildi
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    search_fields = ['full_name', 'phone_number']
    ordering_fields = ['full_name']

    def get_status_queryset(self, status):
        """
        Statusga qarab filterlaydigan umumiy metod
        """
        queryset = Patient.active_patients().filter(status=status).select_related('region',
                                                                                  'type_disease').prefetch_related(
            'appointments')
        search_query = self.request.query_params.get("search", None)

        if search_query:
            queryset = queryset.filter(
                Q(full_name__icontains=search_query) | Q(phone_number__icontains=search_query)
            )

        return queryset


class AllPatientsListView(BasePatientListView):
    """Barcha bemorlarning ro‘yxati (status bo‘yicha ajratilmagan)"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Patient.active_patients().select_related('region', 'type_disease').prefetch_related(
            'appointments').order_by('-created_at')


class DebtorPatientsListView(BasePatientListView):
    """Qarzdor bemorlar ro‘yxati"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.get_status_queryset('debtor').order_by('-created_at')


class UnderTreatmentPatientsListView(BasePatientListView):
    """Hozirda davolanayotgan bemorlar ro‘yxati"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.get_status_queryset('paid').order_by('-created_at')


class TreatedPatientsListView(BasePatientListView):
    """Davolanib bo‘lgan bemorlar ro‘yxati"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.get_status_queryset('treated').order_by('-created_at')


class PatientCreateView(APIView):
    """
    Bemor yaratish API
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PatientCreateSerializer(data=request.data)
        if serializer.is_valid():
            patient = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)  # 🔥 Shu yerda o‘zgarish
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PatientUpdateView(APIView):
    """
    Bemorni yangilash API
    """
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        patient = get_object_or_404(Patient.active_patients(), pk=pk)
        serializer = PatientUpdateSerializer(patient, data=request.data, partial=True)
        if serializer.is_valid():
            patient = serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PatientDeleteView(APIView):
    """
    Faqat superuser uchun bemorni o‘chirish
    """
    permission_classes = [permissions.IsAdminUser]  # Faqat admin (superuser) o‘chira oladi

    def delete(self, request, pk):
        patient = get_object_or_404(Patient, pk=pk)
        patient.delete()
        return Response({"message": "Bemor o‘chirildi"}, status=status.HTTP_204_NO_CONTENT)


class PatientDetailView(APIView):
    """
    Bemorning batafsil ma’lumotlarini qaytaruvchi API
    """

    # permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        patient = get_object_or_404(
            Patient.active_patients().prefetch_related('appointments', 'payments').select_related('region',
                                                                                                  'type_disease'), pk=pk
        )
        serializer = PatientDetailSerializer(patient, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class PatientPaymentCreateView(CreateAPIView):
    """
    Bemor tomonidan amalga oshirilgan yangi to‘lovni kiritish API
    """
    serializer_class = PatientPaymentSerializer

    # permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        patient_id = self.kwargs.get("pk")  # URL orqali patient_id ni olish
        patient = get_object_or_404(Patient.active_patients(), pk=patient_id)  # Agar topilmasa, 404 qaytarish
        serializer.save(patient=patient)  # To‘lovga bemorni qo‘shish
        patient.update_status()  # Qarzni yangilash


class PatientPaymentDeleteView(DestroyAPIView):
    """
    Bemor tomonidan amalga oshirilgan to‘lovni o‘chirish API
    Faqat admin yoki tegishli xodimlar foydalanishi mumkin
    """
    # permission_classes = [IsAuthenticated]
    queryset = PatientPayment.objects.all()
    serializer_class = PatientPaymentSerializer

    def delete(self, request, *args, **kwargs):
        payment = self.get_object()
        patient = payment.patient  # Bemorni olish

        response = super().delete(request, *args, **kwargs)  # To‘lovni o‘chirish

        patient.update_status()  # Qarzni qayta hisoblash
        return response


class UpdatePatientStatusView(APIView):
    """
    Bemorga "treated" statusini berish uchun API
    Faqat to‘liq to‘lagan bemorlar uchun ishlaydi
    """

    # permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        patient = get_object_or_404(Patient.active_patients(), pk=pk)

        if patient.status == 'paid':
            patient.status = 'treated'
            patient.save()
            message = "Bemor davolangan deb belgilandi."
        else:
            message = "Bemor hali qarzdor."

        return Response({"message": message}, status=status.HTTP_200_OK)


class PatientStatisticsView(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        total_patients = Patient.active_patients().count()

        # Default qiymatlar bilan status hisoblash
        status_counts = defaultdict(int, dict(Patient.active_patients().values_list('status').annotate(Count('id'))))

        return Response({
            "total_patients": total_patients,
            "treated": status_counts["treated"],
            "debtor": status_counts["debtor"],
            "paid": status_counts["paid"]
        })


# ertaga kelishi kerak bolgan bemorlar royxati
class TomorrowAppointmentsView(APIView):
    """
    ✅ Ertaga kelishi kerak bo‘lgan bemorlarning ro‘yxatini qaytaradi (uchrashuv vaqti ko‘rsatilmaydi).
    """

    # permission_classes = [IsAuthenticated]

    def get(self, request):
        tomorrow = now().date() + timedelta(days=1)  # Ertangi sana (faqat kun)

        # Ertangi uchrashuvi bor bemorlarni olish
        patients = Patient.active_patients().filter(appointments__appointment_time__date=tomorrow).distinct()

        # JSON formatga o'tkazish
        response_data = PatientSerializer(patients, many=True, context={'request': request}).data

        return Response(response_data)


class TomorrowAppointmentsCountView(APIView):
    """
    ✅ Ertaga kelishi kerak bo‘lgan bemorlarning umumiy sonini optimallashtirilgan tarzda qaytaradi.
    """

    # permission_classes = [IsAuthenticated]

    def get(self, request):
        tomorrow = now().date() + timedelta(days=1)  # Ertangi sana
        patient_count = Appointment.objects.filter(appointment_time__date=tomorrow,
                                                   patient__is_deleted=False).values_list("patient",
                                                                                          flat=True).distinct().count()

        return Response({"tomorrow_patient_count": patient_count})
