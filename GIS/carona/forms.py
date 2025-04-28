from django import forms
from .models import Rota, Veiculo, PrecoKM, Carona, Participante, Pessoa

class CaronaForm(forms.ModelForm):    
    participantes = forms.ModelMultipleChoiceField(
        queryset=Pessoa.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Participantes"
    )
    
    class Meta:
        model = Carona
        fields = ['data', 'rota', 'veiculo', 'direction', 'preco_km', 'notes']
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter vehicles by owner if user is provided
        if user:
            self.fields['veiculo'].queryset = Veiculo.objects.filter(proprietario=Pessoa.user, is_active=True)
            
            # Set initial fuel price
            if not self.instance.pk:  # Only for new instances
                self.fields['preco_km'].initial = PrecoKM.get_current_price()
        
        # For existing carpools, initialize participants field
        if self.instance.pk:
            self.fields['participants'].initial = Pessoa.objects.filter(
                participantes__carona=self.instance
            )
            