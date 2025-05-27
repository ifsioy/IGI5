import pytest
from django.core.exceptions import ValidationError
from tours.models import ClientProfile, TourPackage, Order, Country, Hotel
from django.contrib.auth.models import User
from datetime import date

@pytest.mark.django_db
def test_client_profile_creation():
    user = User.objects.create_user(username="testuser", password="password")
    client = ClientProfile.objects.create(
        user=user,
        patronymic="Иванович",
        address="ул. Пушкина, д.1",
        phone_number="+375 (29) 123-45-67",
        birth_date=date(2000, 1, 1)
    )
    assert client.user.username == "testuser"
    assert client.phone_number == "+375 (29) 123-45-67"

@pytest.mark.django_db
def test_tour_package_price_constraint():
    user = User.objects.create_user(username="testuser", password="password")
    client = ClientProfile.objects.create(
        user=user,
        patronymic="Иванович",
        address="ул. Пушкина, д.1",
        phone_number="+375 (29) 123-45-67",
        birth_date=date(2000, 1, 1),
    )

    country = Country.objects.create(name="Россия", description="Очень холодно!")
    hotel = Hotel.objects.create(name="Hilton", country=country, stars=4, price_per_night=5000)

    tour = TourPackage.objects.create(
        name="Москва Зимой",
        hotel=hotel,
        duration_weeks=2,
        price=50000,
        start_date=date(2025, 1, 1),
        client=client,
    )

    assert tour.price == 50000
    assert tour.client == client

@pytest.mark.django_db
def test_order_status():
    user = User.objects.create_user(username="testclient", password="password")
    order = Order.objects.create(
        client=user,
        departure_date=date(2025, 6, 1),
        total_price=60000,
        status="pending"
    )
    assert order.status == "pending"
    order.status = "confirmed"
    order.save()
    assert order.status == "confirmed"