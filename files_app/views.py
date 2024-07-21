from django.urls import reverse
from django.http import HttpResponseServerError
from rest_framework import generics, status
from django.shortcuts import get_object_or_404, redirect
from rest_framework.response import Response
from rest_framework.decorators import api_view, APIView
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
from django.utils.crypto import get_random_string
import boto3
from botocore.exceptions import NoCredentialsError, ClientError, ParamValidationError
from .models import BuyerInfo, FileUpload
from .serializers import BuyerInfoSerializer, FileUploadSerializer
from payments.views import initiate_paystack_transaction, verify_paystack_transaction
from django.conf import settings
from rest_framework.permissions import IsAuthenticated

# Helper function to check if an S3 key exists
def check_key_exists(bucket_name, key):
    """
    Check if a key exists in the specified S3 bucket.

    :param bucket_name: Name of the S3 bucket.
    :param key: Key of the S3 object.
    :return: True if the key exists, False otherwise.
    """
    s3_client = boto3.client('s3',
                             aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                             aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                             region_name=settings.AWS_S3_REGION_NAME)
    try:
        s3_client.head_object(Bucket=bucket_name, Key=key)
        return True
    except ClientError:
        return False

# Helper function to generate a presigned URL for S3
def generate_presigned_url(file_upload):
    """
    Generate a presigned URL for the specified file upload.

    :param file_upload: The FileUpload instance.
    :return: A tuple containing the presigned URL and status code.
    """
    s3_client = boto3.client('s3',
                             aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                             aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                             region_name=settings.AWS_S3_REGION_NAME)
    key = file_upload.file.name
    if not check_key_exists(settings.AWS_STORAGE_BUCKET_NAME, key):
        return {"error": "File key does not exist in S3."}, 400
    try:
        presigned_url = s3_client.generate_presigned_url('get_object',
                                                         Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                                                                 'Key': key},
                                                         ExpiresIn=7200)  # URL valid for 2 hours
        return presigned_url, 200
    except NoCredentialsError:
        return {"error": "AWS credentials not available."}, 500
    except ClientError as e:
        return {"error": str(e)}, 500
    except ParamValidationError as e:
        return {"error": str(e)}, 400

# API view for listing and creating file uploads
class FileUploadListCreateAPIView(generics.ListCreateAPIView):
    """
    API view to retrieve list of file uploads or create a new file upload.
    """
    queryset = FileUpload.objects.all()
    serializer_class = FileUploadSerializer
    # permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """
        Perform create operation for FileUpload.
        Sets the expiration date and generates unique ID.
        """
        expires_at = timezone.now() + timezone.timedelta(days=7)  # Set expiration date for 7 days from now
        unique_id = get_random_string(10)  # Generate a random unique ID

        try:
            # Save with additional fields like expires_at and unique_id
            file_upload = serializer.save(
                user=self.request.user,
                expires_at=expires_at,
                unique_id=unique_id
            )

            # Check if payment_amount is in the request data
            if 'payment_amount' in self.request.data:
                payment_amount = Decimal(self.request.data['payment_amount'])
                file_upload.payment_amount = payment_amount
                file_upload.request_payment = True  # Mark that payment is requested

                try:
                    # Call the utility function to initiate the transaction and get the payment link
                    callback_url = self.request.build_absolute_uri(f'/files_app/payment-callback/{unique_id}/')
                    payment_link = initiate_paystack_transaction(file_upload, payment_amount, self.request.user.email, callback_url)
                    file_upload.payment_link = payment_link
                    file_upload.save()  # Save the instance with payment link
                except Exception as e:
                    return Response({"error": "Failed to initiate payment."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Additional processing like generating S3 links and metadata
            if file_upload.file and file_upload.file.name:
                presigned_url, status_code = generate_presigned_url(file_upload)
                if status_code != 200:
                    file_upload.delete()
                    return Response(presigned_url, status=status.HTTP_400_BAD_REQUEST)
                file_upload.s3_download_link = presigned_url
                metadata_link = self.request.build_absolute_uri(f'/files_app/files/download/{unique_id}/')
                file_upload.metadata_link = metadata_link
                file_upload.save()  # Save again after updating links

                return Response({
                    's3_download_link': presigned_url,
                    'metadata_link': metadata_link,
                    'payment_link': file_upload.payment_link,
                    'payment_status': file_upload.payment_status,
                }, status=status.HTTP_201_CREATED)
            else:
                file_upload.delete()
                return Response({"error": "File name is missing or file is not present."}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# API view for retrieving and updating file uploads
class FileUploadDetailAPIView(generics.RetrieveUpdateAPIView):
    """
    API view to retrieve or update a file upload by unique_id.
    """
    queryset = FileUpload.objects.all()
    serializer_class = FileUploadSerializer
    lookup_field = 'unique_id'
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Retrieve a FileUpload instance by unique_id.
        """
        unique_id = kwargs.get('unique_id')
        file_upload = self.get_object()  # Retrieve the FileUpload instance based on unique_id

        if file_upload is None:
            return Response({"error": "File not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(file_upload)
        return Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        """
        Partially update a FileUpload instance.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)  # Use partial=True to allow partial updates
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)

# API view for retrieving and creating buyer information
class BuyerInfoAPIView(APIView):
    """
    API view to retrieve or create BuyerInfo.
    """

    def get(self, request, buyer_info_id):
        """
        Retrieves BuyerInfo by its primary key id.
        """
        try:
            buyer_info = get_object_or_404(BuyerInfo, id=buyer_info_id)
            serializer = BuyerInfoSerializer(buyer_info)
            
            response_data = {
                'id': serializer.data['id'],
                'file_upload': serializer.data['file_upload'],
                'buyer_email': serializer.data['buyer_email'],
                'buyer_name': serializer.data['buyer_name'],
                'requirements': serializer.data['requirements'],
                'payment_status': serializer.data['payment_status'],
                'payment_link': serializer.data['payment_link'],
                'order_status': serializer.data['order_status'],
                'payment_amount': serializer.data['payment_amount'],
                'created_at': serializer.data['created_at'],
                'updated_at': serializer.data['updated_at'],
            }
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": "Buyer information not found."}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, unique_id):
        """
        Creates BuyerInfo using the unique_id of the FileUpload.
        """
        buyer_email = request.data.get('buyer_email')
        buyer_name = request.data.get('buyer_name')
        requirements = request.data.get('requirements', 'No specific requirements.')
        payment_status = request.data.get('payment_status', '')  # Default to empty string if not provided

        try:
            file_upload = get_object_or_404(FileUpload, unique_id=unique_id)

            # Determine the order status based on whether the video has been uploaded
            order_status = 'fulfilled' if file_upload.file else 'fulfil'

            buyer_data = {
                'file_upload': file_upload.id,
                'buyer_email': buyer_email,
                'buyer_name': buyer_name,
                'requirements': requirements,
                'payment_status': payment_status,
                'order_status': order_status,
                'payment_amount': file_upload.payment_amount  # Get payment amount from FileUpload
            }

            # Always create a new buyer instance
            serializer = BuyerInfoSerializer(data=buyer_data)

            if serializer.is_valid():
                buyer_info = serializer.save()

                # Generate payment link if payment is required
                if file_upload.payment_amount:
                    try:
                        callback_url = request.build_absolute_uri(reverse('payment_callback', args=[buyer_info.id]))
                        payment_link = buyer_info.initiate_payment(file_upload.payment_amount, callback_url)
                        buyer_info.payment_link = payment_link
                        buyer_info.save()
                    except Exception as e:
                        return Response({"error": "Failed to initiate payment."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                return Response({"payment_link": buyer_info.payment_link}, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": "File upload not found."}, status=status.HTTP_404_NOT_FOUND)

# API view for listing all buyers
class BuyerInfoListAPIView(generics.ListAPIView):
    """
    API view to list all BuyerInfo instances.
    """
    queryset = BuyerInfo.objects.all()
    serializer_class = BuyerInfoSerializer

    def get(self, request, *args, **kwargs):
        """
        Retrieve list of all BuyerInfo instances.
        """
        return self.list(request, *args, **kwargs)

# API view to verify buyer email and file unique ID
class VerifyBuyerEmailView(APIView):
    """
    API view to verify if a BuyerInfo exists for the given email and file unique_id.
    """
    def post(self, request, unique_id):
        """
        Verifies if a BuyerInfo exists for the given email and file unique_id.
        """
        buyer_email = request.data.get('buyer_email')

        try:
            file_upload = get_object_or_404(FileUpload, unique_id=unique_id)
            buyer_instance = BuyerInfo.objects.filter(buyer_email=buyer_email, file_upload=file_upload).first()

            if buyer_instance:
                data = {
                    "buyer_email": buyer_instance.buyer_email,
                    "payment_status": buyer_instance.payment_status,
                    "file_upload_unique_id": buyer_instance.file_upload.unique_id,
                    "buyer_info_id": buyer_instance.id,
                    "payment_link": buyer_instance.payment_link  # Include the payment link in the response
                }
                return Response(data, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Buyer email not found."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"error": "An error occurred while verifying the buyer email."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# API view for payment callback
@api_view(['GET'])
def payment_callback(request, buyer_info_id):
    """
    Handle payment callback from Paystack.
    """
    buyer_info = get_object_or_404(BuyerInfo, id=buyer_info_id)
    reference = request.GET.get('reference')
    trxref = request.GET.get('trxref')

    try:
        if not reference or not trxref:
            return Response({"error": "Missing 'reference' or 'trxref' in callback request."}, status=status.HTTP_400_BAD_REQUEST)

        success, response_data = verify_paystack_transaction(reference)
        if success:
            buyer_info.payment_status = 'paid'
            buyer_info.save()
            # Redirect to the desired URL on successful payment
            return redirect(f'http://localhost:3001/shared/{buyer_info.file_upload.unique_id}/{buyer_info.id}/')
        
        else:
            buyer_info.payment_status = 'failed'
            buyer_info.save()
            return Response({"error": "Payment failed"}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({"error": "Internal server error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# API view to get a presigned URL for downloading a file
@api_view(['GET'])
def get_presigned_url(request, unique_id):
    """
    Get a presigned URL for the specified file upload.
    """
    if request.method == 'GET':
        file_upload = get_object_or_404(FileUpload, unique_id=unique_id)

        if file_upload.expires_at < timezone.now():
            return Response({"error": "The download link has expired."}, status=status.HTTP_404_NOT_FOUND)

        if file_upload.file and file_upload.file.name:
            presigned_url, status_code = generate_presigned_url(file_upload)
            if status_code != 200:
                return Response(presigned_url, status=status_code)

            file_upload.s3_download_link = presigned_url
            file_upload.save()

            response_data = {
                'title': file_upload.title,
                'message': file_upload.message,
                'expires_at': file_upload.expires_at,
                'presigned_url': presigned_url,
                'payment_amount': file_upload.payment_amount
            }
            return Response(response_data)
        else:
            return Response({"error": "File name is missing or file is not present."}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({"error": "Method not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

# View to redirect to a download page
def download_redirect(request, unique_id):
    """
    Redirect to the download page for the specified file upload.
    """
    try:
        target_url = f'http://localhost:3001/shared/{unique_id}/'
        return redirect(target_url)
    except Exception as e:
        return HttpResponseServerError(f'Error: {e}')

# API view to list file uploads for a specific user
class UserFileUploadListAPIView(generics.ListAPIView):
    """
    API view to list all file uploads for a specific user.
    """
    serializer_class = FileUploadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Get queryset of FileUpload instances for the specified user.
        """
        user_id = self.kwargs['user_id']
        return FileUpload.objects.filter(user_id=user_id)

# API view to list all buyers for a specific file
class FileBuyersListAPIView(generics.ListAPIView):
    """
    API view to list all buyers for a specific file upload.
    """
    serializer_class = BuyerInfoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Get queryset of BuyerInfo instances for the specified file upload.
        """
        file_unique_id = self.kwargs['unique_id']
        return BuyerInfo.objects.filter(file_upload__unique_id=file_unique_id)
