from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from rest_framework.test import APIClient

from airport.models import Route, Airport
from airport.serializers import RouteListSerializer

ROUTE_URL = reverse("airport:route-list")


def sample_airport(**params):
    defaults = {
        "name": "airport",
        "closest_big_city": "city",
    }
    defaults.update(params)

    return Airport.objects.create(**defaults)


def sample_route(**params):
    source = sample_airport(name="airport1", closest_big_city="city1")
    destination = sample_airport(name="airport2", closest_big_city="city2")
    defaults = {
        "source": source,
        "destination": destination,
        "distance": 90,
    }
    defaults.update(params)

    return Route.objects.create(**defaults)


class UnauthenticatedRouteAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(ROUTE_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedRouteAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

    def test_list_routes(self):
        airport1 = sample_airport(name="airport1")
        airport2 = sample_airport(name="airport2")
        sample_route(source=airport1, destination=airport2)

        routes = Route.objects.all()
        serializer = RouteListSerializer(routes, many=True)

        response = self.client.get(ROUTE_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_filter_routes_by_airports(self):
        airport1 = sample_airport(name="airport1")
        airport2 = sample_airport(name="airport2")
        route1 = sample_route(source=airport1, destination=airport2)
        route2 = sample_route(source=airport2, destination=airport1)

        serializer1 = RouteListSerializer(route1)
        serializer2 = RouteListSerializer(route2)

        response = self.client.get(ROUTE_URL, {"source": airport1.name})

        self.assertIn(serializer1.data, response.data)
        self.assertNotIn(serializer2.data, response.data)

        response = self.client.get(ROUTE_URL, {"destination": airport2.name})

        self.assertIn(serializer1.data, response.data)
        self.assertNotIn(serializer2.data, response.data)

    def test_create_route_forbidden(self):
        airport1 = sample_airport(name="airport1")
        airport2 = sample_airport(name="airport2")
        payload = {
            "source": airport1,
            "destination": airport2,
            "distance": 90,
        }

        response = self.client.post(ROUTE_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminRouteAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_route(self):
        airport1 = sample_airport(name="airport1")
        airport2 = sample_airport(name="airport2")
        payload = {
            "source": airport1.id,
            "destination": airport2.id,
            "distance": 90,
        }

        response = self.client.post(ROUTE_URL, payload)
        route = Route.objects.get(id=response.data["id"])

        source = route.source
        del payload["source"]

        destination = route.destination
        del payload["destination"]

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        for key in payload:
            self.assertEqual(payload[key], getattr(route, key))

        self.assertEqual(airport1, source)
        self.assertEqual(airport2, destination)
