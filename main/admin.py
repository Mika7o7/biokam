from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms

from .models import (
    User, Category, Product, Cart, CartItem,
    Order, OrderItem, Review, SiteSettings,
    ProductCertificate
)

# Форма создания пользователя (та же, что в регистрации)
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')  # + твои поля, если нужно

# Форма изменения пользователя (пароль меняется отдельно)
class CustomUserChangeForm(UserChangeForm):
    password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        help_text="Оставьте пустым, если не хотите менять пароль"
    )

    class Meta:
        model = User
        fields = '__all__'

    def clean_password(self):
        # Не меняем пароль, если поле пустое
        return self.cleaned_data.get('password')

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:  # Если ввели новый пароль — хэшируем
            user.set_password(password)
        if commit:
            user.save()
        return user


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm       # ← та же форма, что в регистрации!
    form = CustomUserChangeForm
    model = User

    list_display = ('username', 'email', 'referral_code', 'referrer', 'balance', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'referral_code')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Личные данные', {'fields': ('first_name', 'last_name', 'email', 'address')}),
        ('Рефералы и бонусы', {'fields': ('referral_code', 'referrer', 'balance')}),
        ('Права доступа', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Даты', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_staff', 'is_superuser'),
        }),
    )

    readonly_fields = ('referral_code', 'date_joined', 'last_login')

# Категории
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


# Товары
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'get_image_preview')
    list_filter = ('category',)
    search_fields = ('name', 'description')
    readonly_fields = ('get_image_preview',)
    
    def get_image_preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" style="max-height: 50px;">'
        return "Нет изображения"
    get_image_preview.short_description = "Превью"
    get_image_preview.allow_tags = True


@admin.register(ProductCertificate)
class ProductCertificateAdmin(admin.ModelAdmin):
    list_display = ('product', 'description')

    def get_image_preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" style="max-height: 50px;">'
        return "Нет изображения"
    get_image_preview.short_description = "Превью"
    get_image_preview.allow_tags = True


# Корзина и элементы корзины
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at')
    search_fields = ('user__username',)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'quantity')
    list_filter = ('cart__user',)


# Заказы и позиции
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_price', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username',)
    readonly_fields = ('total_price', 'created_at')
    
    fieldsets = (
        (None, {'fields': ('user', 'total_price', 'status', 'address', 'created_at')}),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price')
    search_fields = ('product__name',)


# Отзывы
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__username', 'product__name')


# Глобальные настройки (только одна запись)
@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('max_referral_levels', 'bonus_percent')
    
    def has_add_permission(self, request):
        # Разрешаем создать только одну запись настроек
        return not SiteSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False  # Запрещаем удаление настроек