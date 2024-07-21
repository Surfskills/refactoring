import boto3
from django.conf import settings
from django.db import models

class FileUpload(models.Model):
    """
    Model representing a file upload.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    unique_id = models.CharField(max_length=10, unique=True)
    file = models.FileField(upload_to='uploads/', null=True, blank=True)
    banner = models.FileField(upload_to='uploads/', null=True, blank=True)
    s3_download_link = models.URLField(max_length=500, blank=True, null=True)
    metadata_link = models.URLField(max_length=500, blank=True, null=True)
    expires_at = models.DateTimeField()
    title = models.CharField(max_length=255)
    message = models.TextField()
    request_payment = models.BooleanField(default=False)
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    payment_link = models.URLField(max_length=200, null=True, blank=True)

    def __str__(self):
        """
        String representation of the FileUpload model.
        """
        return self.title or "No Title"

    def generate_s3_download_url(self):
        """
        Generate a presigned S3 URL for the file.
        """
        s3_client = boto3.client('s3',
                                 aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                                 aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                                 region_name=settings.AWS_S3_REGION_NAME)
        try:
            presigned_url = s3_client.generate_presigned_url('get_object',
                                                             Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                                                                     'Key': self.file.name},
                                                             ExpiresIn=3600)  # URL valid for 1 hour
            return presigned_url
        except Exception as e:
            print(f"Error generating S3 presigned URL: {e}")
            return None

    def generate_metadata_link(self):
        """
        Generate a metadata link for the file.
        """
        return f'http://localhost:8000/files_app/files/download/{self.unique_id}/'

    def save(self, *args, **kwargs):
        """
        Override save method to generate S3 and metadata links if not provided.
        """
        if not self.s3_download_link:
            self.s3_download_link = self.generate_s3_download_url()
        if not self.metadata_link:
            self.metadata_link = self.generate_metadata_link()
        super(FileUpload, self).save(*args, **kwargs)

class BuyerInfo(models.Model):
    """
    Model representing buyer information for a file upload.
    """
    file_upload = models.ForeignKey(FileUpload, related_name='buyer_info', on_delete=models.CASCADE)
    buyer_email = models.EmailField(max_length=255, blank=True, null=True)
    buyer_name = models.CharField(max_length=255, blank=True, null=True)
    requirements = models.TextField(null=True, blank=True)
    payment_status = models.CharField(max_length=50, blank=True, null=True)
    payment_link = models.URLField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    order_status = models.CharField(max_length=50, blank=True, null=True)
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def __str__(self):
        """
        String representation of the BuyerInfo model.
        """
        return f"{self.buyer_name} ({self.buyer_email}) for {self.file_upload.unique_id}"

    def initiate_payment(self, payment_amount, callback_url):
        """
        Initiate a Paystack transaction for the buyer.
        """
        from payments.views import initiate_paystack_transaction  # Import here to avoid circular import
        try:
            payment_link = initiate_paystack_transaction(
                self.file_upload, 
                payment_amount, 
                self.buyer_email, 
                callback_url
            )
            self.payment_link = payment_link
            self.save()
            return payment_link
        except Exception as e:
            raise Exception(f"Failed to initiate Paystack transaction: {str(e)}")
