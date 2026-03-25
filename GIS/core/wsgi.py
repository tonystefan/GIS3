"""
WSGI config for core project.
"""
import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

# Em produção (Vercel): roda migrate apenas uma vez por instância Lambda.
# collectstatic e seed_glossario devem ser rodados manualmente via CLI.
if os.environ.get('DJANGO_ENV') == 'production':
    _FLAG = '/tmp/.gis_migrated'
    if not os.path.exists(_FLAG):
        try:
            import django
            django.setup()
            from django.core.management import call_command
            call_command('migrate', '--noinput', verbosity=0)
            open(_FLAG, 'w').close()
        except Exception as exc:
            print(f'[wsgi] migrate falhou: {exc}', file=sys.stderr)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

app = application
