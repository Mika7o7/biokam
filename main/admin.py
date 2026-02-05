from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django import forms
from django.utils.html import format_html

from .models import (
    User, Category, Product, Cart, CartItem,
    Order, OrderItem, Review, SiteSettings,
    ProductCertificate, Coupon, Banner
)


# Форма создания нового пользователя в админке
class CustomUserCreationForm(forms.ModelForm):
    """
    Кастомная форма создания пользователя (без username)
    """
    password1 = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput,
        strip=False,
        help_text="Придумайте надёжный пароль"
    )
    password2 = forms.CharField(
        label="Повторите пароль",
        widget=forms.PasswordInput,
        strip=False,
        help_text="Введите пароль ещё раз для проверки"
    )

    class Meta:
        model = User
        fields = ('email', 'phone', 'first_name', 'last_name', 'is_staff', 'is_superuser')

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Пароли не совпадают.")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


# Форма изменения существующего пользователя
class CustomUserChangeForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        label="Пароль",
        help_text="Оставьте пустым, если не хотите менять пароль"
    )

    class Meta:
        model = User
        fields = '__all__'

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')

        if password:
            user.set_password(password)

        if commit:
            user.save()
        return user


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm

    list_display = (
        'email',
        'phone',
        'first_name',
        'last_name',
        'referral_code',
        'referrer_link',
        'balance',
        'is_staff',
        'is_active',
        'date_joined'
    )
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('email', 'phone', 'first_name', 'last_name', 'referral_code')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Личные данные', {'fields': ('first_name', 'last_name', 'phone', 'address')}),
        ('Рефералы и баланс', {'fields': ('referral_code', 'referrer', 'balance')}),
        ('Права доступа', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Даты', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'phone',
                'first_name',
                'last_name',
                'password1',
                'password2',
                'is_staff',
                'is_superuser'
            ),
        }),
    )

    readonly_fields = ('referral_code', 'date_joined', 'last_login')

    # Красивое отображение реферера как ссылки
    @admin.display(description='Пригласивший')
    def referrer_link(self, obj):
        if obj.referrer:
            url = f"/admin/main/user/{obj.referrer.id}/change/"
            return format_html('<a href="{}">{}</a>', url, obj.referrer.email)
        return "—"

    referrer_link.short_description = 'Пригласивший'

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


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('id', 'uses', 'max_uses', 'discount_percent', 'code')
    list_filter = ('active', 'valid_to')
    search_fields = ('user__username',)
    

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
    
@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ['title', 'position', 'status', 'order', 'preview_image', 'is_active_display', 'created_at']
    list_filter = ['status', 'position', 'created_at']
    search_fields = ['title', 'link']
    list_editable = ['order', 'status']
    readonly_fields = ['preview_image_large', 'created_at', 'updated_at']
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'image', 'preview_image_large', 'link')
        }),
        ('Настройки показа', {
            'fields': ('position', 'status', 'order', 'start_date', 'end_date')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def preview_image(self, obj):
        """Миниатюра в списке"""
        if obj.image:
            return format_html('<img src="{}" width="50" height="30" style="object-fit: cover;" />', obj.image.url)
        return '-'
    preview_image.short_description = 'Превью'
    
    def preview_image_large(self, obj):
        """Большое изображение в форме"""
        if obj.image:
            return format_html('<img src="{}" width="300" style="max-width: 100%; height: auto;" />', obj.image.url)
        return 'Изображение не загружено'
    preview_image_large.short_description = 'Превью изображения'
    
    def is_active_display(self, obj):
        """Отображение активности"""
        if obj.is_active():
            return format_html('<span style="color: green;">✓ Активен</span>')
        else:
            return format_html('<span style="color: red;">✗ Неактивен</span>')
    is_active_display.short_description = 'Активность'