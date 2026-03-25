"""
Serviço central de processamento de jobs de transcrição.
Usado pelo management command, pela view (thread local) e pelo cron (Vercel).
"""
import logging
import traceback
from datetime import timedelta

from django.utils import timezone

from apps.transcricao.models import TranscricaoJob
from apps.transcricao.services.onedrive_service import OneDriveService
from apps.transcricao.services.whisper_service import WhisperService
from apps.transcricao.services.ata_service import AtaService
from apps.transcricao.services.docx_service import DocxService

logger = logging.getLogger(__name__)

OUTPUT_FOLDER = '/Transcrições/Atas'


def process_job(job: TranscricaoJob) -> bool:
    """
    Processa um job de transcrição.
    Retorna True se concluído com sucesso, False se falhou.
    """
    logger.info('Job #%s: iniciando processamento (%s)', job.pk, job.nome_arquivo)

    job.status = TranscricaoJob.STATUS_PROCESSING
    job.iniciado_em = timezone.now()
    job.erro = ''
    job.save(update_fields=['status', 'iniciado_em', 'erro'])

    try:
        # 1. Obter bytes do áudio
        if job.origem == TranscricaoJob.ORIGEM_UPLOAD:
            logger.info('Job #%s: 1/5 lendo arquivo enviado', job.pk)
            with job.audio_file.open('rb') as f:
                audio_bytes = f.read()
            filename = job.nome_arquivo
        else:
            logger.info('Job #%s: 1/5 baixando do OneDrive', job.pk)
            audio_bytes = OneDriveService.download_file(job.user, job.onedrive_file_id)
            filename = job.onedrive_file_name

        # 2. Transcrição com Whisper
        logger.info('Job #%s: 2/5 transcrevendo com Whisper (Groq)', job.pk)
        glossario_prompt = WhisperService.build_glossary_prompt()
        result = WhisperService.transcribe(audio_bytes, filename, glossario_prompt)

        job.transcricao_raw = result['text']
        job.duracao_segundos = result.get('duration_seconds')
        job.save(update_fields=['transcricao_raw', 'duracao_segundos'])

        # 3. Aplicar glossário
        logger.info('Job #%s: 3/5 aplicando glossário', job.pk)
        transcricao_processada = WhisperService.apply_glossary(result['text'])
        job.transcricao_processada = transcricao_processada
        job.save(update_fields=['transcricao_processada'])

        # 4. Estruturar ata com LLaMA
        logger.info('Job #%s: 4/5 gerando ata com LLaMA (Groq)', job.pk)
        dados_ata, tokens = AtaService.estruturar_ata(transcricao_processada, job)
        ata = AtaService.criar_ata(job, dados_ata)
        job.tokens_usados = (job.tokens_usados or 0) + tokens
        job.save(update_fields=['tokens_usados'])

        # 5. Gerar .docx
        logger.info('Job #%s: 5/5 gerando .docx', job.pk)
        docx_bytes = DocxService.gerar_ata_docx(ata)
        _salvar_docx_local(ata, job, docx_bytes)

        job.status = TranscricaoJob.STATUS_COMPLETED
        job.concluido_em = timezone.now()
        job.save(update_fields=['status', 'concluido_em'])
        logger.info('Job #%s: concluído com sucesso', job.pk)
        return True

    except Exception as e:
        job.status = TranscricaoJob.STATUS_FAILED
        job.erro = traceback.format_exc()
        job.concluido_em = timezone.now()
        job.save(update_fields=['status', 'erro', 'concluido_em'])
        logger.error('Job #%s: falhou — %s', job.pk, e)
        return False


def process_pending(limit: int = 1) -> int:
    """
    Processa jobs pendentes (reseta travados há >1h antes).
    Retorna o número de jobs processados.
    """
    stuck_cutoff = timezone.now() - timedelta(hours=1)
    TranscricaoJob.objects.filter(
        status=TranscricaoJob.STATUS_PROCESSING,
        iniciado_em__lt=stuck_cutoff,
    ).update(status=TranscricaoJob.STATUS_PENDING, iniciado_em=None)

    jobs = (
        TranscricaoJob.objects.filter(status=TranscricaoJob.STATUS_PENDING)
        .select_related('user')
        .order_by('created_at')[:limit]
    )

    count = 0
    for job in jobs:
        process_job(job)
        count += 1
    return count


def _salvar_docx_local(ata, job, docx_bytes: bytes):
    import os
    from django.conf import settings as django_settings

    base_name = job.nome_arquivo.rsplit('.', 1)[0]
    docx_filename = f'Ata_{ata.data_reuniao}_{base_name}.docx'
    docx_dir = os.path.join(django_settings.MEDIA_ROOT, 'atas')
    os.makedirs(docx_dir, exist_ok=True)
    docx_path = os.path.join(docx_dir, docx_filename)
    with open(docx_path, 'wb') as f:
        f.write(docx_bytes)
    ata.onedrive_docx_path = f'atas/{docx_filename}'
    ata.save(update_fields=['onedrive_docx_path'])
