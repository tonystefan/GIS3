"""
Whisper service: transcrição de áudio via Groq API (whisper-large-v3).
Groq oferece Whisper gratuitamente com latência muito baixa.
Lida com chunking de arquivos > 25MB e injeção de glossário.
"""
import io
import os
import re
import tempfile
from pathlib import Path
from typing import Optional

from django.conf import settings
from groq import Groq

from apps.transcricao.models import GlossarioTermo

MAX_BYTES = 24 * 1024 * 1024  # 24MB (margem de segurança do limite de 25MB)

SUPPORTED_FORMATS = {'.mp3', '.mp4', '.m4a', '.wav', '.ogg', '.webm', '.flac'}

BASE_PROMPT = (
    "Reunião de trabalho em uma fábrica têxtil da região Sul de Minas Gerais. "
    "Os participantes têm sotaque mineiro característico. "
    "Transcreva fielmente o que foi dito, mantendo a fala natural dos participantes. "
)


def _build_glossary_prompt(termos: list) -> str:
    if not termos:
        return BASE_PROMPT
    termos_str = ', '.join(t.termo_correto for t in termos[:80])
    return (
        BASE_PROMPT
        + f"Termos técnicos do setor têxtil que podem aparecer: {termos_str}. "
        "Priorize a grafia correta desses termos quando o contexto indicar."
    )


def _split_audio_pydub(audio_bytes: bytes, filename: str, chunk_duration_ms: int = 10 * 60 * 1000) -> list[tuple[bytes, str]]:
    """Divide áudio em chunks de chunk_duration_ms milissegundos."""
    try:
        from pydub import AudioSegment
    except ImportError:
        raise ImportError("pydub não está instalado. Execute: pip install pydub")

    ext = Path(filename).suffix.lower().lstrip('.')
    with tempfile.NamedTemporaryFile(suffix=f'.{ext}', delete=False) as f:
        f.write(audio_bytes)
        tmp_path = f.name

    try:
        audio = AudioSegment.from_file(tmp_path, format=ext)
        chunks = []
        for i, start in enumerate(range(0, len(audio), chunk_duration_ms)):
            chunk = audio[start:start + chunk_duration_ms]
            buf = io.BytesIO()
            chunk.export(buf, format='mp3')
            chunks.append((buf.getvalue(), f'chunk_{i:03d}.mp3'))
        return chunks
    finally:
        os.unlink(tmp_path)


class WhisperService:

    @staticmethod
    def transcribe(audio_bytes: bytes, filename: str, glossario_prompt: Optional[str] = None) -> dict:
        """
        Transcreve áudio usando Groq Whisper API (whisper-large-v3).
        Divide automaticamente se o arquivo for maior que 24MB.
        Retorna dict com 'text' (str) e 'duration_seconds' (int ou None).
        """
        client = Groq(api_key=settings.GROQ_API_KEY)
        prompt = glossario_prompt or BASE_PROMPT

        if len(audio_bytes) <= MAX_BYTES:
            return WhisperService._transcribe_single(client, audio_bytes, filename, prompt)

        # Arquivo grande: dividir em chunks
        chunks = _split_audio_pydub(audio_bytes, filename)
        texts = []
        for chunk_bytes, chunk_name in chunks:
            result = WhisperService._transcribe_single(client, chunk_bytes, chunk_name, prompt)
            texts.append(result['text'])
        return {
            'text': '\n\n'.join(texts),
            'duration_seconds': None,
        }

    @staticmethod
    def _transcribe_single(client: Groq, audio_bytes: bytes, filename: str, prompt: str) -> dict:
        ext = Path(filename).suffix.lower()
        if ext not in SUPPORTED_FORMATS:
            ext = '.mp3'

        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = Path(filename).stem + ext

        response = client.audio.transcriptions.create(
            file=audio_file,
            model='whisper-large-v3',
            language='pt',
            prompt=prompt,
            response_format='verbose_json',
        )

        duration = int(response.duration) if hasattr(response, 'duration') and response.duration else None
        return {
            'text': response.text,
            'duration_seconds': duration,
        }

    @staticmethod
    def build_glossary_prompt() -> str:
        termos = list(GlossarioTermo.objects.filter(ativo=True))
        return _build_glossary_prompt(termos)

    @staticmethod
    def apply_glossary(text: str) -> str:
        """Substitui variantes fonéticas pelo termo correto."""
        termos = GlossarioTermo.objects.filter(ativo=True)
        result = text
        for termo in termos:
            for variante in (termo.variantes or []):
                if variante and variante.lower() != termo.termo_correto.lower():
                    result = re.sub(
                        re.escape(variante),
                        termo.termo_correto,
                        result,
                        flags=re.IGNORECASE,
                    )
        return result
