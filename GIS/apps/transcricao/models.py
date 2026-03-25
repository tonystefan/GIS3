from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from common.models import TimeStampedModel


class OneDriveToken(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='onedrive_token')
    access_token = models.TextField()
    refresh_token = models.TextField()
    expires_at = models.DateTimeField()

    class Meta:
        verbose_name = 'Token OneDrive'
        verbose_name_plural = 'Tokens OneDrive'

    def __str__(self):
        return f'OneDrive token — {self.user.username}'

    def is_expired(self):
        return timezone.now() >= self.expires_at

    def is_connected(self):
        return bool(self.access_token)


class GlossarioTermo(TimeStampedModel):
    CATEGORIAS = [
        ('tecelagem', 'Tecelagem'),
        ('urdimento', 'Urdimento'),
        ('acabamento', 'Acabamento'),
        ('malharia', 'Malharia'),
        ('tinturaria', 'Tinturaria'),
        ('manutencao', 'Manutenção'),
        ('qualidade', 'Qualidade'),
        ('gestao', 'Gestão'),
        ('outro', 'Outro'),
    ]

    termo_correto = models.CharField(max_length=200, verbose_name='Termo correto')
    variantes = models.JSONField(
        default=list,
        help_text='Lista de variações fonéticas ou escritas incorretas. Ex: ["urdidúra", "urdidura"]',
        verbose_name='Variantes fonéticas',
    )
    categoria = models.CharField(max_length=50, choices=CATEGORIAS, default='outro')
    descricao = models.TextField(blank=True, verbose_name='Descrição/contexto')
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Termo do Glossário'
        verbose_name_plural = 'Termos do Glossário'
        ordering = ['categoria', 'termo_correto']

    def __str__(self):
        return self.termo_correto


class TranscricaoJob(TimeStampedModel):
    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Aguardando'),
        (STATUS_PROCESSING, 'Processando'),
        (STATUS_COMPLETED, 'Concluído'),
        (STATUS_FAILED, 'Falha'),
    ]

    ORIGEM_UPLOAD = 'upload'
    ORIGEM_ONEDRIVE = 'onedrive'
    ORIGEM_CHOICES = [
        (ORIGEM_UPLOAD, 'Upload direto'),
        (ORIGEM_ONEDRIVE, 'OneDrive'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transcricao_jobs')
    # Origem do arquivo
    origem = models.CharField(max_length=20, choices=ORIGEM_CHOICES, default=ORIGEM_UPLOAD)
    audio_file = models.FileField(upload_to='audios/', null=True, blank=True, verbose_name='Arquivo de áudio (upload)')
    # Campos OneDrive (opcional)
    onedrive_file_id = models.CharField(max_length=500, blank=True, verbose_name='ID do arquivo no OneDrive')
    onedrive_file_name = models.CharField(max_length=500, blank=True, verbose_name='Nome do arquivo')
    onedrive_folder_path = models.CharField(max_length=1000, blank=True, verbose_name='Pasta de origem')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)
    transcricao_raw = models.TextField(blank=True, verbose_name='Transcrição bruta (Whisper)')
    transcricao_processada = models.TextField(blank=True, verbose_name='Transcrição com glossário aplicado')
    erro = models.TextField(blank=True, verbose_name='Mensagem de erro')
    duracao_segundos = models.IntegerField(null=True, blank=True, verbose_name='Duração do áudio (s)')
    tokens_usados = models.IntegerField(null=True, blank=True, verbose_name='Tokens OpenAI usados')
    iniciado_em = models.DateTimeField(null=True, blank=True)
    concluido_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Job de Transcrição'
        verbose_name_plural = 'Jobs de Transcrição'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.nome_arquivo} ({self.get_status_display()})'

    @property
    def nome_arquivo(self):
        """Nome do arquivo independente da origem."""
        if self.origem == self.ORIGEM_UPLOAD and self.audio_file:
            return self.audio_file.name.split('/')[-1]
        return self.onedrive_file_name or '—'

    @property
    def duracao_formatada(self):
        if not self.duracao_segundos:
            return '—'
        m, s = divmod(self.duracao_segundos, 60)
        h, m = divmod(m, 60)
        if h:
            return f'{h}h {m}min'
        return f'{m}min {s}s'


class Ata(TimeStampedModel):
    job = models.OneToOneField(TranscricaoJob, on_delete=models.CASCADE, related_name='ata')
    titulo = models.CharField(max_length=300, verbose_name='Título da reunião')
    data_reuniao = models.DateField(verbose_name='Data da reunião')
    local = models.CharField(max_length=200, blank=True, verbose_name='Local')
    participantes = models.TextField(blank=True, verbose_name='Participantes')
    pauta = models.TextField(blank=True, verbose_name='Pauta')
    deliberacoes = models.TextField(blank=True, verbose_name='Deliberações')
    acoes = models.JSONField(
        default=list,
        verbose_name='Ações',
        help_text='Lista de {acao, responsavel, prazo}',
    )
    conteudo_completo = models.TextField(blank=True, verbose_name='Ata completa formatada')
    onedrive_docx_id = models.CharField(max_length=500, blank=True, verbose_name='ID do .docx no OneDrive')
    onedrive_docx_path = models.CharField(max_length=1000, blank=True, verbose_name='Caminho do .docx')

    class Meta:
        verbose_name = 'Ata'
        verbose_name_plural = 'Atas'
        ordering = ['-data_reuniao']

    def __str__(self):
        return f'{self.titulo} — {self.data_reuniao}'
