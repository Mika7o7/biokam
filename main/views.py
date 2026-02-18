from django.views.generic import CreateView, FormView
from django.urls import reverse_lazy, reverse
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Avg, Sum, Count
from decimal import Decimal
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.utils import timezone
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt
from django.db import models
from yookassa import Configuration, Payment
import random
import string 
import json
import uuid
import os

from .forms import RegisterForm, VerifyEmailForm, LoginForm
from .models import (
    Product, Cart, CartItem, Order,
    OrderItem, Category, Review, User,
    SiteSettings, Coupon, Banner
)

Configuration.account_id = settings.YOOKASSA_SHOP_ID
Configuration.secret_key = settings.YOOKASSA_SECRET_KEY


from django.contrib.auth.views import LoginView

class CustomLoginView(LoginView):
    template_name = "registration/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True
    success_url = reverse_lazy('account')  # или 'home' — любая твоя страница

    # или через метод
    def get_success_url(self):
        return reverse_lazy('account')  # или self.request.GET.get('next', '/')
    
class RegisterView(FormView):
    template_name = 'registration/register.html'
    form_class = RegisterForm
    success_url = reverse_lazy('verify_email')

    def form_valid(self, form):

        # генерируем код
        code = str(random.randint(100000, 999999))

        # сохраняем данные временно в session
        self.request.session['register_data'] = {
            'email': form.cleaned_data['email'],
            'phone': form.cleaned_data['phone'],
            'password': form.cleaned_data['password1'],
            'invite_code': form.cleaned_data.get('invite_code', ''),
            'code': code,
        }

        # отправляем email
        send_mail(
            'Код подтверждения',
            f'Ваш код подтверждения: {code}',
            None,
            [form.cleaned_data['email']],
            fail_silently=False,
        )

        messages.success(self.request, 'Код отправлен на email')

        return redirect('verify_email')


# =========================
# ШАГ 2 — Подтверждение кода
# =========================

class VerifyEmailView(FormView):
    template_name = 'registration/verify_email.html'
    form_class = VerifyEmailForm
    success_url = reverse_lazy('login')

    def form_valid(self, form):

        entered_code = form.cleaned_data['code']

        session_data = self.request.session.get('register_data')

        if not session_data:
            messages.error(self.request, 'Сессия истекла')
            return redirect('register')

        if entered_code != session_data['code']:
            messages.error(self.request, 'Неверный код')
            return redirect('verify_email')

        # создаём пользователя
        user = User.objects.create_user(
            email=session_data['email'],
            phone=session_data['phone'],
            password=session_data['password'],
            is_active=True,
            is_email_verified=True,
        )

        # реферал
        invite_code = session_data.get('invite_code')
        if invite_code:
            referrer = User.objects.filter(referral_code=invite_code).first()
            if referrer:
                user.referrer = referrer
                user.save()

        # очищаем session
        del self.request.session['register_data']

        messages.success(self.request, 'Аккаунт создан!')

        return super().form_valid(form)



# Main Page.
def index(request):
    return render(request, 'main/index3.html')



# ================== CABINET PAGE ===================

def get_sidebar_banners():
    """Получить активные баннеры для сайдбара"""
    now = timezone.now()
    
    banners = Banner.objects.filter(
        position='account_sidebar',
        status__in=['active', 'scheduled']
    ).filter(
        models.Q(start_date__isnull=True) | models.Q(start_date__lte=now)
    ).filter(
        models.Q(end_date__isnull=True) | models.Q(end_date__gte=now)
    ).order_by('order')[:5]  # Ограничим 5 баннерами
    
    return banners



# Обновите все views которые используют сайдбар
@login_required(login_url='login')
def account(request):
    banners = get_sidebar_banners()
    context = {
        'title': 'Личный кабинет',
        'banners': banners,
    }
    return render(request, 'main/account.html', context)

@login_required(login_url='login')
def account_edit(request):
    banners = get_sidebar_banners()
    context = {
        'title': 'Редактирование профиля',
        'banners': banners,
    }
    return render(request, 'main/account_edit.html', context)

@login_required(login_url='login')
def account_change_password(request):
    banners = get_sidebar_banners()
    context = {
        'title': 'Смена пароля',
        'banners': banners,
    }
    return render(request, 'main/account_change_password.html', context)

@login_required(login_url='login')
def account_order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    banners = get_sidebar_banners()
    
    context = {
        'orders': orders,
        'title': 'История заказов',
        'banners': banners,
    }
    return render(request, 'main/account_order_history.html', context)

@login_required(login_url='login')
def account_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = order.items.all()
    banners = get_sidebar_banners()
    
    context = {
        'order': order,
        'order_items': order_items,
        'title': f'Заказ №{order.id}',
        'banners': banners,
    }
    return render(request, 'main/account_order_detail.html', context)


@login_required
def affiliate_dashboard(request):
    user = request.user
    
    # Настройки системы
    settings = SiteSettings.objects.first()
    if not settings:
        settings = SiteSettings.objects.create()  # на всякий случай
    
    # --- Основные данные реферальной программы ---
    referral_link = request.build_absolute_uri(f"/register?ref={user.referral_code}")
    referral_rate = settings.bonus_percent  # % который получает реферер
    
    # Все прямые рефералы (1-й уровень)
    direct_referrals = user.referrals.all()
    
    # Подсчёт статистики
    result = Order.objects.filter(
    user__referrer=user,
    status='completed'
    ).aggregate(
        total_orders_sum=Sum('total_price')
    )

    total_orders = result['total_orders_sum'] or Decimal('0.00')
    bonus_percent = Decimal(str(settings.bonus_percent))  # важно превратить float → Decimal
    total_bonus = total_orders * (bonus_percent / Decimal('100'))
    # Более точный вариант — если бонусы уже начислены на баланс
    # total_earned = user.balance  # ← если используете именно этот подход
    
    # Последние рефералы (например, 10 шт)
    recent_referrals = direct_referrals.order_by('-date_joined')[:10]
    
    referral_stats = []
    for ref in recent_referrals:
        earned_from_this = Order.objects.filter(
            user=ref,
            status='completed'
        ).aggregate(
            total=Sum('total_price')
        )['total'] or 0
        
        bonus_from_this = earned_from_this * (settings.bonus_percent / 100)
        
        referral_stats.append({
            'username': ref.username,
            'date_joined': ref.date_joined,
            'total_orders_sum': earned_from_this,
            'earned_from_user': round(bonus_from_this, 2)
        })
    
    context = {
        'referral_link': referral_link,
        'referral_code': user.referral_code,
        'referral_rate': float(referral_rate),  # для шаблона
        'total_balance': round(user.balance, 2),
        'referral_count': direct_referrals.count(),
        'recent_referrals': referral_stats,
        'max_levels': settings.max_referral_levels,
    }
    
    return render(request, 'main/account_affiliate_add.html', context)


# ================== STORE PAGE ===================
def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category).order_by('-id')  # новые сверху
    banners = get_sidebar_banners()

    context = {
        'category': category,
        'products': products,
        'banners': banners,
    }
    return render(request, 'store/category_products.html', context)

# Страница всех продуктов
def product_list(request):
    products = Product.objects.all()
    return render(request, 'store/product_list.html', {'products': products})

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    # Средний рейтинг и количество отзывов
    avg_rating = product.reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    review_count = product.reviews.count()
    
    context = {
        'product': product,
        'avg_rating': round(avg_rating, 1),
        'review_count': review_count,
        'reviews': product.reviews.all().order_by('-created_at')[:5],  # последние 5 отзывов
    }
    return render(request, 'store/product_detail.html', context)


# ================== CART ===================
from .utils import get_cart
# cart section
def cart_detail(request):
    cart = get_cart(request)
    
    context = {
        'cart': cart,
        'items': cart.items.select_related('product').all(),
        'total': cart.total_price,
    }
    return render(request, 'store/cart_detail.html', context)

# Добавление товара в корзину
def add_to_cart(request, product_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Неверный метод'})

    product = get_object_or_404(Product, pk=product_id)
    cart = get_cart(request)
    # if request.user.is_authenticated:
    #     cart, _ = Cart.objects.get_or_create(user=request.user)
    # else:
    #     cart, _ = Cart.objects.get_or_create(user=None)  # для гостей
    
    # Получаем количество из тела запроса (JSON)
    data = json.loads(request.body)
    quantity = int(data.get('quantity', 1))

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity}
    )
    # Добавьте эту отладку
    print(f"\n=== add_to_cart ===")
    print(f"Cart ID: {cart.id}")
    print(f"Cart session_key: {cart.session_key}")
    print(f"Request session_key: {request.session.session_key}")
    print(f"User: {request.user}")

    if not created:
        cart_item.quantity += quantity
        cart_item.save()

    # Общая сумма и количество для обновления хедера
    total_items = cart.items.count()
    total_price = sum(item.quantity * item.product.price for item in cart.items.all())

    cart_html = render_to_string('main/partials/cart_dropdown.html', {
        'user': request.user,
        'cart': cart,
    }, request=request)

    return JsonResponse({
        'success': True,
        'cart_html': cart_html,
        'cart_total_items': total_items,
        'cart_total_price': float(total_price),
        'product_name': product.name,
    })

# Удаление товара из корзины
@require_POST
def remove_from_cart(request, item_id):
    try:
        cart = get_cart(request)
        
        # Удаляем товар
        try:
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
            cart_item.delete()
        except CartItem.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Товар не найден в корзине'
            })

        # Получаем обновленные данные
        items = cart.items.select_related('product').all()
        total_items = items.count()
        total_price = float(cart.total_price)

        # Подготавливаем данные для шаблона
        cart_items = []
        for item in items:
            if item.product:
                cart_items.append({
                    'id': item.id,
                    'product': item.product,
                    'quantity': item.quantity
                })

        # ВАЖНО: Рендерим ПОЛНЫЙ HTML корзины (как в add_to_cart)
        cart_html = render_to_string('main/partials/cart_dropdown.html', {
            'cart_items': cart_items,
            'total': total_price,
            'cart': cart,
            'user': request.user
        }, request=request)

        return JsonResponse({
            'success': True,
            'cart_html': cart_html,  # ← Полный HTML всего блока корзины
            'cart_total_items': total_items,
            'cart_total_price': total_price
        })
        
    except Exception as e:
        print(f"Error in remove_from_cart: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
    
    
def validate_phone(phone):
    """Валидация российского телефона с учетом форматирования"""
    print(phone)
    if not phone:
        return False
    
    # Убираем все нецифры
    digits = ''.join(filter(str.isdigit, phone))
    print(f"nomer: {digits}")
    
    # Российский номер должен быть 11 цифр и начинаться с 7 или 8
    if len(digits) == 11 and (digits.startswith('7') or digits.startswith('8')):
        return True
    
    # Или 10 цифр (без кода страны)
    if len(digits) == 10:
        return True
    
    return False


# ================== ORDER ===================
# Оформление заказа (пока просто заглушка)
def checkout(request):
    # Получаем корзину через get_cart (как во всех других view)
    cart = get_cart(request)
    
    if not cart.items.exists():
        messages.warning(request, "Ваша корзина пуста")
        return redirect('cart_detail')

    subtotal = cart.total_price
    discount_amount = Decimal('0.00')
    coupon = None
    applied_coupon_code = ''

    if request.method == 'POST':
        coupon_code = request.POST.get('coupon_code', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        address = request.POST.get('address', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()  # Добавляем email

        # AJAX-проверка купона
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            if 'coupon_code' in request.POST and 'create_order' not in request.POST:
                if coupon_code:
                    try:
                        coupon = Coupon.objects.get(code__iexact=coupon_code)
                        if coupon.is_valid():
                            discount_amount = subtotal * (coupon.discount_percent / Decimal('100'))
                            return JsonResponse({
                                'success': True,
                                'discount_percent': float(coupon.discount_percent),
                                'discount_amount': float(discount_amount.quantize(Decimal('0.01'))),
                                'new_total': float((subtotal - discount_amount).quantize(Decimal('0.01'))),
                                'message': f'Купон применён! Скидка {coupon.discount_percent}%',
                                'coupon_code': coupon.code
                            })
                        else:
                            return JsonResponse({'success': False, 'message': 'Купон недействителен или истёк'})
                    except Coupon.DoesNotExist:
                        return JsonResponse({'success': False, 'message': 'Такой купон не найден'})
                return JsonResponse({'success': False, 'message': 'Введите код купона'})

        # Создание заказа
        if 'create_order' in request.POST:
            # Проверяем обязательные поля
            if not first_name:
                return JsonResponse({'success': False, 'message': 'Укажите ваше имя'})
            if not address:
                return JsonResponse({'success': False, 'message': 'Укажите адрес доставки'})
            if not email:
                return JsonResponse({'success': False, 'message': 'Укажите email'})
            
            if not validate_phone(phone):
                return JsonResponse({'success': False, 'message': 'Некорректный номер телефона. Формат: +7 (999) 999-99-99'})

            # Применяем купон
            if coupon_code:
                try:
                    coupon = Coupon.objects.get(code__iexact=coupon_code)
                    if coupon.is_valid():
                        discount_amount = subtotal * (coupon.discount_percent / Decimal('100'))
                except Coupon.DoesNotExist:
                    pass

            total_price = subtotal - discount_amount

            # Если пользователь не авторизован - запускаем процесс регистрации
            if not request.user.is_authenticated:
                # Проверяем, существует ли пользователь с таким email
                if User.objects.filter(email=email).exists():
                    return JsonResponse({
                        'success': False,
                        'require_login': True,
                        'message': 'Этот email уже зарегистрирован. Пожалуйста, войдите в аккаунт.'
                    })
                
                # Сохраняем данные заказа в сессию
                request.session['pending_order'] = {
                    'first_name': first_name,
                    'last_name': last_name,
                    'address': address,
                    'phone': phone,
                    'email': email,
                    'coupon_code': coupon_code,
                    'total_price': float(total_price),
                    'discount_amount': float(discount_amount),
                }
                
                # Генерируем и сохраняем код подтверждения
                verification_code = str(random.randint(100000, 999999))
                request.session['verification_code'] = verification_code
                request.session['verification_email'] = email
                
                # Сохраняем данные для регистрации
                request.session['registration_data'] = {
                    'email': email,
                    'phone': phone,
                    'first_name': first_name,
                    'last_name': last_name,
                    'address': address,
                }
                
                # ОТПРАВЛЯЕМ КОД НА ПОЧТУ (вместо вывода в терминал)
                try:
                    send_mail(
                        'Код подтверждения для регистрации',
                        f'Здравствуйте!\n\nВаш код подтверждения: {verification_code}\n\n'
                        f'Этот код необходимо ввести на сайте для завершения оформления заказа.\n'
                        f'Если вы не запрашивали этот код, просто проигнорируйте это письмо.',
                        settings.DEFAULT_FROM_EMAIL,
                        [email],
                        fail_silently=False,
                    )
                    
                    return JsonResponse({
                        'success': True,
                        'require_verification': True,
                        'message': 'Код подтверждения отправлен на ваш email'
                    })
                    
                except Exception as e:
                    # В случае ошибки отправки email, выводим код в терминал для тестирования
                    print(f"Ошибка отправки email: {e}")
                    print(f"Код подтверждения для {email}: {verification_code}")
                    
                    return JsonResponse({
                        'success': True,
                        'require_verification': True,
                        'message': 'Код подтверждения (тестовый режим): ' + verification_code
                    })

            # Для авторизованных пользователей - создаем заказ сразу
            order = Order.objects.create(
                user=request.user,
                total_price=total_price,
                address=address,
                phone=phone,
                coupon=coupon,
                discount_amount=discount_amount,
                status='new',
            )
            
            # Сохраняем данные в профиль пользователя
            request.user.first_name = first_name
            request.user.last_name = last_name
            request.user.address = address
            request.user.phone = phone
            request.user.save()

            # Добавляем товары в заказ
            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price
                )

            # Очищаем корзину
            cart.items.all().delete()

            return JsonResponse({
                'success': True,
                'order_id': order.id,
                'message': f'Заказ №{order.id} создан успешно!',
                'total_price': float(total_price)
            })

    # Рендер страницы
    context = {
        'cart': cart,
        'items': cart.items.select_related('product').all(),
        'subtotal': subtotal,
        'discount_amount': discount_amount,
        'total': subtotal - discount_amount,
        'applied_coupon_code': applied_coupon_code,
    }
    
    # Добавляем данные пользователя только если он авторизован
    if request.user.is_authenticated:
        context.update({
            'user_first_name': request.user.first_name or '',
            'user_last_name': request.user.last_name or '',
            'user_address': request.user.address or '',
            'user_phone': request.user.phone or '',
            'user_email': request.user.email or '',
        })
    else:
        context.update({
            'user_first_name': '',
            'user_last_name': '',
            'user_address': '',
            'user_phone': '',
            'user_email': '',
        })
    
    return render(request, 'store/cart_detail.html', context)

@csrf_exempt
def verify_order_code(request):
    """Проверяет код подтверждения и создает пользователя"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Неверный метод'})
    
    try:
        data = json.loads(request.body)
        entered_code = data.get('code')
        
        # Получаем данные из сессии
        verification_code = request.session.get('verification_code')
        verification_email = request.session.get('verification_email')
        registration_data = request.session.get('registration_data')
        pending_order = request.session.get('pending_order')
        
        if not verification_code or not verification_email or not registration_data or not pending_order:
            return JsonResponse({
                'success': False, 
                'message': 'Сессия истекла. Пожалуйста, начните оформление заказа заново.'
            })
        
        if entered_code != verification_code:
            return JsonResponse({
                'success': False,
                'message': 'Неверный код подтверждения'
            })
        
        # Генерируем случайный пароль
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        
        # Создаем пользователя
        user = User.objects.create_user(
            email=verification_email,
            phone=registration_data['phone'],
            password=password,
            first_name=registration_data['first_name'],
            last_name=registration_data.get('last_name', ''),
            address=registration_data.get('address', ''),
            is_active=True,
            is_email_verified=True,
        )
        
        # Автоматически логиним пользователя
        from django.contrib.auth import login
        login(request, user)
        
        # Получаем корзину пользователя
        from .utils import get_cart
        cart = get_cart(request)
        
        # Создаем заказ сразу
        order = Order.objects.create(
            user=user,
            total_price=pending_order['total_price'],
            address=pending_order['address'],
            phone=pending_order['phone'],
            coupon=None,
            discount_amount=pending_order['discount_amount'],
            status='new',
        )
        
        # Добавляем товары в заказ из корзины
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )
        
        # Очищаем корзину
        cart.items.all().delete()
        
        # ОТПРАВЛЯЕМ ДАННЫЕ НА ПОЧТУ
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            
            send_mail(
                'Регистрация и заказ на сайте',
                f'Здравствуйте, {user.first_name}!\n\n'
                f'Вы успешно зарегистрировались на нашем сайте.\n\n'
                f'Ваши данные для входа:\n'
                f'Email: {user.email}\n'
                f'Пароль: {password}\n\n'
                f'Ваш заказ №{order.id} создан и принят в обработку.\n'
                f'Сумма заказа: {order.total_price} ₽\n\n'
                f'Спасибо за покупку!\n'
                f'С уважением, администрация сайта.',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
        except Exception as e:
            # Если не удалось отправить email, просто логируем ошибку
            print(f"Ошибка отправки email: {e}")
        
        # Очищаем данные из сессии
        if 'verification_code' in request.session:
            del request.session['verification_code']
        if 'verification_email' in request.session:
            del request.session['verification_email']
        if 'registration_data' in request.session:
            del request.session['registration_data']
        if 'pending_order' in request.session:
            del request.session['pending_order']
        
        return JsonResponse({
            'success': True,
            'message': 'Регистрация успешна',
            'order_id': order.id,
            'total_price': float(order.total_price),
            'user_id': user.id
        })
        
    except Exception as e:
        print(f"Error in verify_order_code: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': str(e)})
    
@login_required
def order_success(request, order_id):
    """Страница успешной оплаты"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Проверяем статус платежа в ЮKassa
    try:
        # Получаем payment_id из сессии (сохраняем при создании платежа)
        payment_id = request.session.get(f'payment_for_order_{order_id}')
        
        print(f"Проверка статуса для заказа {order_id}")
        print(f"payment_id из сессии: {payment_id}")
        print(f"Текущий статус заказа: {order.status}")
        
        # Если заказ уже оплачен - просто показываем страницу
        if order.status == 'paid':
            messages.success(request, f'Заказ №{order_id} уже оплачен!')
            context = {'order': order, 'title': 'Заказ оплачен'}
            return render(request, 'store/order_success.html', context)
        
        # Пробуем найти платеж
        payment = None
        
        if payment_id:
            # Если есть payment_id в сессии, ищем по нему
            try:
                from yookassa import Payment
                payment = Payment.find_one(payment_id)
                print(f"Найден платеж по ID: {payment.id}, статус: {payment.status}")
            except Exception as e:
                print(f"Ошибка при поиске платежа по ID: {e}")
                payment = None
        
        if not payment:
            # Если не нашли по ID, ищем по метаданным заказа
            try:
                from yookassa import Payment
                payments = Payment.list({
                    'metadata': {'order_id': str(order_id)}
                })
                
                if payments and len(payments.items) > 0:
                    payment = payments.items[0]
                    print(f"Найден платеж по метаданным: {payment.id}, статус: {payment.status}")
            except Exception as e:
                print(f"Ошибка при поиске платежа по метаданным: {e}")
        
        if payment:
            print(f"Статус платежа: {payment.status}")
            
            if payment.status == 'succeeded':
                # Платеж успешен - обновляем статус заказа
                order.status = 'paid'
                order.save()
                print(f"Заказ {order_id} обновлен на статус 'paid'")
                
                # Очищаем корзину пользователя
                from .models import Cart
                cart = Cart.objects.filter(user=request.user).first()
                if cart:
                    cart.items.all().delete()
                    print(f"Корзина пользователя {request.user.id} очищена")
                
                messages.success(request, f'Оплата заказа №{order_id} прошла успешно!')
                
            elif payment.status == 'waiting_for_capture':
                messages.info(request, 'Платеж обрабатывается. Статус обновится через несколько секунд.')
            else:
                messages.warning(request, f'Статус платежа: {payment.status}')
        else:
            print(f"Платеж для заказа {order_id} не найден")
            
            # Для тестирования: если заказ в статусе pending_payment, 
            # и прошло больше минуты - принудительно ставим paid
            if order.status == 'pending_payment':
                from datetime import timedelta
                from django.utils import timezone
                
                if order.created_at < timezone.now() - timedelta(minutes=1):
                    print(f"ТЕСТОВЫЙ РЕЖИМ: принудительно оплачиваем заказ {order_id}")
                    order.status = 'paid'
                    order.save()
                    messages.success(request, f'Заказ №{order_id} оплачен (тестовый режим)!')
        
    except Exception as e:
        print(f"Ошибка при проверке платежа: {e}")
        import traceback
        traceback.print_exc()
    
    context = {
        'order': order,
        'title': 'Заказ оплачен'
    }
    return render(request, 'store/order_success.html', context)

@csrf_exempt  # Добавьте этот декоратор
@require_POST
@login_required
def create_payment(request):
    try:
        print("=== НАЧАЛО create_payment ===")
        print("Заголовки:", dict(request.headers))
        print("Метод:", request.method)
        print("Content-Type:", request.content_type)
        print("CSRF токен в заголовке:", request.headers.get('X-Csrftoken'))
        
        # Получаем данные
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        
        print(f"Полученные данные: {data}")
        
        order_id = data.get('order_id')
        expected_amount = data.get('expected_amount')
        
        print(f"order_id из запроса: {order_id}")
        print(f"expected_amount из запроса: {expected_amount}")
        
        if not order_id:
            print("ОШИБКА: order_id не передан")
            return JsonResponse({'success': False, 'message': 'Заказ не найден'}, status=400)

        # Ищем заказ
        try:
            order = Order.objects.get(id=order_id, user=request.user)
            print(f"Найден заказ №{order.id}:")
            print(f"  Сумма в БД: {order.total_price}")
            print(f"  Скидка: {order.discount_amount}")
            print(f"  Статус: {order.status}")
            print(f"  Купон: {order.coupon}")
            
            # Проверяем сумму
            if expected_amount:
                expected_decimal = Decimal(str(expected_amount))
                if order.total_price != expected_decimal:
                    print(f"ВНИМАНИЕ: Несоответствие сумм! БД: {order.total_price}, Ожидается: {expected_decimal}")
        except Order.DoesNotExist:
            print(f"ОШИБКА: Заказ {order_id} не найден для пользователя {request.user}")
            # Посмотрим все заказы пользователя
            user_orders = Order.objects.filter(user=request.user).order_by('-id')[:5]
            print(f"Последние 5 заказов пользователя:")
            for o in user_orders:
                print(f"  Заказ №{o.id}: сумма={o.total_price}, статус={o.status}")
            return JsonResponse({'success': False, 'message': 'Заказ не найден'}, status=404)

        amount = order.total_price
        print(f"Используем сумму: {amount}")

        # Создаем платеж в ЮKassa
        import uuid
        idempotence_key = str(uuid.uuid4())
        
        payment_data = {
            "amount": {
                "value": f"{amount:.2f}",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": request.build_absolute_uri(
                    reverse('order_success', kwargs={'order_id': order_id})
                )
            },
            "capture": True,
            "description": f"Заказ №{order_id}",
            "metadata": {
                "order_id": order_id, 
                "user_id": request.user.id
            },
        }

        print(f"Данные для ЮKassa: {payment_data}")
        
        from yookassa import Payment
        payment = Payment.create(payment_data, idempotence_key)
        
        # Обновляем статус заказа
        order.status = 'pending_payment'
        order.save()
        
        print(f"Платеж создан: {payment.id}")
        print(f"URL для оплаты: {payment.confirmation.confirmation_url}")
        print("=== КОНЕЦ create_payment ===")

        return JsonResponse({
            'success': True,
            'payment_url': payment.confirmation.confirmation_url,
            'payment_id': payment.id,
            'order_amount': float(amount)
        })

    except Exception as e:
        import traceback
        print("=== ОШИБКА в create_payment ===")
        print(f"Ошибка: {str(e)}")
        print(traceback.format_exc())
        print("=== КОНЕЦ ОШИБКИ ===")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


import hashlib
import hmac
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def yookassa_webhook(request):
    """Вебхук для уведомлений от ЮKassa"""
    if request.method != 'POST':
        return HttpResponse(status=405)
    
    try:
        # Получаем данные
        body = request.body.decode('utf-8')
        signature = request.headers.get('HTTP_CONTENT_SIGNATURE', '')
        
        # ВАЖНО: Проверяем подпись
        # Получите секретный ключ из настроек ЮKassa
        secret_key = settings.YOOKASSA_SECRET_KEY
        
        # Проверяем подпись
        hash = hmac.new(
            secret_key.encode('utf-8'),
            body.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        if f"sha256={hash}" != signature:
            print("Неверная подпись от ЮKassa!")
            return HttpResponse(status=400)
        
        # Парсим данные
        import json
        data = json.loads(body)
        
        event = data.get('event')
        payment_data = data.get('object')
        
        if event == 'payment.succeeded':
            payment_id = payment_data.get('id')
            order_id = payment_data.get('metadata', {}).get('order_id')
            amount = payment_data.get('amount', {}).get('value')
            
            print(f"Платеж {payment_id} успешно завершен для заказа {order_id}")
            
            if order_id:
                try:
                    order = Order.objects.get(id=order_id)
                    order.status = 'paid'
                    order.save()
                    
                    # Можно отправить email пользователю
                    # send_order_paid_email(order)
                    
                except Order.DoesNotExist:
                    print(f"Заказ {order_id} не найден")
        
        elif event == 'payment.canceled':
            payment_id = payment_data.get('id')
            order_id = payment_data.get('metadata', {}).get('order_id')
            
            print(f"Платеж {payment_id} отменен для заказа {order_id}")
            
            if order_id:
                try:
                    order = Order.objects.get(id=order_id)
                    order.status = 'canceled'
                    order.save()
                except Order.DoesNotExist:
                    print(f"Заказ {order_id} не найден")
        
        # Всегда возвращаем 200 OK
        return HttpResponse(status=200)
        
    except Exception as e:
        print(f"Ошибка в вебхуке: {e}")
        return HttpResponse(status=500)
    




@require_POST
@login_required
def save_contact_info(request):
    """Сохранить контактную информацию пользователя"""
    try:
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        address = request.POST.get('address', '').strip()
        phone = request.POST.get('phone', '').strip()
        
        # Валидация
        if not first_name:
            return JsonResponse({'success': False, 'message': 'Укажите ваше имя'})
        if not address:
            return JsonResponse({'success': False, 'message': 'Укажите адрес доставки'})
        
        phone_digits = ''.join(filter(str.isdigit, phone))
        if len(phone_digits) < 11:
            return JsonResponse({'success': False, 'message': 'Некорректный номер телефона'})
        
        # Сохраняем в модель User
        user = request.user
        user.first_name = first_name
        user.last_name = last_name
        user.address = address
        user.phone = phone
        user.save()
        
        return JsonResponse({
            'success': True, 
            'message': 'Контактная информация сохранена',
            'first_name': first_name,
            'last_name': last_name,
            'address': address,
            'phone': phone
        })
    
    except Exception as e:
        print(f"Ошибка сохранения контактной информации: {e}")
        return JsonResponse({'success': False, 'message': 'Ошибка сохранения'})
    

@require_POST
@login_required
def save_profile_info(request):
    """Сохранение профиля пользователя"""
    try:
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        address = request.POST.get('address', '').strip()
        phone = request.POST.get('phone', '').strip()
        
        # Валидация
        if not first_name:
            return JsonResponse({'success': False, 'message': 'Укажите ваше имя'})
        if not address:
            return JsonResponse({'success': False, 'message': 'Укажите адрес доставки'})
        
        phone_digits = ''.join(filter(str.isdigit, phone))
        if len(phone_digits) < 11:
            return JsonResponse({'success': False, 'message': 'Некорректный номер телефона'})
        
        # Сохраняем
        user = request.user
        user.first_name = first_name
        user.last_name = last_name
        user.address = address
        user.phone = phone
        user.save()
        
        return JsonResponse({
            'success': True, 
            'message': 'Профиль успешно обновлен'
        })
    
    except Exception as e:
        print(f"Ошибка сохранения профиля: {e}")
        return JsonResponse({'success': False, 'message': 'Ошибка сохранения'})
    

@require_POST
@login_required
def change_password_api(request):
    """API для смены пароля (AJAX)"""
    try:
        current_password = request.POST.get('current_password', '').strip()
        new_password1 = request.POST.get('new_password1', '').strip()
        new_password2 = request.POST.get('new_password2', '').strip()
        
        print(f"Смена пароля для пользователя {request.user.username}")
        print(f"Текущий пароль предоставлен: {bool(current_password)}")
        print(f"Новый пароль 1: {new_password1}")
        print(f"Новый пароль 2: {new_password2}")
        
        # Проверка обязательных полей
        if not current_password:
            return JsonResponse({
                'success': False,
                'message': 'Введите текущий пароль'
            })
        
        if not new_password1 or not new_password2:
            return JsonResponse({
                'success': False,
                'message': 'Заполните оба поля для нового пароля'
            })
        
        # Проверка совпадения новых паролей
        if new_password1 != new_password2:
            return JsonResponse({
                'success': False,
                'message': 'Новые пароли не совпадают'
            })
        
        # Проверка текущего пароля
        if not request.user.check_password(current_password):
            return JsonResponse({
                'success': False,
                'message': 'Текущий пароль неверный'
            })
        
        # Проверка что новый пароль отличается от старого
        if request.user.check_password(new_password1):
            return JsonResponse({
                'success': False,
                'message': 'Новый пароль не должен совпадать со старым'
            })
        
        # Проверка сложности пароля (минимальная)
        if len(new_password1) < 8:
            return JsonResponse({
                'success': False,
                'message': 'Пароль должен содержать минимум 8 символов'
            })
        
        # Меняем пароль
        request.user.set_password(new_password1)
        request.user.save()
        
        # Обновляем сессию, чтобы пользователь не разлогинился
        update_session_auth_hash(request, request.user)
        
        print(f"✓ Пароль успешно изменен для пользователя {request.user.username}")
        
        return JsonResponse({
            'success': True,
            'message': 'Пароль успешно изменен!'
        })
        
    except Exception as e:
        print(f"❌ Ошибка при смене пароля: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': f'Ошибка при смене пароля: {str(e)}'
        })
    
def generate_robokassa_signature(*args, **kwargs):
    """Генерирует подпись для Робокассы"""
    password = settings.ROBOKASSA_PASSWORD2
    parts = [str(arg) for arg in args]
    return hashlib.md5(':'.join(parts).encode()).hexdigest()

@login_required
def create_robokassa_payment(request):
    """Создает платеж через Робокассу"""
    try:
        data = json.loads(request.body)
        order_id = data.get('order_id')
        
        order = get_object_or_404(Order, id=order_id, user=request.user)
        
        # Параметры для Робокассы
        merchant_login = settings.ROBOKASSA_MERCHANT_LOGIN
        out_sum = str(order.total_price)
        inv_id = str(order.id)
        description = f"Оплата заказа №{order.id}"
        
        # Для тестового режима
        if settings.ROBOKASSA_TEST_MODE:
            is_test = '1'
        else:
            is_test = '0'
        
        # Генерируем подпись (md5(Логин:Сумма:НомерЗаказа:Пароль#1))
        signature = hashlib.md5(
            f"{merchant_login}:{out_sum}:{inv_id}:{settings.ROBOKASSA_PASSWORD1}".encode()
        ).hexdigest()
        
        # URL для отправки
        if settings.ROBOKASSA_TEST_MODE:
            payment_url = "http://test.robokassa.ru/Index.aspx"
        else:
            payment_url = "https://auth.robokassa.ru/Merchant/Index.aspx"
        
        # Параметры для формы
        params = {
            'MerchantLogin': merchant_login,
            'OutSum': out_sum,
            'InvId': inv_id,
            'Description': description,
            'SignatureValue': signature,
            'IsTest': is_test,
            'Encoding': 'utf-8',
            'Culture': 'ru',
        }
        
        # Обновляем статус заказа
        order.status = 'pending_payment'
        order.save()
        
        # Вместо JSON возвращаем HTML с формой для автоматического POST
        form_html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Перенаправление на оплату</title>
        </head>
        <body>
            <form id="robokassa_form" action="{payment_url}" method="POST">
                <input type="hidden" name="MerchantLogin" value="{merchant_login}">
                <input type="hidden" name="OutSum" value="{out_sum}">
                <input type="hidden" name="InvId" value="{inv_id}">
                <input type="hidden" name="Description" value="{description}">
                <input type="hidden" name="SignatureValue" value="{signature}">
                <input type="hidden" name="IsTest" value="{is_test}">
                <input type="hidden" name="Encoding" value="utf-8">
                <input type="hidden" name="Culture" value="ru">
            </form>
            <script>document.getElementById('robokassa_form').submit();</script>
        </body>
        </html>
        '''
        
        return HttpResponse(form_html)
        
    except Exception as e:
        print(f"Ошибка в create_robokassa_payment: {e}")
        return JsonResponse({'success': False, 'message': str(e)})

@csrf_exempt
def robokassa_result(request):
    """Обработка результата оплаты (Result URL)"""
    if request.method == 'POST':
        data = request.POST
    else:
        data = request.GET
    
    # Получаем параметры
    out_sum = data.get('OutSum')
    inv_id = data.get('InvId')
    signature = data.get('SignatureValue')
    
    # Проверяем подпись (md5(Сумма:НомерЗаказа:Пароль#2))
    expected_signature = hashlib.md5(
        f"{out_sum}:{inv_id}:{settings.ROBOKASSA_PASSWORD2}".encode()
    ).hexdigest()
    
    if signature.lower() != expected_signature.lower():
        return HttpResponse("bad sign", status=400)
    
    try:
        order = Order.objects.get(id=inv_id)
        order.status = 'paid'
        order.save()
        
        # Очищаем корзину пользователя
        cart = Cart.objects.filter(user=order.user).first()
        if cart:
            cart.items.all().delete()
        
        # Отвечаем Робокассе "OK" для подтверждения
        return HttpResponse(f"OK{inv_id}")
        
    except Order.DoesNotExist:
        return HttpResponse("order not found", status=404)

def robokassa_success(request):
    """Страница успешной оплаты (Success URL)"""
    order_id = request.GET.get('InvId')
    if order_id:
        messages.success(request, f'Заказ №{order_id} успешно оплачен!')
        return redirect('order_success', order_id=order_id)
    return redirect('home')

def robokassa_fail(request):
    """Страница неудачной оплаты (Fail URL)"""
    messages.error(request, 'Оплата не прошла. Пожалуйста, попробуйте снова.')
    return redirect('checkout')