from django import forms

from .models import Empresa, Federal, Estadual, Municipal

class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = '__all__'

class FederalForm(forms.ModelForm):
    class Meta:
        model = Federal
        fields = "__all__"

class EstadualForm(forms.ModelForm):
    class Meta:
        model = Estadual
        fields = "__all__"
class MunicipalForm(forms.ModelForm):
    class Meta:
        model = Municipal
        fields = '__all__'
