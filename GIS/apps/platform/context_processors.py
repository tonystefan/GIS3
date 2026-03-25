from .registry import SERVICE_REGISTRY


def platform_context(request):
    return {
        'services': SERVICE_REGISTRY,
    }
