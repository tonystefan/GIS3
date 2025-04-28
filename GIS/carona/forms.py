from django import forms
from .models import Rota, Veiculo, PrecoKM, Carona, Participante, Pessoa

class CaronaForm(forms.ModelForm):    
    participants = forms.ModelMultipleChoiceField(
        queryset=Pessoa.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Participantes"
    )
    
    class Meta:
        model = Carona
        fields = ['data', 'rota', 'veiculo', 'direction', 'preco_km']
        
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter vehicles by owner if user is provided
        if user:
            self.fields['veiculo'].queryset = Veiculo.objects.filter(proprietario=Pessoa.user, is_active=True)
            
            # Set initial fuel price
            if not self.instance.pk:  # Only for new instances
                self.fields['preco_km'].initial = PrecoKM.get_current_price()
        
        