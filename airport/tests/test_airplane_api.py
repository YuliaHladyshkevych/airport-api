import os
import tempfile

from PIL import Image

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from rest_framework.test import APIClient

from airport.models import Airplane, AirplaneType
from airport.serializers import AirplaneListSerializer, AirplaneSerializer


AIRPLANE_URL = reverse("airport:airplane-list")


def sample_airplane_type(**params):
    defaults = {
        "name": "airplane type",
    }
    defaults.update(params)
    return AirplaneType.objects.create(**defaults)


def sample_airplane(**params):
    defaults = {
        "name": "airplane",
        "rows": 10,
        "seats_in_row": 6,
        "airplane_type": sample_airplane_type(),
    }
    defaults.update(params)

    return Airplane.objects.create(**defaults)


def image_upload_url(airplane_id):
    """Return URL for recipe image upload"""
    return reverse("airport:airplane-upload-image", args=[airplane_id])


class UnauthenticatedAirplaneAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        response = self.client.get(AIRPLANE_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedAirplaneAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

    def test_airplanes_list(self):
        sample_airplane()
        sample_airplane()

        response = self.client.get(AIRPLANE_URL)

        airplanes = Airplane.objects.order_by("name")
        serializer = AirplaneListSerializer(airplanes, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_create_airplane_forbidden(self):
        payload = {
            "name": "airplane",
            "rows": 10,
            "seats_in_row": 6,
            "airplane_type": sample_airplane_type(),
        }

        response = self.client.post(AIRPLANE_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_airplane_property(self):
        sample_airplane_type()
        airplane = sample_airplane()

        expected_capacity = airplane.rows * airplane.seats_in_row

        serializer = AirplaneSerializer(airplane)

        self.assertEqual(serializer.data["capacity"], expected_capacity)


class AdminAirplaneAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_airplane(self):
        airplane_type1 = sample_airplane_type()
        payload = {
            "name": "airplane",
            "rows": 10,
            "seats_in_row": 6,
            "airplane_type": airplane_type1.id,
        }

        response = self.client.post(AIRPLANE_URL, payload)
        airplane = Airplane.objects.get(id=response.data["id"])

        airplane_type = airplane.airplane_type
        del payload["airplane_type"]

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        for key in payload.keys():
            self.assertEqual(payload[key], getattr(airplane, key))

        self.assertEqual(airplane_type1, airplane_type)


class AirplaneImageUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)

        self.sample_airplane_type = sample_airplane_type()
        self.airplane = sample_airplane(airplane_type=self.sample_airplane_type)

    def tearDown(self):
        self.airplane.image.delete()

    def test_upload_image_to_airplane(self):
        """Test uploading an image to airplane"""
        url = image_upload_url(self.airplane.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            response = self.client.post(url, {"image": ntf}, format="multipart")
        self.airplane.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("image", response.data)
        self.assertTrue(os.path.exists(self.airplane.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image"""
        url = image_upload_url(self.airplane.id)
        response = self.client.post(url, {"image": "not image"}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_image_url_is_shown_on_airplane_list(self):
        url = image_upload_url(self.airplane.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        response = self.client.get(AIRPLANE_URL)

        self.assertIn("image", response.data[0].keys())
