from rest_framework import serializers
from .models import BuyerInfo, FileUpload

class BuyerInfoSerializer(serializers.ModelSerializer):
    """
    Serializer for BuyerInfo model.
    """
    class Meta:
        model = BuyerInfo
        fields = [
            'id', 
            'file_upload', 
            'buyer_email', 
            'buyer_name', 
            'requirements', 
            'payment_status', 
            'payment_link', 
            'created_at', 
            'updated_at', 
            'order_status', 
            'payment_amount'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class FileUploadSerializer(serializers.ModelSerializer):
    """
    Serializer for FileUpload model, includes nested BuyerInfo serializer.
    """
    buyer_info = BuyerInfoSerializer(many=True, read_only=True, source='buyerinfo_set')

    class Meta:
        model = FileUpload
        fields = [
            'id', 'unique_id', 'file', 's3_download_link', 'metadata_link',
            'expires_at', 'title', 'message', 'payment_amount', 'uploaded_at', 'buyer_info', 'banner'
        ]
        read_only_fields = ['id', 'unique_id', 's3_download_link', 'metadata_link', 'uploaded_at']

    def get_download_url(self, obj):
        """
        Method to generate S3 download URL.
        """
        if isinstance(obj, FileUpload):
            return obj.generate_s3_download_url()
        elif isinstance(obj, dict):
            print(f"Expected FileUpload instance but got dict: {obj}")
            return None
        else:
            print(f"Unexpected type: {type(obj)}")
            return None
