"""
OneDrive service: OAuth MSAL + Microsoft Graph API.
Gerencia autenticação e operações de arquivos no OneDrive pessoal.
"""
import urllib.parse
from datetime import timedelta
from typing import Optional

import httpx
import msal
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone

from apps.transcricao.models import OneDriveToken

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
SCOPES = ["Files.ReadWrite", "offline_access", "User.Read"]

AUDIO_EXTENSIONS = {'.mp3', '.mp4', '.m4a', '.wav', '.ogg', '.webm', '.flac', '.aac', '.wma', '.opus'}


def _get_msal_app():
    return msal.ConfidentialClientApplication(
        client_id=settings.AZURE_CLIENT_ID,
        client_credential=settings.AZURE_CLIENT_SECRET,
        authority=settings.AZURE_AUTHORITY,
    )


class OneDriveService:

    @staticmethod
    def get_auth_url(redirect_uri: str, state: str = '') -> str:
        """Retorna URL de autorização OAuth para redirecionar o usuário."""
        app = _get_msal_app()
        result = app.initiate_auth_code_flow(
            scopes=SCOPES,
            redirect_uri=redirect_uri,
            state=state,
        )
        return result['auth_uri'], result

    @staticmethod
    def handle_callback(auth_code_flow: dict, callback_params: dict, user: User, redirect_uri: str) -> OneDriveToken:
        """Processa callback OAuth e salva token no banco."""
        app = _get_msal_app()
        result = app.acquire_token_by_auth_code_flow(
            auth_code_flow=auth_code_flow,
            auth_response=callback_params,
            redirect_uri=redirect_uri,
        )
        if 'error' in result:
            raise ValueError(f"Erro OAuth: {result.get('error_description', result['error'])}")

        expires_at = timezone.now() + timedelta(seconds=result.get('expires_in', 3600))
        token, _ = OneDriveToken.objects.update_or_create(
            user=user,
            defaults={
                'access_token': result['access_token'],
                'refresh_token': result.get('refresh_token', ''),
                'expires_at': expires_at,
            }
        )
        return token

    @staticmethod
    def _get_valid_token(user: User) -> str:
        """Retorna access token válido, renovando via refresh token se necessário."""
        token = OneDriveToken.objects.get(user=user)
        if not token.is_expired():
            return token.access_token

        app = _get_msal_app()
        result = app.acquire_token_by_refresh_token(
            refresh_token=token.refresh_token,
            scopes=SCOPES,
        )
        if 'error' in result:
            raise ValueError(f"Erro ao renovar token: {result.get('error_description', result['error'])}")

        token.access_token = result['access_token']
        token.refresh_token = result.get('refresh_token', token.refresh_token)
        token.expires_at = timezone.now() + timedelta(seconds=result.get('expires_in', 3600))
        token.save(update_fields=['access_token', 'refresh_token', 'expires_at'])
        return token.access_token

    @staticmethod
    def _headers(user: User) -> dict:
        return {'Authorization': f'Bearer {OneDriveService._get_valid_token(user)}'}

    @staticmethod
    def is_connected(user: User) -> bool:
        return OneDriveToken.objects.filter(user=user).exists()

    @staticmethod
    def list_files(user: User, folder_path: str = '/') -> list[dict]:
        """Lista arquivos em uma pasta do OneDrive. Retorna apenas arquivos de áudio/vídeo."""
        if folder_path in ('/', ''):
            endpoint = f"{GRAPH_BASE}/me/drive/root/children"
        else:
            encoded = urllib.parse.quote(folder_path.strip('/'))
            endpoint = f"{GRAPH_BASE}/me/drive/root:/{encoded}:/children"

        params = {
            '$select': 'id,name,size,lastModifiedDateTime,file,folder',
            '$top': 100,
            '$orderby': 'lastModifiedDateTime desc',
        }
        resp = httpx.get(endpoint, headers=OneDriveService._headers(user), params=params, timeout=30)
        resp.raise_for_status()
        items = resp.json().get('value', [])

        result = []
        for item in items:
            is_folder = 'folder' in item
            name = item.get('name', '')
            ext = '.' + name.rsplit('.', 1)[-1].lower() if '.' in name else ''
            is_audio = not is_folder and ext in AUDIO_EXTENSIONS
            result.append({
                'id': item['id'],
                'name': name,
                'size': item.get('size', 0),
                'modified': item.get('lastModifiedDateTime', ''),
                'is_folder': is_folder,
                'is_audio': is_audio,
            })
        return result

    @staticmethod
    def download_file(user: User, file_id: str) -> bytes:
        """Faz download do conteúdo de um arquivo do OneDrive."""
        endpoint = f"{GRAPH_BASE}/me/drive/items/{file_id}/content"
        resp = httpx.get(
            endpoint,
            headers=OneDriveService._headers(user),
            follow_redirects=True,
            timeout=300,
        )
        resp.raise_for_status()
        return resp.content

    @staticmethod
    def get_file_info(user: User, file_id: str) -> dict:
        """Retorna metadados de um arquivo."""
        endpoint = f"{GRAPH_BASE}/me/drive/items/{file_id}"
        resp = httpx.get(endpoint, headers=OneDriveService._headers(user), timeout=30)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def upload_file(user: User, folder_path: str, filename: str, content: bytes) -> str:
        """
        Faz upload de arquivo para uma pasta do OneDrive.
        Usa upload de sessão para arquivos grandes.
        Retorna o ID do arquivo criado.
        """
        if folder_path in ('/', ''):
            upload_url = f"{GRAPH_BASE}/me/drive/root:/{filename}:/content"
        else:
            encoded_folder = urllib.parse.quote(folder_path.strip('/'))
            upload_url = f"{GRAPH_BASE}/me/drive/root:/{encoded_folder}/{filename}:/content"

        headers = {
            **OneDriveService._headers(user),
            'Content-Type': 'application/octet-stream',
        }
        resp = httpx.put(upload_url, headers=headers, content=content, timeout=120)
        resp.raise_for_status()
        return resp.json()['id']

    @staticmethod
    def get_item_web_url(user: User, file_id: str) -> Optional[str]:
        """Retorna URL pública para abrir o arquivo no OneDrive."""
        try:
            info = OneDriveService.get_file_info(user, file_id)
            return info.get('webUrl')
        except Exception:
            return None
