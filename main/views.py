from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from .forms import RegisterForm
from django.shortcuts import render

# Create your views here.
def index(request):
    return render(request, 'main/index.html')

class RegisterView(SuccessMessageMixin, CreateView):
    form_class = RegisterForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('login')
    success_message = "Регистрация успешна! Теперь можете войти."

    def form_valid(self, form):
        # Здесь можно добавить логику приветственного бонуса или письма
        return super().form_valid(form)