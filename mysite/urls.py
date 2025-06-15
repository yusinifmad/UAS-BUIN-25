# mysite/urls.py

from django.contrib import admin
from django.urls import path, include  # pastikan 'include' diimpor
from bi import views as bi_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('bi/', include('bi.urls')),  # Menambahkan URL dari aplikasi 'bi'
]
