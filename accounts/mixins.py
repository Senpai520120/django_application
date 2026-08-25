from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from accounts.permissions import is_admin


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Аноним — на логин, залогиненный не-админ — 403 (логика AccessMixin)."""

    def test_func(self) -> bool:
        return is_admin(self.request.user)
