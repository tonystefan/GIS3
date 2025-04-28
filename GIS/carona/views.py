from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic.edit import UpdateView, CreateView, DeleteView
from .models import(
    Carona,
    Participante
)
from .forms import(
    CaronaForm,
)


# Create your views here.

def index(request):

    # Page from the theme 
    return render(request, 'carona/index.html')

class CaronaCreate(CreateView):
    model = Carona
    template_name = 'carona/carona_form.html'
    form_class = CaronaForm    
    
    def form_valid(self, form):
        self.object = form.save(commit=False)        
        self.object.save()
        participantes = form.cleaned_data.get('participantes', [])
        for participante in participantes:
            Participante.objects.create(carona=self.object.carona, pessoa=participante)
        participantes.save()
        return HttpResponseRedirect(f'/carona/index/')


