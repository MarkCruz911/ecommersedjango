from store.models import Product, ReviewRating

import os
import json
import base64
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt
from ecommerce.forms import CombineImagesForm
from .services.gemini import combine_images

# Necesitas Pillow para trabajar con objetos Image
from PIL import Image
# Necesitas BytesIO para leer datos binarios como si fueran un archivo para PIL
from io import BytesIO


from google.generativeai import GenerativeModel
import google.generativeai as genai

genai.configure(api_key=settings.GEMINI_API_KEY)

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


def get_generative_model():
    return GenerativeModel(
        model_name=settings.GEMINI_MODEL,
        generation_config={
            "response_modalities": ["TEXT", "IMAGE"]
        }
    )

@csrf_exempt
def combine_images(request):
    """Vista para combinar dos imágenes usando la IA de Google Gemini"""
    if request.method == 'POST':
        try:
            image1_file = request.FILES.get('image1')
            # Ahora buscamos la URL de la segunda imagen en POST en lugar de un archivo
            image2_url = request.POST.get('image2_url')
            prompt = request.POST.get('prompt')
            product_id = request.POST.get('product_id')

            # Validar que se recibieron los datos necesarios
            # image1_file es requerido porque es la foto del usuario que siempre se sube
            # image2_url es requerido porque es la prenda del producto
            if not image1_file or not image2_url or not prompt:
                return JsonResponse({'success': False, 'error': 'Faltan la foto de tu persona, la prenda del producto o las instrucciones'})

            # --- Leer el archivo de la primera imagen (persona) como objeto PIL.Image ---
            try:
                img1_pil = Image.open(image1_file)
                if img1_pil.mode != 'RGB':
                     img1_pil = img1_pil.convert('RGB')
            except Exception as e:
                 return JsonResponse({'success': False, 'error': f'Error al procesar tu foto (imagen 1): {str(e)}'})

            # --- Cargar la segunda imagen (prenda del producto) desde la URL ---
            img2_pil = None # Inicializamos a None
            try:
                # Para cargar desde una URL, necesitas hacer una petición HTTP
                import requests
                # Asegúrate de que la URL es válida y la imagen es accesible
                response_img2 = requests.get(image2_url, stream=True)
                response_img2.raise_for_status() # Lanza un error para códigos de estado HTTP erróneos (4xx, 5xx)

                # Usar BytesIO para leer el contenido de la respuesta como si fuera un archivo
                img2_pil = Image.open(BytesIO(response_img2.content))

                if img2_pil.mode != 'RGB':
                     img2_pil = img2_pil.convert('RGB')

            except requests.exceptions.RequestException as e:
                # Error al descargar la imagen de la URL
                return JsonResponse({'success': False, 'error': f'Error al descargar la imagen del producto (imagen 2): {str(e)}'})
            except Exception as e:
                # Error al procesar la imagen descargada con PIL
                 return JsonResponse({'success': False, 'error': f'Error al procesar la imagen del producto descargada: {str(e)}'})

            # Asegurarnos de que ambas imágenes se cargaron correctamente antes de llamar a la API
            if not img1_pil or not img2_pil:
                 return JsonResponse({'success': False, 'error': 'No se pudieron cargar una o ambas imágenes para la combinación.'})


            # --- Llamar al modelo de Google Gemini ---
            model = get_generative_model()

            # --- Estructura del contenido para generate_content usando objetos PIL.Image ---
            contents = [
                prompt,
                img1_pil,   # Primera imagen (la persona)
                img2_pil    # Segunda imagen (la prenda del producto)
            ]

            # --- Puntos de depuración (mantener) ---
            print("\n--- Llamando a la API Gemini ---")
            print(f"Modelo: {settings.GEMINI_MODEL}")
            print(f"Prompt: {prompt[:100]}...")
            print(f"Tamaño Img1 (PIL): {img1_pil.size}, Modo: {img1_pil.mode}")
            print(f"Tamaño Img2 (PIL): {img2_pil.size}, Modo: {img2_pil.mode}")

            response = model.generate_content(contents)

            # --- Puntos de depuración mejorados para la respuesta (mantener) ---
            print("\n--- Respuesta de la API Gemini ---")
            print(f"Tipo de respuesta: {type(response)}")
            if hasattr(response, 'candidates') and response.candidates:
                 print(f"Número de candidatos: {len(response.candidates)}")
                 if len(response.candidates) > 0 and hasattr(response.candidates[0], 'content') and response.candidates[0].content and hasattr(response.candidates[0].content, 'parts'):
                      print(f"Número de partes en el contenido del primer candidato: {len(response.candidates[0].content.parts)}")
                      print("Inspeccionando partes:")
                      for i, part in enumerate(response.candidates[0].content.parts):
                           print(f"  Parte {i}: Tipo = {type(part)}")
                           print(f"    Tiene texto? {hasattr(part, 'text')}")
                           if hasattr(part, 'text'):
                                print(f"      Texto: {part.text[:100]}...")

                           print(f"    Tiene inline_data? {hasattr(part, 'inline_data')}")
                           if hasattr(part, 'inline_data'):
                                print(f"      Valor de part.inline_data: {part.inline_data}")
                                print(f"      inline_data es None? {part.inline_data is None}")
                                if part.inline_data is not None:
                                    print(f"      inline_data tiene mime_type? {hasattr(part.inline_data, 'mime_type')}")
                                    if hasattr(part.inline_data, 'mime_type'):
                                        print(f"      Mime Type: {part.inline_data.mime_type}")
                                    print(f"      inline_data tiene data? {hasattr(part.inline_data, 'data') and part.inline_data.data is not None}")
                                    if hasattr(part.inline_data, 'data') and part.inline_data.data is not None:
                                         print(f"      Tamaño de datos en inline_data: {len(part.inline_data.data)} bytes")
                                    else:
                                         print("      *** inline_data existe pero NO tiene data o data es None ***")
                           # *** FIN MEJORA DEPURACIÓN ***

                 else:
                      print("El primer candidato no tiene contenido o partes en el formato esperado.")
            else:
                 print("La respuesta no tiene candidatos (posiblemente bloqueada por seguridad o error de API).")
                 if hasattr(response, 'prompt_feedback'):
                      print(f"Prompt Feedback: {response.prompt_feedback}")
                 if hasattr(response, 'safety_ratings'):
                      print(f"Safety Ratings: {response.safety_ratings}")

            # --- Procesar la respuesta: Extraer imagen y/o texto ---
            result_image_data = None
            result_text = ""

            if response.candidates and len(response.candidates) > 0 and hasattr(response.candidates[0], 'content') and response.candidates[0].content and hasattr(response.candidates[0].content, 'parts'):
                 for part in response.candidates[0].content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data is not None and hasattr(part.inline_data, 'data') and part.inline_data.data:
                        result_image_data = part.inline_data.data
                        # break

                    if hasattr(part, 'text') and part.text:
                         result_text += part.text

            # --- Guardar la imagen resultante si se generó alguna ---
            if result_image_data:
                 name1 = os.path.splitext(image1_file.name)[0]
                 # Aquí necesitarías un nombre para la segunda imagen, podrías usar el ID del producto
                 name2 = f"product_{product_id}" # Usamos el ID del producto como identificador
                 output_filename = f"combined_image_{product_id}_{name1}_{name2}.png"

                 output_path = default_storage.save(f'combined_images/{output_filename}', ContentFile(result_image_data))

                 image_url = settings.MEDIA_URL + output_path

                 print(f"\n--- Imagen generada guardada en: {image_url} ---")
                 return JsonResponse({'success': True, 'image_url': image_url, 'generated_text': result_text})

            else:
                error_message = 'La IA no generó una imagen en la respuesta o la respuesta fue bloqueada.'
                if result_text:
                     error_message += f' Texto generado: "{result_text[:200]}..."'
                print(f"\n--- No se generó imagen. Mensaje de error: {error_message} ---")
                return JsonResponse({'success': False, 'error': error_message, 'generated_text': result_text})


        except Exception as e:
            # --- Puntos de depuración del error (mantener) ---
            print("\n--- ¡EXCEPCIÓN CAPTURADA! ---")
            print(f"Tipo de excepción: {type(e)}")
            print(f"Mensaje de excepción (str(e)): {str(e)}")
            print(f"Objeto excepción: {e}")
            import traceback
            traceback.print_exc()

            return JsonResponse({'success': False, 'error': f'Ocurrió un error: {type(e).__name__} - {e}'})

    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)




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