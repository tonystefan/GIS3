from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse


class HtmxLoginRequiredMixin(LoginRequiredMixin):
    """LoginRequired que retorna 401 para requests HTMX (evita redirect dentro de swap)."""

    def handle_no_permission(self):
        if self.request.headers.get('HX-Request'):
            return HttpResponse(status=401, headers={'HX-Redirect': self.get_login_url()})
        return super().handle_no_permission()
