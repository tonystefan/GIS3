"""
Views do módulo de transcrição.
Padrão: views leves que delegam para os services.
HTMX: respostas parciais (partials) para listas e polling de status.
"""
import json
import threading

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from common.mixins import HtmxLoginRequiredMixin
from apps.transcricao.models import Ata, GlossarioTermo, OneDriveToken, TranscricaoJob
from apps.transcricao.services.onedrive_service import OneDriveService

# --------------------------------------------------------------------------- #
# Dashboard de transcrição
# --------------------------------------------------------------------------- #

class IndexView(LoginRequiredMixin, TemplateView):
    template_name = 'transcricao/index.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['jobs'] = TranscricaoJob.objects.filter(user=self.request.user).select_related('ata')
        ctx['onedrive_connected'] = OneDriveService.is_connected(self.request.user)
        return ctx


# --------------------------------------------------------------------------- #
# HTMX: polling de status de um job
# --------------------------------------------------------------------------- #

class JobStatusView(HtmxLoginRequiredMixin, View):
    def get(self, request, pk):
        job = get_object_or_404(TranscricaoJob, pk=pk, user=request.user)
        # Retorna partial HTML com a linha atualizada
        return _render_partial(request, 'transcricao/partials/job_row.html', {'job': job})


# --------------------------------------------------------------------------- #
# HTMX: lista de jobs (refresh completo)
# --------------------------------------------------------------------------- #

class JobListPartialView(HtmxLoginRequiredMixin, View):
    def get(self, request):
        jobs = TranscricaoJob.objects.filter(user=request.user).select_related('ata')
        return _render_partial(request, 'transcricao/partials/job_list.html', {'jobs': jobs})


# --------------------------------------------------------------------------- #
# Detalhe de um job e sua ata
# --------------------------------------------------------------------------- #

class JobDetailView(LoginRequiredMixin, DetailView):
    model = TranscricaoJob
    template_name = 'transcricao/detail.html'
    context_object_name = 'job'

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user).select_related('ata')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        job = self.get_object()
        if hasattr(job, 'ata'):
            try:
                docx_url = OneDriveService.get_item_web_url(self.request.user, job.ata.onedrive_docx_id)
            except Exception:
                docx_url = None
            ctx['docx_url'] = docx_url
        return ctx


# --------------------------------------------------------------------------- #
# OneDrive OAuth
# --------------------------------------------------------------------------- #

class OneDriveConnectView(LoginRequiredMixin, View):
    def get(self, request):
        redirect_uri = request.build_absolute_uri(reverse('transcricao:onedrive_callback'))
        auth_url, flow = OneDriveService.get_auth_url(redirect_uri, state=str(request.user.pk))
        request.session['onedrive_auth_flow'] = flow
        return redirect(auth_url)


class OneDriveCallbackView(LoginRequiredMixin, View):
    def get(self, request):
        flow = request.session.pop('onedrive_auth_flow', None)
        if not flow:
            messages.error(request, 'Sessão de autenticação expirada. Tente novamente.')
            return redirect('transcricao:index')
        redirect_uri = request.build_absolute_uri(reverse('transcricao:onedrive_callback'))
        try:
            OneDriveService.handle_callback(flow, dict(request.GET), request.user, redirect_uri)
            messages.success(request, 'OneDrive conectado com sucesso!')
        except ValueError as e:
            messages.error(request, f'Erro ao conectar OneDrive: {e}')
        return redirect('transcricao:index')


class OneDriveDisconnectView(LoginRequiredMixin, View):
    def post(self, request):
        OneDriveToken.objects.filter(user=request.user).delete()
        messages.success(request, 'OneDrive desconectado.')
        return redirect('transcricao:index')


# --------------------------------------------------------------------------- #
# Browser de arquivos OneDrive (HTMX)
# --------------------------------------------------------------------------- #

class FileBrowserView(HtmxLoginRequiredMixin, View):
    def get(self, request):
        folder_path = request.GET.get('path', '/')
        try:
            files = OneDriveService.list_files(request.user, folder_path)
        except Exception as e:
            return _render_partial(request, 'transcricao/partials/file_list.html', {
                'error': str(e), 'files': [], 'folder_path': folder_path
            })
        return _render_partial(request, 'transcricao/partials/file_list.html', {
            'files': files, 'folder_path': folder_path, 'error': None
        })


# --------------------------------------------------------------------------- #
# Criar job de transcrição
# --------------------------------------------------------------------------- #

class JobCreateView(LoginRequiredMixin, View):
    """Cria job via upload direto de arquivo."""
    def post(self, request):
        audio_file = request.FILES.get('audio_file')

        if not audio_file:
            messages.error(request, 'Nenhum arquivo selecionado.')
            return redirect('transcricao:index')

        ext = audio_file.name.rsplit('.', 1)[-1].lower() if '.' in audio_file.name else ''
        formatos_aceitos = {'mp3', 'mp4', 'm4a', 'wav', 'ogg', 'webm', 'flac', 'aac', 'wma'}
        if ext not in formatos_aceitos:
            messages.error(request, f'Formato .{ext} não suportado. Use: {", ".join(sorted(formatos_aceitos))}')
            return redirect('transcricao:index')

        job = TranscricaoJob.objects.create(
            user=request.user,
            origem=TranscricaoJob.ORIGEM_UPLOAD,
            audio_file=audio_file,
            onedrive_file_name=audio_file.name,
        )
        _trigger_processing(job)
        messages.success(request, f'"{audio_file.name}" enviado. Processamento iniciado.')
        return redirect('transcricao:job_detail', pk=job.pk)


class JobCreateOneDriveView(LoginRequiredMixin, View):
    """Cria job a partir de arquivo selecionado no OneDrive."""
    def post(self, request):
        file_id = request.POST.get('file_id')
        file_name = request.POST.get('file_name')
        folder_path = request.POST.get('folder_path', '/')

        if not file_id or not file_name:
            messages.error(request, 'Arquivo não selecionado.')
            return redirect('transcricao:index')

        job = TranscricaoJob.objects.create(
            user=request.user,
            origem=TranscricaoJob.ORIGEM_ONEDRIVE,
            onedrive_file_id=file_id,
            onedrive_file_name=file_name,
            onedrive_folder_path=folder_path,
        )
        _trigger_processing(job)
        messages.success(request, f'Job criado para "{file_name}". Processamento iniciado.')
        return redirect('transcricao:job_detail', pk=job.pk)


# --------------------------------------------------------------------------- #
# Glossário CRUD
# --------------------------------------------------------------------------- #

class GlossarioView(LoginRequiredMixin, TemplateView):
    template_name = 'transcricao/glossario.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['termos'] = GlossarioTermo.objects.all().order_by('categoria', 'termo_correto')
        ctx['categorias'] = GlossarioTermo.CATEGORIAS
        return ctx


class GlossarioCreateView(LoginRequiredMixin, View):
    def post(self, request):
        termo = request.POST.get('termo_correto', '').strip()
        variantes_raw = request.POST.get('variantes', '').strip()
        categoria = request.POST.get('categoria', 'outro')
        descricao = request.POST.get('descricao', '').strip()

        if not termo:
            return _htmx_error(request, 'Termo não pode ser vazio.')

        variantes = [v.strip() for v in variantes_raw.split(',') if v.strip()]
        GlossarioTermo.objects.create(
            termo_correto=termo,
            variantes=variantes,
            categoria=categoria,
            descricao=descricao,
        )

        termos = GlossarioTermo.objects.all().order_by('categoria', 'termo_correto')
        return _render_partial(request, 'transcricao/partials/glossario_table.html', {
            'termos': termos, 'categorias': GlossarioTermo.CATEGORIAS
        })


class GlossarioDeleteView(LoginRequiredMixin, View):
    def delete(self, request, pk):
        termo = get_object_or_404(GlossarioTermo, pk=pk)
        termo.delete()
        termos = GlossarioTermo.objects.all().order_by('categoria', 'termo_correto')
        return _render_partial(request, 'transcricao/partials/glossario_table.html', {
            'termos': termos, 'categorias': GlossarioTermo.CATEGORIAS
        })


# --------------------------------------------------------------------------- #
# Download do .docx gerado sob demanda
# --------------------------------------------------------------------------- #

class DownloadDocxView(LoginRequiredMixin, View):
    def get(self, request, pk):
        job = get_object_or_404(TranscricaoJob, pk=pk, user=request.user)
        if not hasattr(job, 'ata'):
            return HttpResponse('Ata não disponível.', status=404)

        from apps.transcricao.services.docx_service import DocxService
        docx_bytes = DocxService.gerar_ata_docx(job.ata)

        base_name = job.nome_arquivo.rsplit('.', 1)[0]
        filename = f'Ata_{job.ata.data_reuniao}_{base_name}.docx'

        response = HttpResponse(
            docx_bytes,
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


# --------------------------------------------------------------------------- #
# Endpoint cron (processo jobs via Vercel Cron ou cron externo)
# --------------------------------------------------------------------------- #

class CronProcessView(View):
    """
    Chamado por Vercel Cron Jobs (header Authorization: Bearer <CRON_SECRET>)
    ou manualmente via ?secret= para testes.
    """

    def get(self, request):
        if not self._authorized(request):
            return HttpResponse(status=403)

        from apps.transcricao.services.processing_service import process_pending
        count = process_pending(limit=1)
        return JsonResponse({'processed': count})

    def _authorized(self, request) -> bool:
        if not settings.CRON_SECRET:
            return False
        # Vercel injeta: Authorization: Bearer <CRON_SECRET>
        auth_header = request.headers.get('Authorization', '')
        if auth_header == f'Bearer {settings.CRON_SECRET}':
            return True
        # Fallback para testes manuais: ?secret=
        return request.GET.get('secret', '') == settings.CRON_SECRET


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _trigger_processing(job: TranscricaoJob):
    """Dispara o processamento do job em background thread (desenvolvimento e Vercel)."""
    from apps.transcricao.services.processing_service import process_job
    from django.db import connection

    def run():
        connection.close()  # cada thread precisa de sua própria conexão
        process_job(job)

    t = threading.Thread(target=run, daemon=True)
    t.start()


def _render_partial(request, template_name: str, context: dict) -> HttpResponse:
    from django.template.loader import render_to_string
    html = render_to_string(template_name, context, request=request)
    return HttpResponse(html)


def _htmx_error(request, message: str) -> HttpResponse:
    return HttpResponse(
        f'<div class="text-red-600 text-sm p-2">{message}</div>',
        status=422,
    )
