from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg
from django.http import JsonResponse

from .forms import RegisterForm
from .models import (
    Product, Cart, CartItem, Order,
    OrderItem, Category, Review
)


# Create your views here.
def index(request):
    return render(request, 'main/index.html')


@login_required(login_url='login')
def account(request):
    return render(request, 'main/account.html')

@login_required(login_url='login')
def account_edit(request):
    return render(request, 'main/account_edit.html')

@login_required(login_url='login')
def account_change_password(request):
    return render(request, 'main/account_change_password.html')

@login_required(login_url='login')
def account_change_address(request):
    return render(request, 'main/account_change_address.html')

@login_required(login_url='login')
def account_change_bookmarks(request):
    return render(request, 'main/account_change_bookmarks.html')

@login_required(login_url='login')
def account_order_history(request):
    return render(request, 'main/account_order_history.html')

@login_required(login_url='login')
def account_bonus_points(request):
    return render(request, 'main/account_bonus_points.html')

@login_required(login_url='login')
def account_return(request):
    return render(request, 'main/account_return.html')

@login_required(login_url='login')
def account_transaction(request):
    return render(request, 'main/account_transaction.html')

@login_required(login_url='login')
def account_recurring(request):
    return render(request, 'main/account_recurring.html')

@login_required(login_url='login')
def account_affiliate_add(request):
    return render(request, 'main/account_affiliate_add.html')

@login_required(login_url='login')
def account_newsletter(request):
    return render(request, 'main/account_newsletter.html')



def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category).order_by('-id')  # новые сверху
    
    context = {
        'category': category,
        'products': products,
    }
    return render(request, 'main/category_products.html', context)


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
    return render(request, 'main/product_detail.html', context)


def quick_view(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    context = {
        'product': product,
    }
    return render(request, 'main/quick_view.html', context)


class RegisterView(SuccessMessageMixin, CreateView):
    form_class = RegisterForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('login')
    success_message = "Регистрация успешна! Теперь можете войти."

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Передаём GET-параметр ref в форму
        if 'ref' in self.request.GET:
            kwargs['initial'] = {'referral_code': self.request.GET['ref']}
        return kwargs

    def form_valid(self, form):
        # Здесь можно обработать реферальный код или бонус
        referral_code = form.cleaned_data.get('referral_code')
        code_word = form.cleaned_data.get('code_word')

        if referral_code:
            # Твоя логика: найти пользователя по коду и начислить бонус
            print(f"Пользователь пришёл по реферальному коду: {referral_code}")
            # Например: Referral.objects.create(...)
        
        if code_word:
            print(f"Кодовое слово: {code_word}")
            # Твоя логика обработки кодового слова

        return super().form_valid(form)


# Страница всех продуктов
def product_list(request):
    products = Product.objects.all()
    return render(request, 'store/product_list.html', {'products': products})

# Добавление товара в корзину
@login_required
def add_to_cart(request, product_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Неверный метод'})

    product = get_object_or_404(Product, pk=product_id)
    
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        cart, _ = Cart.objects.get_or_create(user=None)  # для гостей

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 1}
    )
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()

    # Общая сумма и количество для обновления хедера
    total_items = cart.items.count()
    total_price = sum(item.quantity * item.product.price for item in cart.items.all())

    return JsonResponse({
        'success': True,
        'cart_total_items': total_items,
        'cart_total_price': float(total_price)
    })

# Страница корзины
# Страница корзины
@login_required  # или убрать, если хочешь для гостей
def cart_detail(request):
    cart = Cart.objects.filter(user=request.user).first()
    
    if not cart:
        cart = Cart.objects.create(user=request.user)
    
    items = cart.items.all()
    total_price = sum(item.quantity * item.product.price for item in items)
    
    context = {
        'cart': cart,
        'items': items,
        'total_price': total_price,
    }
    return render(request, 'main/cart_detail.html', context)


# Удаление товара из корзины
@login_required
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    item.delete()
    messages.success(request, "Товар удалён из корзины")
    return redirect('cart_detail')

# Оформление заказа (пока просто заглушка)
@login_required
def checkout(request):
    if request.method == 'POST':
        try:
            cart = Cart.objects.get(user=request.user)
            if not cart.items.exists():
                messages.error(request, "Корзина пуста")
                return redirect('cart_detail')
            
            # Создаём заказ
            order = Order.objects.create(
                user=request.user,
                total_price=cart.get_total_price(),
                address=request.user.address or "Адрес не указан",
                status='new'
            )
            
            # Переносим товары в заказ
            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price
                )
            
            # Очищаем корзину
            cart.items.all().delete()
            
            messages.success(request, "Заказ успешно оформлен! (пока без оплаты)")
            return redirect('order_success')  # Создай потом страницу успеха
            
        except Exception as e:
            messages.error(request, f"Ошибка при оформлении: {str(e)}")
    
    return redirect('cart_detail')