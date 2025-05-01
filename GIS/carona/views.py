from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic.edit import UpdateView, CreateView, DeleteView
from django.views.generic.base import TemplateView
from django.db.models import Sum, Count, Q

import datetime
from .models import(
    Carona,
    Participante
)
from .forms import(
    CaronaForm,
)



def distancia_total(self):
    """Calculate total distance based on route and direction."""
    if self.direction == 'round_trip':
        return float(self.rota.distancia) * 2
    return float(self.rota.distancia)


def viagem_custo(self):
    """Calculate fuel cost for this carpool."""        
    custo_km = self.distancia_total / float(self.veiculo.consumo)
    return round(custo_km * float(self.preco_km), 2)


def custo_por_pessoa(self):
    """Calculate cost per person for this carpool."""
    participantes_count = self.participantes.count() + 1  # +1 for the driver
    if participantes_count <= 1:
        return self.viagem_custo
    return round(self.viagem_custo / participantes_count, 2)

# Create your views here.

class Index(TemplateView):
    template_name = 'carona/index.html'
    
    def get(self, *args, **kwargs):
        context = {}    
        context['carona_list'] = Carona.objects.filter()
        return render(self.request, self.template_name, context)


class ParticipantesUso(TemplateView):
    template_name = 'carona/participantes_uso.html'
    
    def get(self, *args, **kwargs):
        context = {}    
        lista_pessoas3 = Participante.objects.filter().values('pessoa__nome').annotate(soma_preco=Sum('carona__preco_km'))
        lista_pessoas = Participante.objects.filter().order_by('pessoa')
        lista = ()
        


        context['pessoa_list'] = lista_pessoas
        return render(self.request, self.template_name, context)


class CaronaCreate(CreateView):
    model = Carona
    template_name = 'carona/carona_form.html'
    form_class = CaronaForm    

    def get_initial(self, *args, **kwargs):
        initial = super(CaronaCreate, self).get_initial(**kwargs)             
        initial['data'] = datetime.date.today()        
        return initial
    
    def form_valid(self, form):
        self.object = form.save(commit=False)        
        self.object.save()
        participantes = form.cleaned_data.get('participants', [])
        for participante in participantes:
            Participante.objects.create(carona=self.object, pessoa=participante)
        participante.save()        
        return HttpResponseRedirect(f'/index')


