"""Тесты для роутеров POST /subscribe, DELETE /subscribe/{id}, GET /subscriptions."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from database import get_db
from main import app
from models.weather import WeatherResponse

WEATHER_RESPONSE = WeatherResponse(
    city="London",
    temp=15.5,
    humidity=72,
    description="light rain",
)


def _make_mock_db() -> AsyncMock:
    """Создаёт мок AsyncSession для подмены зависимости get_db."""
    return AsyncMock()


def _override_get_db(mock_db: AsyncMock):
    """Возвращает async-генератор, подставляющий мок-сессию."""

    async def _get_db_override():
        yield mock_db

    return _get_db_override


class TestPostSubscribe:
    """Тесты для POST /subscribe."""

    def test_create_subscription_happy_path(self) -> None:
        """Успешное создание подписки возвращает 201 с subscription_id, city, email, weather."""
        mock_db = _make_mock_db()
        app.dependency_overrides[get_db] = _override_get_db(mock_db)

        mock_user = MagicMock()
        mock_user.id = 1

        mock_subscription = MagicMock()
        mock_subscription.id = 42

        with (
            patch("routers.subscription.get_or_create_user", return_value=mock_user) as _,
            patch(
                "routers.subscription.get_subscription_by_user_city", return_value=None
            ) as _,
            patch(
                "routers.subscription._fetch_weather", return_value=WEATHER_RESPONSE
            ) as _,
            patch(
                "routers.subscription.create_subscription", return_value=mock_subscription
            ) as _,
        ):
            client = TestClient(app)
            response = client.post(
                "/subscribe",
                json={"email": "user@example.com", "city": "London"},
            )

        app.dependency_overrides.clear()

        assert response.status_code == 201
        data = response.json()
        assert data["subscription_id"] == 42
        assert data["city"] == "London"
        assert data["email"] == "user@example.com"
        assert data["weather"]["temp"] == 15.5
        assert data["weather"]["humidity"] == 72

    def test_create_subscription_duplicate_returns_409(self) -> None:
        """Дубликат подписки возвращает 409 Conflict."""
        mock_db = _make_mock_db()
        app.dependency_overrides[get_db] = _override_get_db(mock_db)

        mock_user = MagicMock()
        mock_user.id = 1

        existing_subscription = MagicMock()

        with (
            patch("routers.subscription.get_or_create_user", return_value=mock_user) as _,
            patch(
                "routers.subscription.get_subscription_by_user_city",
                return_value=existing_subscription,
            ) as _,
        ):
            client = TestClient(app)
            response = client.post(
                "/subscribe",
                json={"email": "user@example.com", "city": "London"},
            )

        app.dependency_overrides.clear()

        assert response.status_code == 409
        assert response.json()["detail"] == "Subscription already exists"

    def test_create_subscription_city_not_found_returns_404(self) -> None:
        """Если _fetch_weather бросает HTTPException 404, роутер возвращает 404."""
        mock_db = _make_mock_db()
        app.dependency_overrides[get_db] = _override_get_db(mock_db)

        mock_user = MagicMock()
        mock_user.id = 1

        with (
            patch("routers.subscription.get_or_create_user", return_value=mock_user) as _,
            patch(
                "routers.subscription.get_subscription_by_user_city", return_value=None
            ) as _,
            patch(
                "routers.subscription._fetch_weather",
                side_effect=HTTPException(status_code=404, detail="City not found"),
            ) as _,
        ):
            client = TestClient(app)
            response = client.post(
                "/subscribe",
                json={"email": "user@example.com", "city": "UnknownCity"},
            )

        app.dependency_overrides.clear()

        assert response.status_code == 404
        assert response.json()["detail"] == "City not found"


    def test_create_subscription_invalid_email_returns_422(self) -> None:
        """Невалидный email возвращает 422 Unprocessable Entity."""
        client = TestClient(app)
        response = client.post(
            "/subscribe",
            json={"email": "not-an-email", "city": "London"},
        )

        assert response.status_code == 422


class TestDeleteSubscription:
    """Тесты для DELETE /subscribe/{id}."""

    def test_delete_subscription_happy_path(self) -> None:
        """Успешное удаление подписки возвращает 204 без тела."""
        mock_db = _make_mock_db()
        app.dependency_overrides[get_db] = _override_get_db(mock_db)

        with patch("routers.subscription.delete_subscription", return_value=True) as _:
            client = TestClient(app)
            response = client.delete("/subscribe/42")

        app.dependency_overrides.clear()

        assert response.status_code == 204
        assert response.content == b""

    def test_delete_subscription_not_found_returns_404(self) -> None:
        """Подписка не найдена — возвращает 404."""
        mock_db = _make_mock_db()
        app.dependency_overrides[get_db] = _override_get_db(mock_db)

        with patch("routers.subscription.delete_subscription", return_value=False) as _:
            client = TestClient(app)
            response = client.delete("/subscribe/999")

        app.dependency_overrides.clear()

        assert response.status_code == 404
        assert response.json()["detail"] == "Subscription not found"


class TestGetSubscriptions:
    """Тесты для GET /subscriptions."""

    def test_get_subscriptions_returns_list_with_total(self) -> None:
        """GET /subscriptions возвращает список подписок с полем total."""
        mock_db = _make_mock_db()
        app.dependency_overrides[get_db] = _override_get_db(mock_db)

        mock_sub_1 = MagicMock()
        mock_sub_1.id = 1
        mock_sub_1.city = "London"

        mock_sub_2 = MagicMock()
        mock_sub_2.id = 2
        mock_sub_2.city = "Paris"

        rows = [
            (mock_sub_1, "alice@example.com"),
            (mock_sub_2, "bob@example.com"),
        ]

        with patch("routers.subscription.get_all_subscriptions", return_value=rows) as _:
            client = TestClient(app)
            response = client.get("/subscriptions")

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["subscriptions"]) == 2
        assert data["subscriptions"][0]["subscription_id"] == 1
        assert data["subscriptions"][0]["city"] == "London"
        assert data["subscriptions"][0]["email"] == "alice@example.com"
        assert data["subscriptions"][1]["subscription_id"] == 2
        assert data["subscriptions"][1]["city"] == "Paris"
        assert data["subscriptions"][1]["email"] == "bob@example.com"

    def test_get_subscriptions_empty_returns_200_with_zero_total(self) -> None:
        """GET /subscriptions при отсутствии подписок возвращает 200 с пустым списком и total=0."""
        mock_db = _make_mock_db()
        app.dependency_overrides[get_db] = _override_get_db(mock_db)

        with patch("routers.subscription.get_all_subscriptions", return_value=[]) as _:
            client = TestClient(app)
            response = client.get("/subscriptions")

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["subscriptions"] == []


class TestPatchSubscription:
    """Тесты для PATCH /subscribe/{id}."""

    def test_update_subscription_notification_time_happy_path(self) -> None:
        """Успешное обновление времени уведомления возвращает 200 с обновлённой подпиской."""
        from datetime import datetime, time as time_type

        mock_db = _make_mock_db()
        app.dependency_overrides[get_db] = _override_get_db(mock_db)

        mock_updated = MagicMock()
        mock_updated.id = 1
        mock_updated.city = "Moscow"
        mock_updated.notification_time = time_type(18, 30)
        mock_updated.is_active = True
        mock_updated.created_at = datetime(2026, 4, 26, 10, 0, 0)

        mock_result = MagicMock()
        mock_row = (None, "user@example.com")
        mock_result.first.return_value = mock_row
        mock_db.execute.return_value = mock_result

        with patch("routers.subscription.update_subscription", return_value=mock_updated) as _:
            client = TestClient(app)
            response = client.patch(
                "/subscribe/1",
                json={"notification_time": "18:30"},
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["subscription_id"] == 1
        assert data["city"] == "Moscow"
        assert data["email"] == "user@example.com"
        assert data["notification_time"] == "18:30:00"
        assert data["is_active"] is True

    def test_update_subscription_is_active_happy_path(self) -> None:
        """Успешное обновление активности подписки возвращает 200."""
        from datetime import datetime, time as time_type

        mock_db = _make_mock_db()
        app.dependency_overrides[get_db] = _override_get_db(mock_db)

        mock_updated = MagicMock()
        mock_updated.id = 2
        mock_updated.city = "London"
        mock_updated.notification_time = time_type(9, 0)
        mock_updated.is_active = False
        mock_updated.created_at = datetime(2026, 4, 26, 10, 0, 0)

        mock_result = MagicMock()
        mock_row = (None, "test@example.com")
        mock_result.first.return_value = mock_row
        mock_db.execute.return_value = mock_result

        with patch("routers.subscription.update_subscription", return_value=mock_updated) as _:
            client = TestClient(app)
            response = client.patch(
                "/subscribe/2",
                json={"is_active": False},
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["subscription_id"] == 2
        assert data["is_active"] is False

    def test_update_subscription_both_fields_happy_path(self) -> None:
        """Успешное обновление обоих полей одновременно возвращает 200."""
        from datetime import datetime, time as time_type

        mock_db = _make_mock_db()
        app.dependency_overrides[get_db] = _override_get_db(mock_db)

        mock_updated = MagicMock()
        mock_updated.id = 3
        mock_updated.city = "Paris"
        mock_updated.notification_time = time_type(20, 0)
        mock_updated.is_active = False
        mock_updated.created_at = datetime(2026, 4, 26, 10, 0, 0)

        mock_result = MagicMock()
        mock_row = (None, "alice@example.com")
        mock_result.first.return_value = mock_row
        mock_db.execute.return_value = mock_result

        with patch("routers.subscription.update_subscription", return_value=mock_updated) as _:
            client = TestClient(app)
            response = client.patch(
                "/subscribe/3",
                json={"notification_time": "20:00", "is_active": False},
            )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["subscription_id"] == 3
        assert data["city"] == "Paris"
        assert data["notification_time"] == "20:00:00"
        assert data["is_active"] is False

    def test_update_subscription_not_found_returns_404(self) -> None:
        """Подписка не найдена — возвращает 404."""
        mock_db = _make_mock_db()
        app.dependency_overrides[get_db] = _override_get_db(mock_db)

        with patch("routers.subscription.update_subscription", return_value=None) as _:
            client = TestClient(app)
            response = client.patch(
                "/subscribe/999",
                json={"is_active": False},
            )

        app.dependency_overrides.clear()

        assert response.status_code == 404
        assert response.json()["detail"] == "Subscription not found"

    def test_update_subscription_empty_body_returns_422(self) -> None:
        """Пустое тело запроса возвращает 422 (Pydantic валидация)."""
        client = TestClient(app)
        response = client.patch(
            "/subscribe/1",
            json={},
        )

        assert response.status_code == 422

    def test_update_subscription_invalid_time_returns_422(self) -> None:
        """Невалидное время возвращает 422 (Pydantic валидация)."""
        client = TestClient(app)
        response = client.patch(
            "/subscribe/1",
            json={"notification_time": "25:00"},
        )

        assert response.status_code == 422
