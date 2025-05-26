from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from .models import Country, ClientProfile, EmployeeProfile, SeasonClimate, Hotel, TourPackage, Order, Article, FAQ, \
    Vacancy, Review, PromoCode, AboutPageContent, CompanyVideo, CompanyLogo, CompanyHistoryItem, CompanyRequisite



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
    context_object_name = 'history_items'

class CompanyHistoryItemDetailView(DetailView):
    model = CompanyHistoryItem
    template_name = 'tours/companyhistoryitem_detail.html'
    context_object_name = 'history_item'

class CompanyHistoryItemCreateView(CreateView):
    model = CompanyHistoryItem
    fields = ['title', 'description', 'date', 'image', 'order']
    template_name = 'tours/companyhistoryitem_form.html'
    success_url = reverse_lazy('companyhistoryitem-list')

class CompanyHistoryItemUpdateView(UpdateView):
    model = CompanyHistoryItem
    fields = ['title', 'description', 'date', 'image', 'order']
    template_name = 'tours/companyhistoryitem_form.html'
    success_url = reverse_lazy('companyhistoryitem-list')

class CompanyHistoryItemDeleteView(DeleteView):
    model = CompanyHistoryItem
    template_name = 'tours/companyhistoryitem_confirm_delete.html'
    success_url = reverse_lazy('companyhistoryitem-list')

class CompanyRequisiteListView(ListView):
    model = CompanyRequisite
    template_name = 'tours/companyrequisite_list.html'
    context_object_name = 'companyrequisites'

class CompanyRequisiteDetailView(DetailView):
    model = CompanyRequisite
    template_name = 'tours/companyrequisite_detail.html'
    context_object_name = 'companyrequisite'

class CompanyRequisiteCreateView(CreateView):
    model = CompanyRequisite
    fields = ['name', 'value', 'order']
    template_name = 'tours/companyrequisite_form.html'
    success_url = reverse_lazy('companyrequisite-list')

class CompanyRequisiteUpdateView(UpdateView):
    model = CompanyRequisite
    fields = ['name', 'value', 'order']
    template_name = 'tours/companyrequisite_form.html'
    success_url = reverse_lazy('companyrequisite-list')

class CompanyRequisiteDeleteView(DeleteView):
    model = CompanyRequisite
    template_name = 'tours/companyrequisite_confirm_delete.html'
    success_url = reverse_lazy('companyrequisite-list')