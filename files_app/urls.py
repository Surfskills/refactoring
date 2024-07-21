from django.urls import path
from .views import (
    BuyerInfoAPIView,
    BuyerInfoListAPIView,
    FileUploadListCreateAPIView,
    FileUploadDetailAPIView,
    VerifyBuyerEmailView,
    download_redirect,
    payment_callback,
    get_presigned_url,
    UserFileUploadListAPIView,
    FileBuyersListAPIView,
)

urlpatterns = [
    path('files/', FileUploadListCreateAPIView.as_view(), name='file-upload-list-create'),
    path('files/<unique_id>/', FileUploadDetailAPIView.as_view(), name='file-upload-detail'),
    path('files/download/<str:unique_id>/', download_redirect, name='download_redirect'),
    path('buyers/', BuyerInfoListAPIView.as_view(), name='buyer-info-list'),
    path('buyers/<int:buyer_info_id>/', BuyerInfoAPIView.as_view(), name='buyer-info-detail'),
    path('files/create-buyer-info/<str:unique_id>/', BuyerInfoAPIView.as_view(), name='create_buyer_info'),
    path('files/update-buyer-info/<str:unique_id>/', BuyerInfoAPIView.as_view(), name='update_buyer_info'),
    path('files/verify-buyer-email/<str:unique_id>/', VerifyBuyerEmailView.as_view(), name='verify_buyer_email'),
    path('payment-callback/<int:buyer_info_id>/', payment_callback, name='payment_callback'),
    path('get-presigned-url/<str:unique_id>/', get_presigned_url, name='get-presigned-url'),
    path('user-files/<int:user_id>/', UserFileUploadListAPIView.as_view(), name='user-file-upload-list'),
    path('file-buyers/<str:unique_id>/', FileBuyersListAPIView.as_view(), name='file-buyers-list'),
]
