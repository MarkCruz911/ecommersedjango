from django.urls import path
from . import views
# En urls.py del proyecto principal
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.store, name="store"),
    path('category/<slug:category_slug>/', views.store, name="products_by_category"),
    path('category/<slug:category_slug>/<slug:product_slug>/', views.product_detail, name="product_detail"),
    path('search/', views.search, name='search'),
    path('submit_review/<int:product_id>/', views.submit_review, name='submit_review'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)