import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from tours.models import Country, Hotel, TourPackage, ClientProfile

@pytest.mark.django_db
def test_tours_catalog_view(client):
    user = User.objects.create_user(username="testuser", password="password")
    client_profile = ClientProfile.objects.create(
        user=user,
        patronymic="Иванович",
        address="ул. Пушкина, д.1",
        phone_number="+375 (29) 123-45-67",
        birth_date="2000-01-01",
    )
    country = Country.objects.create(name="Греция", description="Солнечная страна")
    hotel = Hotel.objects.create(name="Santorini Resort", country=country, stars=5, price_per_night=10000)
    TourPackage.objects.create(
        name="Греческие Каникулы",
        hotel=hotel,
        duration_weeks=2,
        price=200000,
        client=client_profile,
    )

    response = client.get(reverse("tours-catalog"))
    assert response.status_code == 200
    assert "Греческие Каникулы" in response.content.decode()