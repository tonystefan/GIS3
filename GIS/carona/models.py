from django.db import models
from django.contrib.auth.models import User



class Pessoa(models.Model):    
    id              = models.AutoField(db_column='id',primary_key=True)
    nome         = models.CharField(max_length=100, verbose_name="Nome")        
    user         = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='pessoas', verbose_name="usuario")
    is_active    = models.BooleanField(default=True, verbose_name="Ativo")
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)
    
    class Meta:        
        ordering = ['nome']
    
    def __str__(self):
        return f"{self.nome}"


class Rota(models.Model):
    id              = models.AutoField(db_column='id',primary_key=True)
    nome       = models.CharField(max_length=100, verbose_name="Nome da Rota")
    distancia  = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Distância (km)")
    descricao  = models.TextField(blank=True, null=True, verbose_name="Descrição")
    is_active  = models.BooleanField(default=True, verbose_name="Ativa")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Rotas"        
    
    def __str__(self):
        return f"{self.nome} ({self.distancia} km)"

class Veiculo(models.Model):    
    id              = models.AutoField(db_column='id',primary_key=True)
    proprietario = models.ForeignKey(Pessoa, on_delete=models.CASCADE, related_name='veiculos', verbose_name="Proprietário")
    modelo       = models.CharField(max_length=100, verbose_name="Modelo")    
    consumo      = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Consumo (km/l)")
    capacidade   = models.PositiveSmallIntegerField(default=4, verbose_name="Capacidade")
    is_active    = models.BooleanField(default=True, verbose_name="Ativo")
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Veículo"
        verbose_name_plural = "Veículos"
        ordering = ['modelo', 'proprietario']
    
    def __str__(self):
        return f"{self.modelo} ({self.proprietario})"

class PrecoKM(models.Model):
    id         = models.AutoField(db_column='id',primary_key=True)
    preco      = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Preço KM")
    data       = models.DateField(verbose_name="Data de Vigência")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='precosKM', verbose_name="Criado por")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Preço do Kilometro"
        verbose_name_plural = "Preços de Combustível"
        ordering = ['-data']
    
    def __str__(self):
        return f"R$ {self.preco} (a partir de {self.data})"
    
    @classmethod
    def get_current_price(cls):
        """Get the most recent fuel price."""
        try:
            return cls.objects.order_by('-data').first().preco
        except AttributeError:
            return 5.00  # Default price if no prices are set

class Carona(models.Model):
    DIRECTION_CHOICES = (
        ('one_way', 'Somente Ida'),
        ('round_trip', 'Ida e Volta'),
    )
    id         = models.AutoField(db_column='id',primary_key=True)
    data       = models.DateField(verbose_name="data")
    rota       = models.ForeignKey(Rota, on_delete=models.PROTECT, related_name='caronas', verbose_name="Rota")
    veiculo    = models.ForeignKey(Veiculo, on_delete=models.PROTECT, related_name='caronas', verbose_name="Veículo")
    direction  = models.CharField(max_length=10, choices=DIRECTION_CHOICES, default='round_trip', verbose_name="Direção")
    preco_km   = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Preço KM")
    notes      = models.TextField(blank=True, null=True, verbose_name="Observações")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='caronas', verbose_name="Criado por")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Caronas"
        ordering = ['-data', '-created_at']
    
    def __str__(self):
        return f"Carona em {self.data} - {self.rota.nome} ({self.get_direction_display()})"
    
    def save(self, *args, **kwargs):
        # Set fuel price if not provided
        if not self.preco_km:
            self.preco_km = PrecoKM.objects.latest('data').preco
        super().save(*args, **kwargs)
    
    @property
    def distancia_total(self):
        """Calculate total distance based on route and direction."""
        if self.direction == 'round_trip':
            return float(self.rota.distancia) * 2
        return float(self.rota.distancia)
    
    @property
    def viagem_custo(self):
        """Calculate fuel cost for this carpool."""        
        custo_km = self.distancia_total / float(self.veiculo.consumo)
        return round(custo_km * float(self.preco_km), 2)
    
    @property
    def custo_por_pessoa(self):
        """Calculate cost per person for this carpool."""
        participantes_count = self.participantes.count() + 1  # +1 for the driver
        if participantes_count <= 1:
            return self.viagem_custo
        return round(self.viagem_custo / participantes_count, 2)

class Participante(models.Model):
    """
    Model for participants in a carpool.
    """
    id         = models.AutoField(db_column='id',primary_key=True)
    carona     = models.ForeignKey(Carona, on_delete=models.CASCADE, related_name='participantes', verbose_name="Carona")        
    pessoa       = models.ForeignKey(Pessoa, on_delete=models.CASCADE, related_name='carona_participantes', verbose_name="Participante")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Participante de Carona"
        verbose_name_plural = "Participantes de Carona"
        unique_together = ('carona', 'pessoa')
        ordering = ['carona', 'pessoa']
    
    def __str__(self):
        return f"{self.pessoa} - {self.carona}"

