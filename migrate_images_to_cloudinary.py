import os
import django
from django.conf import settings
import cloudinary.uploader

# Configura Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecommerce.settings")
django.setup()

from store.models import Product, ProductGallery

# Migrar imágenes de productos
products = Product.objects.all()
for product in products:
    if product.images and os.path.exists(os.path.join(settings.MEDIA_ROOT, str(product.images))):
        # Subir a Cloudinary
        result = cloudinary.uploader.upload(os.path.join(settings.MEDIA_ROOT, str(product.images)))
        # Actualizar la URL en el modelo
        product.images = result['secure_url']
        product.save()

# Migrar galería de productos
gallery_images = ProductGallery.objects.all()
for gallery_image in gallery_images:
    if gallery_image.image and os.path.exists(os.path.join(settings.MEDIA_ROOT, str(gallery_image.image))):
        # Subir a Cloudinary
        result = cloudinary.uploader.upload(os.path.join(settings.MEDIA_ROOT, str(gallery_image.image)))
        # Actualizar la URL en el modelo
        gallery_image.image = result['secure_url']
        gallery_image.save()

print("Migración de imágenes a Cloudinary completada.")