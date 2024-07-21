from django.contrib import admin
from .models import FileUpload, BuyerInfo

from django.contrib import admin
from .models import BuyerInfo

class BuyerInfoInline(admin.TabularInline):
    model = BuyerInfo
    extra = 1
    fields = ('id', 'buyer_email', 'buyer_name', 'requirements', 'payment_status', 'payment_link', 'created_at', 'updated_at', 'order_status', 'payment_amount')
    readonly_fields = ('id', 'payment_status', 'payment_link', 'created_at', 'updated_at')


@admin.register(FileUpload)
class FileUploadAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'file', 'title', 'message', 'payment_amount',
        'uploaded_at', 'expires_at', 's3_download_link_display', 'metadata_link_display', 'banner'
    )
    search_fields = ('user__username', 'file', 'title', 'message')
    list_filter = ('uploaded_at', 'expires_at', 'payment_amount')
    readonly_fields = ('s3_download_link_display', 'metadata_link_display')
    inlines = [BuyerInfoInline]

    def s3_download_link_display(self, obj):
        return obj.s3_download_link if obj.s3_download_link else 'N/A'
    s3_download_link_display.short_description = 'S3 Download Link'

    def metadata_link_display(self, obj):
        return obj.metadata_link if obj.metadata_link else 'N/A'
    metadata_link_display.short_description = 'Metadata Link'

@admin.register(BuyerInfo)
class BuyerInfoAdmin(admin.ModelAdmin):
    list_display = ('id', 'file_upload', 'buyer_email', 'buyer_name', 'payment_status', 'payment_link')
    list_filter = ('payment_status',)
    search_fields = ('buyer_email', 'buyer_name')
    ordering = ('buyer_email',)
