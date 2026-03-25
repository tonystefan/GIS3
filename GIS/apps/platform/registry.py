"""
Registro central de serviços da plataforma.
Para adicionar um novo serviço, basta incluir uma entrada aqui.
"""

SERVICE_REGISTRY = {
    'transcricao': {
        'name': 'Transcrição',
        'description': 'Transcreva reuniões do OneDrive e gere atas automaticamente.',
        'index_url': 'transcricao:index',
        'icon': 'microphone',
        'color': 'indigo',
        'version': '1.0',
    },
}
