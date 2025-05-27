import logging
import re
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger('tours')

def validate_phone(value):
    pattern = r'^\+375 \(\d{2}\) \d{3}-\d{2}-\d{2}$'
    if not re.match(pattern, value):
        raise ValidationError('Формат телефона должен быть +375 (XX) XXX-XX-XX')

def validate_adult(value):
    today = timezone.now().date()
    age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
    if age < 18:
        raise ValidationError('Пользователь должен быть старше 18 лет')

class ClientProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Пользователь")
    patronymic = models.CharField(max_length=100, blank=True, verbose_name="Отчество")
    address = models.TextField(verbose_name="Адрес")
    phone_number = models.CharField(max_length=20, verbose_name="Номер телефона", validators=[validate_phone])
    birth_date = models.DateField(verbose_name="Дата рождения", validators=[validate_adult])
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Профиль клиента"
        verbose_name_plural = "Профили клиентов"

    def __str__(self):
        fn = self.user.first_name
        ln = self.user.last_name
        if fn or ln:
            return f"{ln} {fn}".strip()
        return self.user.username or self.user.email or str(self.pk)

    def save(self, *args, **kwargs):
        try:
            super().save(*args, **kwargs)
            logger.info(f'Сохранен профиль клиента: {self} (ID: {self.id})')
        except Exception as e:
            logger.error(f'Ошибка при сохранении профиля клиента: {e}', exc_info=True)
            raise

    @property
    def email(self):
        return self.user.email


class EmployeeProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Пользователь (сотрудник)")
    patronymic = models.CharField(max_length=100, blank=True, verbose_name="Отчество")
    position = models.CharField(max_length=100, verbose_name="Должность")
    photo = models.ImageField(upload_to='employee_photos/', blank=True, null=True, verbose_name="Фото сотрудника")
    work_description = models.TextField(blank=True, verbose_name="Описание выполняемых работ")
    phone_number = models.CharField(max_length=20, verbose_name="Номер телефона", validators=[validate_phone])
    birth_date = models.DateField(verbose_name="Дата рождения", validators=[validate_adult])
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Профиль сотрудника"
        verbose_name_plural = "Профили сотрудников"

    def __str__(self):
        return f"{self.user.last_name} {self.user.first_name} ({self.position})"

    @property
    def email(self):
        return self.user.email

class Country(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название страны")
    description = models.TextField(blank=True, verbose_name="Описание")

    class Meta:
        verbose_name = "Страна"
        verbose_name_plural = "Страны"
        ordering = ['name']

    def __str__(self):
        return self.name

class SeasonClimate(models.Model):
    SEASON_CHOICES = [
        ('winter', 'Зима'),
        ('spring', 'Весна'),
        ('summer', 'Лето'),
        ('autumn', 'Осень'),
    ]
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='climates', verbose_name="Страна")
    season = models.CharField(max_length=10, choices=SEASON_CHOICES, verbose_name="Сезон")
    climate_description = models.TextField(verbose_name="Описание климата")

    class Meta:
        verbose_name = "Климат по сезонам"
        verbose_name_plural = "Климаты по сезонам"
        unique_together = ('country', 'season')

    def __str__(self):
        return f"{self.country.name} - {self.get_season_display()}"

class Hotel(models.Model):
    STAR_CHOICES = [(i, f"{i}*") for i in range(1, 6)]
    name = models.CharField(max_length=200, verbose_name="Название отеля")
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='hotels', verbose_name="Страна")
    stars = models.PositiveSmallIntegerField(choices=STAR_CHOICES, verbose_name="Количество звезд")
    description = models.TextField(blank=True, verbose_name="Описание")
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Стоимость за ночь")
    photo = models.ImageField(upload_to='hotel_photos/', blank=True, null=True, verbose_name="Фото отеля")

    class Meta:
        verbose_name = "Отель"
        verbose_name_plural = "Отели"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.country.name}, {self.get_stars_display()})"

class TourPackage(models.Model):
    DURATION_CHOICES = [
        (1, "1 неделя"),
        (2, "2 недели"),
        (4, "4 недели"),
    ]
    name = models.CharField(max_length=255, verbose_name="Название путевки")
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='tour_packages', verbose_name="Отель")
    duration_weeks = models.PositiveSmallIntegerField(choices=DURATION_CHOICES, verbose_name="Длительность (недели)")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Стоимость путевки")
    description = models.TextField(blank=True, verbose_name="Описание")
    is_hot_deal = models.BooleanField(default=False, verbose_name="Горящая путевка")
    additional_services = models.TextField(blank=True, verbose_name="Дополнительные услуги")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    start_date = models.DateField(verbose_name="Дата начала тура", null=True, blank=True)
    end_date = models.DateField(verbose_name="Дата окончания тура", null=True, blank=True)

    client = models.ForeignKey(
        'ClientProfile',
        on_delete=models.CASCADE,
        related_name='tour_packages',
        verbose_name="Клиент"
    )

    class Meta:
        verbose_name = "Путевка"
        verbose_name_plural = "Путевки"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if self.start_date and not self.end_date and self.duration_weeks:
            self.end_date = self.start_date + timedelta(weeks=self.duration_weeks)
        super().save(*args, **kwargs)
        try:
            super().save(*args, **kwargs)
            logger.info(f'Сохранен тур: {self.name} (ID: {self.id})')
        except Exception as e:
            logger.error(f'Ошибка при сохранении тура: {e}', exc_info=True)
            raise

    def __str__(self):
        return f"{self.name} ({self.hotel.name}, {self.get_duration_weeks_display()})"

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'В ожидании'),
        ('confirmed', 'Подтвержден'),
        ('paid', 'Оплачен'),
        ('cancelled', 'Отменен'),
    ]
    client = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='orders_as_client', on_delete=models.PROTECT, verbose_name="Клиент")
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='orders_as_employee', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Сотрудник (оформил)")
    tour_packages = models.ManyToManyField(TourPackage, related_name='orders', verbose_name="Приобретенные путевки")
    order_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата заказа")
    departure_date = models.DateField(verbose_name="Дата отправления")
    total_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Общая стоимость")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Статус заказа")

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ['-order_date']

    def __str__(self):
        return f"Заказ №{self.id} от {self.client.username} ({self.order_date.strftime('%d/%m/%Y')})"


class Article(models.Model):
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    short_content = models.TextField(verbose_name="Краткое содержание (одно предложение)")
    full_content = models.TextField(verbose_name="Полное содержание")
    image = models.ImageField(upload_to='article_images/', blank=True, null=True, verbose_name="Изображение")
    publication_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата публикации")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Автор")

    class Meta:
        verbose_name = "Статья (Новость)"
        verbose_name_plural = "Статьи (Новости)"
        ordering = ['-publication_date']

    def __str__(self):
        return self.title

class FAQ(models.Model):
    question = models.TextField(verbose_name="Вопрос")
    answer = models.TextField(verbose_name="Ответ")
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")

    class Meta:
        verbose_name = "Вопрос-Ответ (FAQ)"
        verbose_name_plural = "Вопросы-Ответы (FAQ)"
        ordering = ['-added_at']

    def __str__(self):
        return self.question[:50] + "..."

class Vacancy(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название вакансии")
    description = models.TextField(verbose_name="Описание вакансии")
    publication_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата публикации")

    class Meta:
        verbose_name = "Вакансия"
        verbose_name_plural = "Вакансии"
        ordering = ['-publication_date']

    def __str__(self):
        return self.title

class Review(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Клиент (автор отзыва)")
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, verbose_name="Оценка")
    text = models.TextField(verbose_name="Текст отзыва")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата отзыва")

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ['-created_at']

    def __str__(self):
        return f"Отзыв от {self.client.username} ({self.rating}*)"

class PromoCode(models.Model):
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    discount = models.PositiveSmallIntegerField()
    valid_from = models.DateField(default=timezone.now)
    valid_until = models.DateField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Промокод"
        verbose_name_plural = "Промокоды"
        ordering = ['-valid_until']

    @property
    def is_currently_active(self):
        today = timezone.now().date()
        return self.is_active and self.valid_from <= today <= self.valid_until

    def __str__(self):
        return self.code

class AboutPageContent(models.Model):
    main_text = models.TextField(verbose_name="Основной текст о компании")

    class Meta:
        verbose_name = "Контент страницы 'О компании'"
        verbose_name_plural = "Контент страницы 'О компании'"

    def __str__(self):
        return "Основной текст 'О компании'"


class CompanyVideo(models.Model):
    title = models.CharField(max_length=200, verbose_name="Название видео")
    video_url = models.URLField(verbose_name="Ссылка на видео")
    description = models.TextField(blank=True, verbose_name="Описание")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Видео компании"
        verbose_name_plural = "Видео компании"

    def __str__(self):
        return self.title

class CompanyLogo(models.Model):
    title = models.CharField(max_length=100, default="Логотип компании", verbose_name="Название/тип логотипа")
    logo_image = models.ImageField(upload_to='company_logos/', verbose_name="Файл логотипа")
    description = models.TextField(blank=True, verbose_name="Описание")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Логотип компании"
        verbose_name_plural = "Логотипы компании"

    def __str__(self):
        return self.title

class CompanyHistoryItem(models.Model):
    year = models.PositiveIntegerField(verbose_name="Год")
    event_description = models.TextField(verbose_name="Описание события")

    class Meta:
        verbose_name = "Пункт истории компании"
        verbose_name_plural = "История компании (по годам)"
        ordering = ['-year']

    def __str__(self):
        return f"{self.year}: {self.event_description[:50]}..."

class CompanyRequisite(models.Model):
    name = models.CharField(max_length=255, verbose_name="Наименование реквизита")
    value = models.TextField(verbose_name="Значение реквизита")

    class Meta:
        verbose_name = "Реквизит компании"
        verbose_name_plural = "Реквизиты компании"

    def __str__(self):
        return self.name