from .models import Category, Banner
from django.utils import timezone
from django.db import models

def categories_processor(request):
    return {
        'categories': Category.objects.all(),
    }

def account_sidebar_banners(request):
    """Автоматически добавляет баннеры в контекст всех шаблонов"""
    if request.user.is_authenticated:
        now = timezone.now()
        banners = Banner.objects.filter(
            position='account_sidebar',
            status__in=['active', 'scheduled']
        ).filter(
            models.Q(start_date__isnull=True) | models.Q(start_date__lte=now)
        ).filter(
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=now)
        ).order_by('order')[:5]
        
        return {'account_sidebar_banners': banners}
    return {'account_sidebar_banners': []}