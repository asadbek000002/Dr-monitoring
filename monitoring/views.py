from collections import defaultdict

from django.db.models import Q, Count
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView, CreateAPIView, DestroyAPIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from .models import Patient, PatientPayment
from .serializers import PatientSerializer, PatientCreateSerializer, PatientDetailSerializer, PatientUpdateSerializer, \
    PatientPaymentSerializer
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated


class PatientPagination(PageNumberPagination):
    """
    Bemorlar ro‘yxati uchun pagination
    """
    page_size = 10  # Har bir sahifada 10 ta bemor chiqadi
    page_size_query_param = 'page_size'  # Foydalanuvchi o‘zi sonni belgilashi mumkin
    max_page_size = 100  # Maksimal 100 ta bemor


class BasePatientListView(ListAPIView):
    """
    Bemorlarni status bo‘yicha filterlaydigan bazaviy klass
    """
    serializer_class = PatientSerializer
    pagination_class = PatientPagination  # Pagination qo‘shildi
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    search_fields = ['full_name', 'phone_number']
    ordering_fields = ['full_name']

    def get_status_queryset(self, status):
        """
        Statusga qarab filterlaydigan umumiy metod
        """
        queryset = Patient.objects.filter(status=status).select_related('region', 'type_disease').prefetch_related(
            'appointments')
        search_query = self.request.query_params.get("search", None)

        if search_query:
            queryset = queryset.filter(
                Q(full_name__icontains=search_query) | Q(phone_number__icontains=search_query)
            )

        return queryset


class AllPatientsListView(BasePatientListView):
    """Barcha bemorlarning ro‘yxati (status bo‘yicha ajratilmagan)"""

    def get_queryset(self):
        return Patient.objects.all().select_related('region', 'type_disease').prefetch_related('appointments')


class DebtorPatientsListView(BasePatientListView):
    """Qarzdor bemorlar ro‘yxati"""

    def get_queryset(self):
        return self.get_status_queryset('debtor')


class UnderTreatmentPatientsListView(BasePatientListView):
    """Hozirda davolanayotgan bemorlar ro‘yxati"""

    def get_queryset(self):
        return self.get_status_queryset('paid')


class TreatedPatientsListView(BasePatientListView):
    """Davolanib bo‘lgan bemorlar ro‘yxati"""

    def get_queryset(self):
        return self.get_status_queryset('treated')


class PatientCreateView(APIView):
    """
    Bemor yaratish API
    """

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

    def put(self, request, pk):
        patient = get_object_or_404(Patient, pk=pk)
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

    def get(self, request, pk):
        patient = get_object_or_404(
            Patient.objects.prefetch_related('appointments', 'payments').select_related('region', 'type_disease'), pk=pk
        )
        serializer = PatientDetailSerializer(patient, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class PatientPaymentCreateView(CreateAPIView):
    """
    Bemor tomonidan amalga oshirilgan yangi to‘lovni kiritish API
    """
    serializer_class = PatientPaymentSerializer

    def perform_create(self, serializer):
        patient_id = self.kwargs.get("pk")  # URL orqali patient_id ni olish
        patient = get_object_or_404(Patient, pk=patient_id)  # Agar topilmasa, 404 qaytarish
        serializer.save(patient=patient)  # To‘lovga bemorni qo‘shish
        patient.update_status()  # Qarzni yangilash


class PatientPaymentDeleteView(DestroyAPIView):
    """
    Bemor tomonidan amalga oshirilgan to‘lovni o‘chirish API
    Faqat admin yoki tegishli xodimlar foydalanishi mumkin
    """
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

    def patch(self, request, pk):
        patient = get_object_or_404(Patient, pk=pk)

        if patient.status == 'paid':
            patient.status = 'treated'
            patient.save()
            message = "Bemor davolangan deb belgilandi."
        else:
            message = "Bemor hali qarzdor."

        return Response({"message": message}, status=status.HTTP_200_OK)


class PatientStatisticsView(APIView):
    def get(self, request):
        total_patients = Patient.objects.count()

        # Default qiymatlar bilan status hisoblash
        status_counts = defaultdict(int, dict(Patient.objects.values_list('status').annotate(Count('id'))))

        return Response({
            "total_patients": total_patients,
            "treated": status_counts["treated"],
            "debtor": status_counts["debtor"],
            "paid": status_counts["paid"]
        })
