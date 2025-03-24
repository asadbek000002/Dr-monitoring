from django.urls import path
from .views import PatientCreateView, PatientDetailView, TreatedPatientsListView, UnderTreatmentPatientsListView, \
    PatientDeleteView, PatientUpdateView, DebtorPatientsListView, AllPatientsListView, \
    PatientPaymentCreateView, PatientPaymentDeleteView, UpdatePatientStatusView, PatientStatisticsView

urlpatterns = [
    path('patients/statistics/', PatientStatisticsView.as_view(), name='patient-statistics'),

    path('patients/create/', PatientCreateView.as_view(), name='patient-create'),

    path('patients/treated/', TreatedPatientsListView.as_view(), name='treated-patients'),
    path('patients/under-treatment/', UnderTreatmentPatientsListView.as_view(), name='under-treatment-patients'),
    path('patients/debtor/', DebtorPatientsListView.as_view(), name='debtor-patients'),
    path('patients/all/', AllPatientsListView.as_view(), name='all-patients'),  # Barcha bemorlar API

    path('patients/<int:pk>/', PatientDetailView.as_view(), name='patient-detail'),

    path('patients/update/<int:pk>/', PatientUpdateView.as_view(), name='patient-detail'),

    path('patients/<int:pk>/delete/', PatientDeleteView.as_view(), name='patient-delete'),

    path('patients/<int:pk>/payments/', PatientPaymentCreateView.as_view(), name='patient-payment-create'),
    path('patients/<int:pk>/payments/<int:payment_id>/', PatientPaymentDeleteView.as_view(), name='delete-payment'),

    path('patients/<int:pk>/update-status/', UpdatePatientStatusView.as_view(), name='update-patient-status'),

]
