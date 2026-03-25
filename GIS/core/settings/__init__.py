from .base import *  # noqa

import os
from decouple import config

env = config('DJANGO_ENV', default='development')

if env == 'production':
    from .production import *  # noqa
else:
    from .development import *  # noqa
