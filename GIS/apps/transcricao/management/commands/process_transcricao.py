"""
Management command: processa jobs de transcrição pendentes.

Uso:
    python manage.py process_transcricao
    python manage.py process_transcricao --limit 3
    python manage.py process_transcricao --job-id 42
    python manage.py process_transcricao --dry-run
"""
import traceback
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.transcricao.models import TranscricaoJob
from apps.transcricao.services.onedrive_service import OneDriveService
from apps.transcricao.services.whisper_service import WhisperService
from apps.transcricao.services.ata_service import AtaService
from apps.transcricao.services.docx_service import DocxService


OUTPUT_FOLDER = '/Transcrições/Atas'


class Command(BaseCommand):
    help = 'Processa jobs de transcrição pendentes no OneDrive'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=1, help='Número máximo de jobs a processar')
        parser.add_argument('--job-id', type=int, help='Processar job específico por ID')
        parser.add_argument('--dry-run', action='store_true', help='Simular sem processar de fato')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options['limit']
        job_id = options.get('job_id')

        if job_id:
            jobs = TranscricaoJob.objects.filter(pk=job_id)
        else:
            # Evitar re-processar jobs que ficaram travados há mais de 1h
            stuck_cutoff = timezone.now() - timedelta(hours=1)
            TranscricaoJob.objects.filter(
                status=TranscricaoJob.STATUS_PROCESSING,
                iniciado_em__lt=stuck_cutoff,
            ).update(
                status=TranscricaoJob.STATUS_PENDING,
                iniciado_em=None,
            )
            jobs = TranscricaoJob.objects.filter(
                status=TranscricaoJob.STATUS_PENDING
            ).select_related('user').order_by('created_at')[:limit]

        if not jobs.exists():
            self.stdout.write(self.style.SUCCESS('Nenhum job pendente.'))
            return

        for job in jobs:
            self.stdout.write(f'> Job #{job.pk}: {job.nome_arquivo} (usuario: {job.user.username})')
            if dry_run:
                self.stdout.write(self.style.WARNING('  [dry-run] Pulando processamento.'))
                continue
            self._process_job(job)

    def _process_job(self, job: TranscricaoJob):
        job.status = TranscricaoJob.STATUS_PROCESSING
        job.iniciado_em = timezone.now()
        job.erro = ''
        job.save(update_fields=['status', 'iniciado_em', 'erro'])

        try:
            # 1. Obter bytes do áudio (upload local ou OneDrive)
            if job.origem == TranscricaoJob.ORIGEM_UPLOAD:
                self.stdout.write('  1/5 Lendo arquivo enviado...')
                with job.audio_file.open('rb') as f:
                    audio_bytes = f.read()
                filename = job.nome_arquivo
            else:
                self.stdout.write('  1/5 Baixando arquivo do OneDrive...')
                audio_bytes = OneDriveService.download_file(job.user, job.onedrive_file_id)
                filename = job.onedrive_file_name

            # 2. Transcrição com Whisper
            self.stdout.write('  2/5 Transcrevendo com Whisper (Groq)...')
            glossario_prompt = WhisperService.build_glossary_prompt()
            result = WhisperService.transcribe(audio_bytes, filename, glossario_prompt)

            job.transcricao_raw = result['text']
            job.duracao_segundos = result.get('duration_seconds')
            job.save(update_fields=['transcricao_raw', 'duracao_segundos'])

            # 3. Aplicar glossário
            self.stdout.write('  3/5 Aplicando glossário...')
            transcricao_processada = WhisperService.apply_glossary(result['text'])
            job.transcricao_processada = transcricao_processada
            job.save(update_fields=['transcricao_processada'])

            # 4. Estruturar ata com LLaMA (Groq)
            self.stdout.write('  4/5 Gerando ata com LLaMA (Groq)...')
            dados_ata, tokens = AtaService.estruturar_ata(transcricao_processada, job)
            ata = AtaService.criar_ata(job, dados_ata)
            job.tokens_usados = (job.tokens_usados or 0) + tokens
            job.save(update_fields=['tokens_usados'])

            # 5. Gerar .docx e salvar localmente (disponível para download)
            self.stdout.write('  5/5 Gerando .docx...')
            docx_bytes = DocxService.gerar_ata_docx(ata)
            base_name = job.nome_arquivo.rsplit('.', 1)[0]
            docx_filename = f'Ata_{ata.data_reuniao}_{base_name}.docx'

            import os
            from django.conf import settings as django_settings
            docx_dir = os.path.join(django_settings.MEDIA_ROOT, 'atas')
            os.makedirs(docx_dir, exist_ok=True)
            docx_path = os.path.join(docx_dir, docx_filename)
            with open(docx_path, 'wb') as f:
                f.write(docx_bytes)
            ata.onedrive_docx_path = f'atas/{docx_filename}'
            ata.save(update_fields=['onedrive_docx_path'])

            # Concluído
            job.status = TranscricaoJob.STATUS_COMPLETED
            job.concluido_em = timezone.now()
            job.save(update_fields=['status', 'concluido_em'])
            self.stdout.write(self.style.SUCCESS(f'  OK Job #{job.pk} concluido!'))

        except Exception as e:
            job.status = TranscricaoJob.STATUS_FAILED
            job.erro = traceback.format_exc()
            job.concluido_em = timezone.now()
            job.save(update_fields=['status', 'erro', 'concluido_em'])
            self.stdout.write(self.style.ERROR(f'  ERRO: {e}'))
