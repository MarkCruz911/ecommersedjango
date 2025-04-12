from django.shortcuts import render
from store.models import Product, ReviewRating

import base64
from django.http import HttpResponse, JsonResponse
from ecommerce.forms import CombineImagesForm
from .services.gemini import combine_images

def home(request):
    products = Product.objects.all().filter(is_available=True).order_by('created_date')
    reviews=[]
    for product in products:
        reviews = ReviewRating.objects.filter(product_id=product.id, status=True)


    context = {
        'products': products,
        'reviews': reviews,
    }

    return render(request, 'home.html', context)


def projects_ai(request):
    result_data = None
    error = None

    if request.method == "POST":
        form = CombineImagesForm(request.POST, request.FILES)
        if form.is_valid():
            prompt = form.cleaned_data["prompt"]

            # Leer imágenes y convertir a base64 sin cabecera
            img1 = base64.b64encode(request.FILES["image1"].read())
            img2 = base64.b64encode(request.FILES["image2"].read())

            try:
                generated = combine_images(prompt, img1, img2)
                # Prepara data URI para mostrar en template
                result_data = f"data:image/png;base64,{generated.decode('utf-8')}"
            except Exception as e:
                error = str(e)
        else:
            error = "Formulario inválido"
    else:
        form = CombineImagesForm()

    return render(request, "projects_ai.html", {
        "form": form,
        "result": result_data,
        "error": error,
    })