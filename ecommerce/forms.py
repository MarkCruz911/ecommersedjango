from django import forms

class CombineImagesForm(forms.Form):
    prompt = forms.CharField(widget=forms.Textarea, initial="Cambia la prenda…")
    image1 = forms.ImageField()
    image2 = forms.ImageField()