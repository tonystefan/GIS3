from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic.edit import UpdateView, CreateView, DeleteView
from django.views.generic.base import TemplateView


import datetime
from .models import(
    Carona,
    Participante
)
from .forms import(
    CaronaForm,
)


# Create your views here.

class Index(TemplateView):
    template_name = 'carona/index.html'
    
    def get(self, *args, **kwargs):
        context = {}    
        context['carona_list'] = Carona.objects.filter()
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
        return HttpResponseRedirect(f'/carona/')


