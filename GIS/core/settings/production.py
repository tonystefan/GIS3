from decouple import config

DEBUG = False

# Serve static files via WhiteNoise sem precisar de collectstatic prévio.
# CompressedManifest requer collectstatic; WhiteNoiseStorage serve diretamente.
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
WHITENOISE_USE_FINDERS = True

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

CSRF_TRUSTED_ORIGINS = [
    config('CSRF_TRUSTED_ORIGIN', default='https://example.vercel.app'),
]

# ---------------------------------------------------------------------------
# Cloud storage para media (áudios e .docx)
# Compatível com Supabase Storage, AWS S3 ou qualquer backend S3.
# Se AWS_ACCESS_KEY_ID não estiver configurado, cai no filesystem local.
# ---------------------------------------------------------------------------
_aws_key = config('AWS_ACCESS_KEY_ID', default='')
if _aws_key:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

    AWS_ACCESS_KEY_ID = _aws_key
    AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='us-east-1')
    AWS_S3_ENDPOINT_URL = config('AWS_S3_ENDPOINT_URL', default='')  # Supabase: https://<ref>.supabase.co/storage/v1/s3
    AWS_DEFAULT_ACL = 'public-read'
    AWS_S3_FILE_OVERWRITE = False
    AWS_QUERYSTRING_AUTH = False  # URLs públicas diretas

    MEDIA_URL = f'https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/'
    if AWS_S3_ENDPOINT_URL:
        MEDIA_URL = f'{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/'
