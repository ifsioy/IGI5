import calendar
import logging
from datetime import datetime
from statistics import median, mode

import pytz
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import user_passes_test, login_required
from django.db.models import Avg, Count, F, Sum

from .models import Country, ClientProfile, EmployeeProfile, SeasonClimate, Hotel, TourPackage, Order, Article, FAQ, \
    Vacancy, Review, PromoCode, AboutPageContent, CompanyVideo, CompanyLogo, CompanyHistoryItem, CompanyRequisite

import requests
import matplotlib.pyplot as plt
import io
import base64

logger = logging.getLogger('tours')

def sales_distribution_chart(request):
    tours = TourPackage.objects.values('name', 'price')
    names = [tour['name'] for tour in tours]
    prices = [tour['price'] for tour in tours]

    plt.figure(figsize=(10, 6))
    plt.bar(names, prices, color='skyblue')
    plt.title('Распределение цен туров')
    plt.xlabel('Название тура')
    plt.ylabel('Цена')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    string = base64.b64encode(buf.read())
    uri = 'data:image/png;base64,' + string.decode('utf-8')
    buf.close()

    return render(request, 'sales_chart.html', {'chart_uri': uri})

def currency_page(request):
    url = 'https://open.er-api.com/v6/latest/RUB'
    rates = {}
    error = None
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code != 200:
            error = f"Ошибка соединения: {resp.status_code}"
        else:
            data = resp.json()
            if data.get('result') == 'success':
                rates = data.get('rates', {})
            else:
                error = data.get('error-type', 'Ошибка ответа от API')
    except Exception as e:
        error = str(e)
    return render(request, 'currency_external.html', {'rates': rates, 'error': error})

def weather_page(request):
    cities = ['Moscow', 'Istanbul', 'Bangkok']
    weather_data = []
    for city in cities:
        url = f'https://wttr.in/{city}?format=j1'
        try:
            resp = requests.get(url, timeout=5)
            data = resp.json()
            current = data['current_condition'][0]
            weather_data.append({
                'city': city,
                'temp': current['temp_C'],
                'desc': current['weatherDesc'][0]['value'],
                'icon': None
            })
        except Exception as e:
            weather_data.append({
                'city': city,
                'temp': None,
                'desc': f"Ошибка: {e}",
                'icon': None,
            })
    return render(request, 'weather_external.html', {'weather_data': weather_data, 'global_error': None})


def tours_catalog(request):
    try:
        logger.info('Запрос к каталогу туров')
        price_min = request.GET.get('price_min')
        price_max = request.GET.get('price_max')
        country_id = request.GET.get('country')
        hotel_class = request.GET.get('hotel_class')
        is_hot = request.GET.get('is_hot')
        service = request.GET.get('service')
        search_query = request.GET.get('search')
        sort_by = request.GET.get('sort_by')

        tours = TourPackage.objects.all()

        if price_min:
            tours = tours.filter(price__gte=price_min)
        if price_max:
            tours = tours.filter(price__lte=price_max)
        if country_id:
            tours = tours.filter(hotel__country__id=country_id)
        if hotel_class:
            tours = tours.filter(hotel__stars=hotel_class)
        if is_hot:
            tours = tours.filter(is_hot_deal=True)
        if service:
            tours = tours.filter(additional_services__icontains=service)

        logger.debug(f'Найдено {tours.count()} туров после фильтрации')
        if sort_by:
            if sort_by in ['price', 'name', 'created_at']:
                tours = tours.order_by(sort_by)
            elif sort_by == '-price':
                tours = tours.order_by('-price')

        hotels = Hotel.objects.select_related('country').all()
        countries = Country.objects.all()
        promo_codes = [p for p in PromoCode.objects.all() if p.is_currently_active]

        return render(request, 'tours_catalog.html', {
            'tours': tours,
            'hotels': hotels,
            'countries': countries,
            'promo_codes': promo_codes,
            'filters': {
                'price_min': price_min,
                'price_max': price_max,
                'country_id': country_id,
                'hotel_class': hotel_class,
                'is_hot': is_hot,
                'service': service,
                'search_query': search_query,
                'sort_by': sort_by,
            }
        })
    except Exception as e:
        logger.error(f'Ошибка при загрузке каталога туров: {e}', exc_info=True)
        return HttpResponse('Произошла ошибка при загрузке каталога', status=500)



@login_required
def user_dashboard(request):
    user = request.user
    now_utc = datetime.utcnow().replace(tzinfo=pytz.UTC)
    user_timezone = getattr(user, 'timezone', 'Europe/Moscow')
    local_now = now_utc.astimezone(pytz.timezone(user_timezone))

    current_month_calendar = calendar.TextCalendar().formatmonth(local_now.year, local_now.month)

    client_profile = getattr(user, 'clientprofile', None)
    employee_profile = getattr(user, 'employeeprofile', None)

    if client_profile:
        recent_tours = TourPackage.objects.filter(client=client_profile).order_by('-created_at')[:5]
    elif employee_profile:
        recent_tours = TourPackage.objects.filter(client__user=user).order_by('-created_at')[:5]
    else:
        recent_tours = []

    sales_data = TourPackage.objects.aggregate(
        avg_sale=Avg('price'),
        total_sales=Sum('price')
    )
    all_sales_prices = list(TourPackage.objects.values_list('price', flat=True))
    sales_median = median(all_sales_prices) if all_sales_prices else None
    sales_mode = mode(all_sales_prices) if all_sales_prices else None

    current_year = timezone.now().year
    client_ages = [
        current_year - client.birth_date.year
        for client in ClientProfile.objects.exclude(birth_date__isnull=True)
    ]
    age_median = median(client_ages) if client_ages else None
    age_avg = sum(client_ages) / len(client_ages) if client_ages else None

    popular_packages = (
        TourPackage.objects.values('name')
        .annotate(count=Count('id'))
        .order_by('-count')
        .first()
    )
    profitable_packages = (
        TourPackage.objects.values('name')
        .annotate(total_profit=Sum('price'))
        .order_by('-total_profit')
        .first()
    )

    context = {
        'user': user,
        'current_time_utc': now_utc.strftime('%d/%m/%Y %H:%M:%S'),
        'current_time_local': local_now.strftime('%d/%m/%Y %H:%M:%S'),
        'user_timezone': user_timezone,
        'calendar': current_month_calendar,
        'recent_tours': recent_tours,
        'stats': {
            'avg_sale': sales_data['avg_sale'],
            'total_sales': sales_data['total_sales'],
            'sales_median': sales_median,
            'sales_mode': sales_mode,
            'age_median': age_median,
            'age_avg': age_avg,
            'popular_package': popular_packages,
            'profitable_package': profitable_packages,
        },
    }

    if client_profile:
        tours = client_profile.tour_packages.select_related('hotel')
        promo_codes = PromoCode.objects.filter(is_active=True, valid_from__lte=now_utc, valid_until__gte=now_utc)
        context.update({
            'profile_type': 'client',
            'profile': client_profile,
            'tours': tours,
            'promo_codes': promo_codes,
        })
    elif employee_profile:
        clients = ClientProfile.objects.prefetch_related('tour_packages').filter(user=user)
        sales = TourPackage.objects.filter(client__user=user).select_related('hotel')
        context.update({
            'profile_type': 'employee',
            'profile': employee_profile,
            'clients': clients,
            'sales': sales,
        })
    else:
        context['profile_type'] = 'unknown'

    return render(request, 'user_dashboard.html', context)

@login_required
def client_dashboard(request):
    client = get_object_or_404(ClientProfile, user=request.user)
    tours = TourPackage.objects.filter(client=client)
    now = timezone.now().date()
    promo_codes = PromoCode.objects.filter(is_active=True, valid_from__lte=now, valid_until__gte=now)
    return render(request, 'client_dashboard.html', {
        'client': client,
        'tours': tours,
        'promo_codes': promo_codes,
    })

@login_required
def employee_dashboard(request):
    employee = get_object_or_404(EmployeeProfile, user=request.user)
    clients = ClientProfile.objects.prefetch_related('tour_packages')
    sales = TourPackage.objects.select_related('client', 'hotel')
    return render(request, 'employee_dashboard.html', {
        'employee': employee,
        'clients': clients,
        'sales': sales,
    })

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_clients_with_tours(request):
    from django.db.models import Sum, Count, Prefetch

    clients = ClientProfile.objects.prefetch_related('tour_packages__hotel__country')
    client_tour_stats = ClientProfile.objects.annotate(
        tour_count=Count('tour_packages'),
        total_cost=Sum('tour_packages__price')
    )
    hotels = Hotel.objects.select_related('country')

    client_tour_stats = ClientProfile.objects.annotate(
        tour_count=Count('tour_packages'),
        total_cost=Sum('tour_packages__price')
    )

    return render(request, 'admin_clients_with_tours.html', {
        'clients': clients,
        'hotels': hotels,
        'client_tour_stats': client_tour_stats,
    })
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def home(request):
    last_article = Article.objects.order_by('-publication_date').first()
    return render(request, 'tours/home.html', {'last_article': last_article})

def about(request):
    about_content = AboutPageContent.objects.first()
    videos = CompanyVideo.objects.all()
    logos = CompanyLogo.objects.all()
    history = CompanyHistoryItem.objects.order_by('-year')
    requisites = CompanyRequisite.objects.all()
    return render(request, 'tours/about.html', {
        'about_content': about_content,
        'videos': videos,
        'logos': logos,
        'history': history,
        'requisites': requisites,
    })

def news_list(request):
    articles = Article.objects.order_by('-publication_date')
    return render(request, 'tours/news_list.html', {'articles': articles})

def faq_list(request):
    faqs = FAQ.objects.order_by('-added_at')
    return render(request, 'tours/faq_list.html', {'faqs': faqs})

def contacts(request):
    employees = EmployeeProfile.objects.select_related('user').all()
    return render(request, 'tours/contacts.html', {'employees': employees})

def privacy_policy(request):
    return render(request, 'tours/privacy_policy.html')


def vacancy_list(request):
    vacancies = Vacancy.objects.order_by('-publication_date')
    return render(request, 'tours/vacancy_list.html', {'vacancies': vacancies})

def review_list(request):
    reviews = Review.objects.select_related('client').order_by('-created_at')
    return render(request, 'tours/review_list.html', {'reviews': reviews})


def promocode_list(request):
    today = timezone.now().date()
    active_promocodes = PromoCode.objects.filter(is_active=True, valid_until__gte=today).order_by('-valid_until')
    archived_promocodes = PromoCode.objects.filter(is_active=False) | PromoCode.objects.filter(valid_until__lt=today)
    archived_promocodes = archived_promocodes.distinct().order_by('-valid_until') # distinct() на случай пересечения

    return render(request, 'tours/promocode_list.html', {
        'active_promocodes': active_promocodes,
        'archived_promocodes': archived_promocodes,
    })

class CountryListView(ListView):
    model = Country
    template_name = 'tours/country_list.html'
    context_object_name = 'countries'

class CountryDetailView(DetailView):
    model = Country
    template_name = 'tours/country_detail.html'
    context_object_name = 'country'

class CountryCreateView(CreateView):
    model = Country
    fields = ['name', 'description']
    template_name = 'tours/country_form.html'
    success_url = reverse_lazy('country-list')

class CountryUpdateView(UpdateView):
    model = Country
    fields = ['name', 'description']
    template_name = 'tours/country_form.html'
    success_url = reverse_lazy('country-list')

class CountryDeleteView(DeleteView):
    model = Country
    template_name = 'tours/country_confirm_delete.html'
    success_url = reverse_lazy('country-list')

class ClientProfileListView(ListView):
    model = ClientProfile
    template_name = 'tours/client_list.html'
    context_object_name = 'clients'

class ClientProfileDetailView(DetailView):
    model = ClientProfile
    template_name = 'tours/client_detail.html'
    context_object_name = 'client'

class ClientProfileCreateView(CreateView):
    model = ClientProfile
    fields = ['user', 'patronymic', 'address', 'phone_number', 'birth_date']
    template_name = 'tours/client_form.html'
    success_url = reverse_lazy('client-list')

class ClientProfileUpdateView(UpdateView):
    model = ClientProfile
    fields = ['user', 'patronymic', 'address', 'phone_number', 'birth_date']
    template_name = 'tours/client_form.html'
    success_url = reverse_lazy('client-list')

class ClientProfileDeleteView(DeleteView):
    model = ClientProfile
    template_name = 'tours/client_confirm_delete.html'
    success_url = reverse_lazy('client-list')

class EmployeeProfileListView(ListView):
    model = EmployeeProfile
    template_name = 'tours/employee_list.html'
    context_object_name = 'employees'

class EmployeeProfileDetailView(DetailView):
    model = EmployeeProfile
    template_name = 'tours/employee_detail.html'
    context_object_name = 'employee'

class EmployeeProfileCreateView(CreateView):
    model = EmployeeProfile
    fields = ['user', 'patronymic', 'position', 'photo', 'work_description', 'birth_date']
    template_name = 'tours/employee_form.html'
    success_url = reverse_lazy('employee-list')

class EmployeeProfileUpdateView(UpdateView):
    model = EmployeeProfile
    fields = ['user', 'patronymic', 'position', 'photo', 'work_description', 'birth_date']
    template_name = 'tours/employee_form.html'
    success_url = reverse_lazy('employee-list')

class EmployeeProfileDeleteView(DeleteView):
    model = EmployeeProfile
    template_name = 'tours/employee_confirm_delete.html'
    success_url = reverse_lazy('employee-list')

class SeasonClimateListView(ListView):
    model = SeasonClimate
    template_name = 'tours/seasonclimate_list.html'
    context_object_name = 'climates'

class SeasonClimateDetailView(DetailView):
    model = SeasonClimate
    template_name = 'tours/seasonclimate_detail.html'
    context_object_name = 'climate'

class SeasonClimateCreateView(CreateView):
    model = SeasonClimate
    fields = ['country', 'season', 'climate_description']
    template_name = 'tours/seasonclimate_form.html'
    success_url = reverse_lazy('seasonclimate-list')

class SeasonClimateUpdateView(UpdateView):
    model = SeasonClimate
    fields = ['country', 'season', 'climate_description']
    template_name = 'tours/seasonclimate_form.html'
    success_url = reverse_lazy('seasonclimate-list')

class SeasonClimateDeleteView(DeleteView):
    model = SeasonClimate
    template_name = 'tours/seasonclimate_confirm_delete.html'
    success_url = reverse_lazy('seasonclimate-list')

class HotelListView(ListView):
    model = Hotel
    template_name = 'tours/hotel_list.html'
    context_object_name = 'hotels'

class HotelDetailView(DetailView):
    model = Hotel
    template_name = 'tours/hotel_detail.html'
    context_object_name = 'hotel'

class HotelCreateView(CreateView):
    model = Hotel
    fields = ['name', 'country', 'stars', 'description', 'price_per_night', 'photo']
    template_name = 'tours/hotel_form.html'
    success_url = reverse_lazy('hotel-list')

class HotelUpdateView(UpdateView):
    model = Hotel
    fields = ['name', 'country', 'stars', 'description', 'price_per_night', 'photo']
    template_name = 'tours/hotel_form.html'
    success_url = reverse_lazy('hotel-list')

class HotelDeleteView(DeleteView):
    model = Hotel
    template_name = 'tours/hotel_confirm_delete.html'
    success_url = reverse_lazy('hotel-list')

class TourPackageListView(ListView):
    model = TourPackage
    template_name = 'tours/tourpackage_list.html'
    context_object_name = 'tourpackages'

class TourPackageDetailView(DetailView):
    model = TourPackage
    template_name = 'tours/tourpackage_detail.html'
    context_object_name = 'tourpackage'

class TourPackageCreateView(CreateView):
    model = TourPackage
    fields = ['name', 'hotel', 'duration_weeks', 'price', 'description', 'is_hot_deal', 'additional_services']
    template_name = 'tours/tourpackage_form.html'
    success_url = reverse_lazy('tourpackage-list')

class TourPackageUpdateView(UpdateView):
    model = TourPackage
    fields = ['name', 'hotel', 'duration_weeks', 'price', 'description', 'is_hot_deal', 'additional_services']
    template_name = 'tours/tourpackage_form.html'
    success_url = reverse_lazy('tourpackage-list')

class TourPackageDeleteView(DeleteView):
    model = TourPackage
    template_name = 'tours/tourpackage_confirm_delete.html'
    success_url = reverse_lazy('tourpackage-list')

class OrderListView(ListView):
    model = Order
    template_name = 'tours/order_list.html'
    context_object_name = 'orders'

class OrderDetailView(DetailView):
    model = Order
    template_name = 'tours/order_detail.html'
    context_object_name = 'order'

class OrderCreateView(CreateView):
    model = Order
    fields = ['client', 'tour_package', 'date', 'status', 'comment']
    template_name = 'tours/order_form.html'
    success_url = reverse_lazy('order-list')

class OrderUpdateView(UpdateView):
    model = Order
    fields = ['client', 'tour_package', 'date', 'status', 'comment']
    template_name = 'tours/order_form.html'
    success_url = reverse_lazy('order-list')

class OrderDeleteView(DeleteView):
    model = Order
    template_name = 'tours/order_confirm_delete.html'
    success_url = reverse_lazy('order-list')

class ArticleListView(ListView):
    model = Article
    template_name = 'tours/article_list.html'
    context_object_name = 'articles'

class ArticleDetailView(DetailView):
    model = Article
    template_name = 'tours/article_detail.html'
    context_object_name = 'article'

class ArticleCreateView(CreateView):
    model = Article
    fields = ['title', 'content', 'author', 'created_at', 'updated_at']
    template_name = 'tours/article_form.html'
    success_url = reverse_lazy('article-list')

class ArticleUpdateView(UpdateView):
    model = Article
    fields = ['title', 'content', 'author', 'created_at', 'updated_at']
    template_name = 'tours/article_form.html'
    success_url = reverse_lazy('article-list')

class ArticleDeleteView(DeleteView):
    model = Article
    template_name = 'tours/article_confirm_delete.html'
    success_url = reverse_lazy('article-list')

class FAQListView(ListView):
    model = FAQ
    template_name = 'tours/faq_list.html'
    context_object_name = 'faqs'

class FAQDetailView(DetailView):
    model = FAQ
    template_name = 'tours/faq_detail.html'
    context_object_name = 'faq'

class FAQCreateView(CreateView):
    model = FAQ
    fields = ['question', 'answer']
    template_name = 'tours/faq_form.html'
    success_url = reverse_lazy('faq-list')

class FAQUpdateView(UpdateView):
    model = FAQ
    fields = ['question', 'answer']
    template_name = 'tours/faq_form.html'
    success_url = reverse_lazy('faq-list')

class FAQDeleteView(DeleteView):
    model = FAQ
    template_name = 'tours/faq_confirm_delete.html'
    success_url = reverse_lazy('faq-list')

class VacancyListView(ListView):
    model = Vacancy
    template_name = 'tours/vacancy_list.html'
    context_object_name = 'vacancies'

class VacancyDetailView(DetailView):
    model = Vacancy
    template_name = 'tours/vacancy_detail.html'
    context_object_name = 'vacancy'

class VacancyCreateView(CreateView):
    model = Vacancy
    fields = ['title', 'description', 'requirements', 'salary', 'is_active']
    template_name = 'tours/vacancy_form.html'
    success_url = reverse_lazy('vacancy-list')

class VacancyUpdateView(UpdateView):
    model = Vacancy
    fields = ['title', 'description', 'requirements', 'salary', 'is_active']
    template_name = 'tours/vacancy_form.html'
    success_url = reverse_lazy('vacancy-list')

class VacancyDeleteView(DeleteView):
    model = Vacancy
    template_name = 'tours/vacancy_confirm_delete.html'
    success_url = reverse_lazy('vacancy-list')

class ReviewListView(ListView):
    model = Review
    template_name = 'tours/review_list.html'
    context_object_name = 'reviews'

class ReviewDetailView(DetailView):
    model = Review
    template_name = 'tours/review_detail.html'
    context_object_name = 'review'

class ReviewCreateView(CreateView):
    model = Review
    fields = ['author', 'tour_package', 'rating', 'text', 'created_at']
    template_name = 'tours/review_form.html'
    success_url = reverse_lazy('review-list')

class ReviewUpdateView(UpdateView):
    model = Review
    fields = ['author', 'tour_package', 'rating', 'text', 'created_at']
    template_name = 'tours/review_form.html'
    success_url = reverse_lazy('review-list')

class ReviewDeleteView(DeleteView):
    model = Review
    template_name = 'tours/review_confirm_delete.html'
    success_url = reverse_lazy('review-list')

class PromoCodeListView(ListView):
    model = PromoCode
    template_name = 'tours/promocode_list.html'
    context_object_name = 'promocodes'

class PromoCodeDetailView(DetailView):
    model = PromoCode
    template_name = 'tours/promocode_detail.html'
    context_object_name = 'promocode'

class PromoCodeCreateView(CreateView):
    model = PromoCode
    fields = ['code', 'discount_percent', 'valid_from', 'valid_to', 'is_active']
    template_name = 'tours/promocode_form.html'
    success_url = reverse_lazy('promocode-list')

class PromoCodeUpdateView(UpdateView):
    model = PromoCode
    fields = ['code', 'discount_percent', 'valid_from', 'valid_to', 'is_active']
    template_name = 'tours/promocode_form.html'
    success_url = reverse_lazy('promocode-list')

class PromoCodeDeleteView(DeleteView):
    model = PromoCode
    template_name = 'tours/promocode_confirm_delete.html'
    success_url = reverse_lazy('promocode-list')

class AboutPageContentListView(ListView):
    model = AboutPageContent
    template_name = 'tours/aboutpagecontent_list.html'
    context_object_name = 'about_contents'

class AboutPageContentDetailView(DetailView):
    model = AboutPageContent
    template_name = 'tours/aboutpagecontent_detail.html'
    context_object_name = 'about_content'

class AboutPageContentCreateView(CreateView):
    model = AboutPageContent
    fields = ['title', 'body', 'image', 'order']
    template_name = 'tours/aboutpagecontent_form.html'
    success_url = reverse_lazy('aboutpagecontent-list')

class AboutPageContentUpdateView(UpdateView):
    model = AboutPageContent
    fields = ['title', 'body', 'image', 'order']
    template_name = 'tours/aboutpagecontent_form.html'
    success_url = reverse_lazy('aboutpagecontent-list')

class AboutPageContentDeleteView(DeleteView):
    model = AboutPageContent
    template_name = 'tours/aboutpagecontent_confirm_delete.html'
    success_url = reverse_lazy('aboutpagecontent-list')

class CompanyVideoListView(ListView):
    model = CompanyVideo
    template_name = 'tours/companyvideo_list.html'
    context_object_name = 'companyvideos'

class CompanyVideoDetailView(DetailView):
    model = CompanyVideo
    template_name = 'tours/companyvideo_detail.html'
    context_object_name = 'companyvideo'

class CompanyVideoCreateView(CreateView):
    model = CompanyVideo
    fields = ['title', 'video_url', 'order', 'is_active']
    template_name = 'tours/companyvideo_form.html'
    success_url = reverse_lazy('companyvideo-list')

class CompanyVideoUpdateView(UpdateView):
    model = CompanyVideo
    fields = ['title', 'video_url', 'order', 'is_active']
    template_name = 'tours/companyvideo_form.html'
    success_url = reverse_lazy('companyvideo-list')

class CompanyVideoDeleteView(DeleteView):
    model = CompanyVideo
    template_name = 'tours/companyvideo_confirm_delete.html'
    success_url = reverse_lazy('companyvideo-list')

class CompanyLogoListView(ListView):
    model = CompanyLogo
    template_name = 'tours/companylogo_list.html'
    context_object_name = 'companylogos'

class CompanyLogoDetailView(DetailView):
    model = CompanyLogo
    template_name = 'tours/companylogo_detail.html'
    context_object_name = 'companylogo'

class CompanyLogoCreateView(CreateView):
    model = CompanyLogo
    fields = ['image', 'alt_text', 'is_active', 'order']
    template_name = 'tours/companylogo_form.html'
    success_url = reverse_lazy('companylogo-list')

class CompanyLogoUpdateView(UpdateView):
    model = CompanyLogo
    fields = ['image', 'alt_text', 'is_active', 'order']
    template_name = 'tours/companylogo_form.html'
    success_url = reverse_lazy('companylogo-list')

class CompanyLogoDeleteView(DeleteView):
    model = CompanyLogo
    template_name = 'tours/companylogo_confirm_delete.html'
    success_url = reverse_lazy('companylogo-list')


class CompanyHistoryItemListView(ListView):
    model = CompanyHistoryItem
    template_name = 'tours/companyhistoryitem_list.html'
    context_object_name = 'history_items'  # Or your preferred name like 'object_list'


class CompanyHistoryItemDetailView(DetailView):
    model = CompanyHistoryItem
    template_name = 'tours/companyhistoryitem_detail.html'
    context_object_name = 'object'  # Default is 'object', can be 'history_item' if you prefer


class CompanyHistoryItemCreateView(CreateView):
    model = CompanyHistoryItem
    fields = ['year', 'event_description']  # Corrected fields
    template_name = 'tours/companyhistoryitem_form.html'
    success_url = reverse_lazy('companyhistoryitem-list')  # Added namespace


class CompanyHistoryItemUpdateView(UpdateView):
    model = CompanyHistoryItem
    fields = ['year', 'event_description']  # Corrected fields
    template_name = 'tours/companyhistoryitem_form.html'

    # success_url = reverse_lazy('tours:companyhistoryitem-list') # Original

    def get_success_url(self):  # More typical for UpdateView
        return reverse_lazy('companyhistoryitem-detail', kwargs={'pk': self.object.pk})


class CompanyHistoryItemDeleteView(DeleteView):  # Ensure this view exists if used by templates
    model = CompanyHistoryItem
    template_name = 'tours/companyhistoryitem_confirm_delete.html'  # Standard template name
    success_url = reverse_lazy('companyhistoryitem-list')


class CompanyRequisiteListView(ListView):
    model = CompanyRequisite
    template_name = 'tours/companyrequisite_list.html'
    context_object_name = 'companyrequisite_list'

class CompanyRequisiteDetailView(DetailView):
    model = CompanyRequisite
    template_name = 'tours/companyrequisite_detail.html'
    context_object_name = 'companyrequisite_detail'

class CompanyRequisiteCreateView(CreateView):
    model = CompanyRequisite
    fields = ['name', 'value']
    template_name = 'tours/companyrequisite_form.html'
    success_url = reverse_lazy('companyrequisite-list')

class CompanyRequisiteUpdateView(UpdateView):
    model = CompanyRequisite
    fields = ['name', 'value']
    template_name = 'tours/companyrequisite_form.html'
    success_url = reverse_lazy('companyrequisite-list')

class CompanyRequisiteDeleteView(DeleteView):
    model = CompanyRequisite
    template_name = 'tours/companyrequisite_confirm_delete.html'
    success_url = reverse_lazy('companyrequisite-list')