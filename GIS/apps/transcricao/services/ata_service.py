"""
Ata service: estrutura a transcrição bruta em uma ata formal usando
Groq + LLaMA 3.3 70B (rápido, gratuito, excelente em português).
"""
import json
from datetime import date

from django.conf import settings
from groq import Groq

from apps.transcricao.models import Ata, TranscricaoJob

ATA_SYSTEM_PROMPT = """Você é um assistente especializado em redigir atas de reuniões formais para indústrias têxteis brasileiras.

Dado o texto transcrito de uma reunião, extraia e estruture as informações no formato JSON abaixo.
Seja fiel ao conteúdo, use linguagem formal e corrija imprecisões gramaticais da fala.

Formato de resposta (JSON puro, sem markdown):
{
  "titulo": "string — título descritivo da reunião",
  "data_reuniao": "YYYY-MM-DD — se não mencionada, use null",
  "local": "string — local da reunião, ou '' se não mencionado",
  "participantes": "string — lista de nomes separados por vírgula ou quebra de linha",
  "pauta": "string — tópicos da pauta, um por linha",
  "deliberacoes": "string — decisões tomadas, em formato de lista numerada",
  "acoes": [
    {"acao": "string", "responsavel": "string", "prazo": "string"}
  ],
  "conteudo_completo": "string — ata completa e formatada em texto corrido, pronta para uso oficial"
}
"""


class AtaService:

    @staticmethod
    def estruturar_ata(transcricao: str, job: TranscricaoJob) -> tuple[dict, int]:
        """
        Usa Groq LLaMA 3.3 70B para estruturar a transcrição em campos da ata.
        Retorna (dados_dict, tokens_usados).
        """
        client = Groq(api_key=settings.GROQ_API_KEY)

        user_content = (
            f"Arquivo: {job.onedrive_file_name}\n\n"
            f"TRANSCRIÇÃO DA REUNIÃO:\n{transcricao[:12000]}"
        )

        response = client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=[
                {'role': 'system', 'content': ATA_SYSTEM_PROMPT},
                {'role': 'user', 'content': user_content},
            ],
            response_format={'type': 'json_object'},
            temperature=0.2,
        )

        raw = response.choices[0].message.content
        tokens_usados = response.usage.total_tokens if response.usage else 0

        try:
            dados = json.loads(raw)
        except json.JSONDecodeError:
            dados = {
                'titulo': job.onedrive_file_name,
                'data_reuniao': None,
                'local': '',
                'participantes': '',
                'pauta': '',
                'deliberacoes': '',
                'acoes': [],
                'conteudo_completo': transcricao,
            }

        return dados, tokens_usados

    @staticmethod
    def criar_ata(job: TranscricaoJob, dados: dict) -> Ata:
        """Cria o objeto Ata no banco com os dados estruturados."""
        data_reuniao_str = dados.get('data_reuniao')
        if data_reuniao_str:
            try:
                from datetime import datetime
                data_reuniao = datetime.strptime(data_reuniao_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                data_reuniao = date.today()
        else:
            data_reuniao = date.today()

        ata, _ = Ata.objects.update_or_create(
            job=job,
            defaults={
                'titulo': dados.get('titulo') or job.onedrive_file_name,
                'data_reuniao': data_reuniao,
                'local': dados.get('local', ''),
                'participantes': dados.get('participantes', ''),
                'pauta': dados.get('pauta', ''),
                'deliberacoes': dados.get('deliberacoes', ''),
                'acoes': dados.get('acoes', []),
                'conteudo_completo': dados.get('conteudo_completo', ''),
            }
        )
        return ata
