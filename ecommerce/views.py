import numpy as np
from django.shortcuts import render
from store.models import Product, ReviewRating
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

def home(request):
    products = Product.objects.all().filter(is_available=True).order_by('created_date')

    product_data = []
    for product in products:
        price = product.price
        stock = product.stock
        product_data.append([price, stock])

    # Convertir los datos a una matriz de NumPy
    product_data = np.array(product_data)

    # Escalar los datos para normalizar (esto es importante para KMeans)
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(product_data)

    # Aplicar K-means clustering
    kmeans = KMeans(n_clusters=3, random_state=42)
    kmeans.fit(scaled_data)

    # Obtener los labels (clusters) de los productos
    product_clusters = kmeans.labels_

    # Agregar el cluster a cada producto
    for i, product in enumerate(products):
        product.cluster = product_clusters[i]

    # Obtener las reseñas para cada producto
    product_reviews = {}
    for product in products:
        avg_rating = product.averageReview()
        review_count = product.countReview()
        product_reviews[product.id] = {
            'avg_rating': avg_rating,
            'review_count': review_count
        }

    # Obtener clústeres únicos
    unique_clusters = list(set(product_clusters))


    # Crear el contexto para pasar a la plantilla
    context = {
        'products': products,
        'unique_clusters': unique_clusters,
        'product_reviews': product_reviews,
    }

    return render(request, 'home.html', context)
