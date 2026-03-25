"""
WSGI config for core project.

It exposes the WSGI callable as a module-level variable named ``application``.
"""
import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

# ---------------------------------------------------------------------------
# Em produção (Vercel): executa migrate + collectstatic na primeira invocação.
# Usa um flag file em /tmp para não repetir a cada request.
# ---------------------------------------------------------------------------
_INIT_FLAG = '/tmp/.gis_initialized'

if os.environ.get('DJANGO_ENV') == 'production' and not os.path.exists(_INIT_FLAG):
    try:
        from django.core.management import call_command
        import django
        django.setup()
        call_command('migrate', '--noinput', verbosity=0)
        call_command('collectstatic', '--noinput', '--clear', verbosity=0)
        call_command('seed_glossario', verbosity=0)
        open(_INIT_FLAG, 'w').close()
    except Exception as e:
        print(f'[wsgi init] erro na inicialização: {e}', file=sys.stderr)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

app = application
