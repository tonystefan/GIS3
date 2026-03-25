"""
Management command: processa jobs de transcrição pendentes.

Uso:
    python manage.py process_transcricao
    python manage.py process_transcricao --limit 3
    python manage.py process_transcricao --job-id 42
    python manage.py process_transcricao --dry-run
"""
from django.core.management.base import BaseCommand

from apps.transcricao.models import TranscricaoJob
from apps.transcricao.services.processing_service import process_job, process_pending


class Command(BaseCommand):
    help = 'Processa jobs de transcrição pendentes'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=1, help='Número máximo de jobs a processar')
        parser.add_argument('--job-id', type=int, help='Processar job específico por ID')
        parser.add_argument('--dry-run', action='store_true', help='Simular sem processar de fato')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        job_id = options.get('job_id')

        if job_id:
            jobs = TranscricaoJob.objects.filter(pk=job_id)
            if not jobs.exists():
                self.stdout.write(self.style.ERROR(f'Job #{job_id} não encontrado.'))
                return
            for job in jobs:
                self.stdout.write(f'> Job #{job.pk}: {job.nome_arquivo}')
                if not dry_run:
                    ok = process_job(job)
                    style = self.style.SUCCESS if ok else self.style.ERROR
                    self.stdout.write(style(f'  {"OK" if ok else "FALHOU"}'))
        else:
            jobs = TranscricaoJob.objects.filter(status=TranscricaoJob.STATUS_PENDING).order_by('created_at')[:options['limit']]
            if not jobs.exists():
                self.stdout.write(self.style.SUCCESS('Nenhum job pendente.'))
                return
            for job in jobs:
                self.stdout.write(f'> Job #{job.pk}: {job.nome_arquivo}')
                if not dry_run:
                    ok = process_job(job)
                    style = self.style.SUCCESS if ok else self.style.ERROR
                    self.stdout.write(style(f'  {"OK" if ok else "FALHOU"}'))
