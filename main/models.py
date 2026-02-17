from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils.crypto import get_random_string
from django.template.defaulttags import register
from django.utils.translation import gettext_lazy as _


class SiteSettings(models.Model):
    max_referral_levels = models.PositiveIntegerField(
        default=3,
        verbose_name="Максимальное количество уровней рефералов",
        help_text="Максимальное количество уровней рефералов"
    )
    bonus_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10.00,
        verbose_name="Процент бонуса от суммы заказа",
        help_text="Процент бонуса от суммы заказа для реферера"
    )

    class Meta:
        verbose_name = "Настройка сайта"
        verbose_name_plural = "Настройки сайта"

    def __str__(self):
        return "Глобальные настройки"


class Category(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name="Название категории"
    )
    slug = models.SlugField(
        unique=True,
        verbose_name="Slug (URL)"
    )

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name="Название товара"
    )
    description = models.TextField(
        verbose_name="Описание"
    )
    composition = models.TextField(  # ← новое поле "Состав"
        blank=True,
        verbose_name="Состав"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Цена"
    )
    stock = models.PositiveIntegerField(
        default=0,
        verbose_name="Остаток на складе"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Категория"
    )
    image = models.ImageField(
        upload_to='products/',
        blank=True,
        null=True,
        verbose_name="Изображение"
    )

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

    def __str__(self):
        return self.name
    
    # Средний рейтинг (вычисляем на лету)
    @property
    def average_rating(self):
        from django.db.models import Avg
        avg = self.reviews.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else 0.0

    # Количество отзывов
    @property
    def review_count(self):
        return self.reviews.count()
    
    
class ProductCertificate(models.Model):
    product = models.ForeignKey(
        Product,
        related_name='certificates',
        on_delete=models.CASCADE,
        verbose_name="Товар"
    )
    image = models.ImageField(
        upload_to='certificates/',
        verbose_name="Изображение сертификата"
    )
    description = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Описание сертификата"
    )

    class Meta:
        verbose_name = "Сертификат товара"
        verbose_name_plural = "Сертификаты товаров"

    def __str__(self):
        return f"Сертификат для {self.product.name}"

class CustomUserManager(BaseUserManager):
    """
    Кастомный менеджер, чтобы create_user / create_superuser работали без username
    """
    def create_user(self, email, phone, password=None, **extra_fields):
        if not email:
            raise ValueError(_("Email обязателен"))
        if not phone:
            raise ValueError(_("Телефон обязателен"))

        email = self.normalize_email(email)
        user = self.model(email=email, phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self.create_user(email, phone, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_("email адрес"), unique=True, max_length=254)
    phone = models.CharField(_("телефон"), max_length=20, unique=True)
    first_name = models.CharField(_("имя"), max_length=150, blank=True)
    last_name = models.CharField(_("фамилия"), max_length=150, blank=True)
    referral_code = models.CharField(_("реферальный код"), max_length=10, unique=True, blank=True, editable=False)
    referrer = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='referrals',
        verbose_name=_("пригласивший")
    )
    balance = models.DecimalField(_("баланс"), max_digits=10, decimal_places=2, default=0.00)
    address = models.TextField(_("адрес доставки"), blank=True, null=True)

    is_active = models.BooleanField(_("активен"), default=False)  # пользователь активен после подтверждения email
    is_email_verified = models.BooleanField(_("email подтверждён"), default=False)
    email_verification_code = models.CharField(max_length=6, blank=True, null=True)  # код для подтверждения email

    is_staff = models.BooleanField(_("сотрудник"), default=False)
    date_joined = models.DateTimeField(_("дата регистрации"), auto_now_add=True)

    # Настройки аутентификации
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone']

    objects = CustomUserManager()  # твой менеджер пользователей

    class Meta:
        verbose_name = _("пользователь")
        verbose_name_plural = _("пользователи")

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        # Генерация реферального кода
        if not self.referral_code:
            while True:
                code = get_random_string(10).upper()
                if not User.objects.filter(referral_code=code).exists():
                    self.referral_code = code
                    break
        super().save(*args, **kwargs)


class Cart(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Пользователь"
    )
    session_key = models.CharField(
        max_length=40,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Ключ сессии"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_price(self):
        return sum(item.quantity * item.product.price for item in self.items.all())

    def __str__(self):
        if self.user:
            return f"Корзина {self.user.username}"
        return f"Гостевая корзина {self.session_key}"


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        related_name='items',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Корзина"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Товар"
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="Количество"
    )

    @register.filter
    def multiply(value, arg):
        return value * arg

    class Meta:
        verbose_name = "Элемент корзины"
        verbose_name_plural = "Элементы корзины"

    def __str__(self):
        return f"{self.quantity} x {self.product.name if self.product else 'Удалённый товар'}"


class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name="Код купона")
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=5.00,
        verbose_name="Процент скидки"
    )
    valid_from = models.DateTimeField(verbose_name="Действует с")
    valid_to = models.DateTimeField(verbose_name="Действует до")
    active = models.BooleanField(default=True, verbose_name="Активен")
    max_uses = models.PositiveIntegerField(default=0, verbose_name="Макс. использований (0 — без лимита)")
    uses = models.PositiveIntegerField(default=0, verbose_name="Сколько раз использован")

    class Meta:
        verbose_name = "Купон на скидку"
        verbose_name_plural = "Купоны на скидку"

    def __str__(self):
        return f"{self.code} ({self.discount_percent}% скидки)"

    def is_valid(self, user=None):
        if not self.active:
            return False
        if self.valid_to < timezone.now() or self.valid_from > timezone.now():
            return False
        if self.max_uses > 0 and self.uses >= self.max_uses:
            return False
        return True


class Order(models.Model):
    STATUS_CHOICES = (
        ('new', 'Новый'),
        ('pending_payment', 'Ожидает оплаты'),  # Добавим этот статус
        ('paid', 'Оплачен'),
        ('shipped', 'Отправлен'),
        ('completed', 'Завершён'),
        ('canceled', 'Отменен'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Пользователь"
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Общая сумма"
    )
    status = models.CharField(
        max_length=20,  # Увеличим для 'pending_payment'
        choices=STATUS_CHOICES,
        default='new',
        verbose_name="Статус"
    )
    address = models.TextField(
        verbose_name="Адрес доставки (на момент заказа)"
    )
    phone = models.CharField(
        max_length=20,
        verbose_name="Телефон (на момент заказа)",
        blank=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    coupon = models.ForeignKey(
        Coupon,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="Купон на скидку"
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Сумма скидки"
    )

    # УБИРАЕМ расчет скидки из save() - он уже сделан во view
    def save(self, *args, **kwargs):
        # Только увеличиваем счетчик использования купона
        if self.coupon and self.coupon.is_valid() and not self.pk:
            # Увеличиваем uses только при создании нового заказа
            self.coupon.uses += 1
            self.coupon.save()
        
        super().save(*args, **kwargs)
        
        if self.status == 'paid':
            settings = SiteSettings.objects.first() or SiteSettings()
            referrer = self.user.referrer
            level = 1
            while referrer and level <= settings.max_referral_levels:
                bonus = self.total_price * (settings.bonus_percent / 100)
                referrer.balance += bonus
                referrer.save()
                referrer = referrer.referrer
                level += 1

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ['-created_at']  # Добавим сортировку по умолчанию

    def __str__(self):
        return f"Заказ #{self.id} от {self.user.username if self.user else 'Гость'}"
    

class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name='items',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Заказ"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Товар"
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="Количество"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Цена на момент заказа"
    )

    class Meta:
        verbose_name = "Элемент заказа"
        verbose_name_plural = "Элементы заказа"

    def __str__(self):
        return f"{self.quantity} x {self.product.name if self.product else 'Удалённый товар'}"


class Review(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Пользователь"
    )
    product = models.ForeignKey(
        Product,
        related_name='reviews',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Товар"
    )
    text = models.TextField(
        verbose_name="Текст отзыва"
    )
    rating = models.PositiveIntegerField(
        default=5,
        verbose_name="Оценка (1-5)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"

    def __str__(self):
        return f"Отзыв от {self.user.username if self.user else 'Аноним'} на {self.product.name if self.product else 'Удалённый товар'}"
    

class Banner(models.Model):
    """Модель для баннеров в сайдбаре"""
    POSITION_CHOICES = (
        ('account_sidebar', 'Сайдбар личного кабинета'),
        ('home_top', 'Главная страница - верх'),
        ('home_sidebar', 'Главная страница - сайдбар'),
        ('category', 'Категории товаров'),
        ('product', 'Страница товара'),
    )
    
    STATUS_CHOICES = (
        ('active', 'Активен'),
        ('inactive', 'Неактивен'),
        ('scheduled', 'По расписанию'),
    )
    
    title = models.CharField(max_length=200, verbose_name="Название баннера")
    image = models.ImageField(upload_to='banners/', verbose_name="Изображение")
    link = models.URLField(max_length=500, verbose_name="Ссылка", blank=True)
    position = models.CharField(
        max_length=50, 
        choices=POSITION_CHOICES, 
        default='account_sidebar',
        verbose_name="Позиция"
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='active',
        verbose_name="Статус"
    )
    order = models.IntegerField(default=0, verbose_name="Порядок сортировки")
    start_date = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name="Дата начала показа"
    )
    end_date = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name="Дата окончания показа"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    class Meta:
        verbose_name = "Баннер"
        verbose_name_plural = "Баннеры"
        ordering = ['order', '-created_at']
    
    def __str__(self):
        return self.title
    
    def is_active(self):
        """Проверка активности баннера"""
        if self.status == 'inactive':
            return False
        elif self.status == 'scheduled':
            now = timezone.now()
            if self.start_date and now < self.start_date:
                return False
            if self.end_date and now > self.end_date:
                return False
        return True
    
    @property
    def image_url(self):
        """URL изображения"""
        if self.image and hasattr(self.image, 'url'):
            return self.image.url
        return ''