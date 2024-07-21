from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


# In your main urls.py
api_info = openapi.Info(
    title="TOOMA",
    default_version='v1',
    description="API documentation for Tooma",
    terms_of_service="https://www.google.com/policies/terms/",
    contact=openapi.Contact(email="fred@tooma.app"),
    license=openapi.License(name="BSD License"),
)

SWAGGER_SETTINGS = {
    'DEFAULT_INFO': 'tooma_backend.urls.api_info',
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
    }
}

schema_view = get_schema_view(
    api_info,
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('admin/', admin.site.urls),
    path('auth/', include('authentication.urls')),
    path('files_app/', include('files_app.urls')),
    path('social_auth/', include(('social_auth.urls', 'social_auth'), namespace="social_auth")),
]
