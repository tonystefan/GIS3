from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from .registry import SERVICE_REGISTRY


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'platform/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['services'] = SERVICE_REGISTRY
        return ctx
