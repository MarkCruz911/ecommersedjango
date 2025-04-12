# ecommerce/services/gemini.py

from google import genai
from django.conf import settings

# Inicializa el cliente una sola vez
client = genai.Client(api_key=settings.GEMINI_API_KEY)

def get_generative_model():
    # Devuelve un helper para llamar a generate_content con tu modelo por defecto
    def generate(contents):
        return client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=contents
        )
    return generate

def combine_images(prompt: str, image_bytes1: bytes, image_bytes2: bytes) -> bytes:
    """
    prompt: texto
    image_bytes1/2: base64 bytes (sin encabezado data:image/png;base64,)
    """
    generate = get_generative_model()

    # La API de google-genai acepta contents como lista de dicts
    contents = [
        {"text": prompt},
        {"image": image_bytes1},
        {"image": image_bytes2},
    ]

    response = generate(contents=contents)

    # Según la respuesta de google-genai, la parte image viene en response.images
    # response.images es lista de dicts con 'image' en base64
    if not getattr(response, "images", None):
        raise ValueError("No se recibió ninguna imagen generada")

    # Tomamos la primera imagen generada
    b64data = response.images[0]["image"]  # ya es str base64

    return b64data.encode("utf-8")
