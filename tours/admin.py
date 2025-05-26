from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import (
    ClientProfile,
    EmployeeProfile,
    Country,
    SeasonClimate,
    Hotel,
    TourPackage,
    Order,
    Article,
    FAQ,
    Vacancy,
    Review,
    PromoCode,
    AboutPageContent,
    CompanyVideo,
    CompanyLogo,
    CompanyHistoryItem,
    CompanyRequisite
)

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not email:
            raise forms.ValidationError("Email обязателен")
        return email

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "password1", "password2"),
        }),
    )
    # чтобы email был обязательным и в изменении
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Персональная информация', {'fields': ('first_name', 'last_name', 'email')}),
        ('Права доступа', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

class SeasonClimateInline(admin.TabularInline):
    model = SeasonClimate
    extra = 1

class HotelInline(admin.TabularInline):
    model = Hotel
    extra = 1

class TourPackageInline(admin.TabularInline):
    model = TourPackage
    extra = 1

class CountryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    inlines = [SeasonClimateInline, HotelInline]

class SeasonClimateAdmin(admin.ModelAdmin):
    list_display = ('country', 'season', 'climate_description')
    list_filter = ('country', 'season')
    search_fields = ('country__name', 'season', 'climate_description')

class HotelAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'stars', 'price_per_night')
    list_filter = ('country', 'stars')
    search_fields = ('name', 'country__name')

class TourPackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'hotel', 'duration_weeks', 'price', 'is_hot_deal')
    list_filter = ('hotel', 'duration_weeks', 'is_hot_deal')
    search_fields = ('name', 'hotel__name')
    inlines = []

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'employee', 'order_date', 'status', 'total_price')
    list_filter = ('status', 'order_date')
    search_fields = ('client__username', 'employee__username')
    filter_horizontal = ('tour_packages',)

class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'birth_date', 'address')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone_number')

class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'position', 'birth_date')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'position')

class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'publication_date', 'author')
    search_fields = ('title', 'short_content', 'full_content', 'author__username')
    list_filter = ('publication_date',)

class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'added_at')
    search_fields = ('question', 'answer')

class VacancyAdmin(admin.ModelAdmin):
    list_display = ('title', 'publication_date')
    search_fields = ('title', 'description')

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('client', 'rating', 'created_at')
    search_fields = ('client__username', 'text')
    list_filter = ('rating', 'created_at')

class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount', 'description', 'valid_from', 'valid_until', 'is_active')
    list_filter = ('is_active', 'valid_from', 'valid_until')
    search_fields = ('code', 'description')

class AboutPageContentAdmin(admin.ModelAdmin):
    list_display = ('main_text',)

class CompanyVideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'uploaded_at')
    search_fields = ('title',)

class CompanyLogoAdmin(admin.ModelAdmin):
    list_display = ('title', 'uploaded_at')
    search_fields = ('title',)

class CompanyHistoryItemAdmin(admin.ModelAdmin):
    list_display = ('year', 'event_description')
    search_fields = ('year', 'event_description')

class CompanyRequisiteAdmin(admin.ModelAdmin):
    list_display = ('name', 'value')
    search_fields = ('name', 'value')

admin.site.register(ClientProfile, ClientProfileAdmin)
admin.site.register(EmployeeProfile, EmployeeProfileAdmin)
admin.site.register(Country, CountryAdmin)
admin.site.register(SeasonClimate, SeasonClimateAdmin)
admin.site.register(Hotel, HotelAdmin)
admin.site.register(TourPackage, TourPackageAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Article, ArticleAdmin)
admin.site.register(FAQ, FAQAdmin)
admin.site.register(Vacancy, VacancyAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(PromoCode, PromoCodeAdmin)
admin.site.register(AboutPageContent, AboutPageContentAdmin)
admin.site.register(CompanyVideo, CompanyVideoAdmin)
admin.site.register(CompanyLogo, CompanyLogoAdmin)
admin.site.register(CompanyHistoryItem, CompanyHistoryItemAdmin)
admin.site.register(CompanyRequisite, CompanyRequisiteAdmin)