from io import BytesIO
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest

from app import create_app
from app.core.config import TestConfig
from app.db.extensions import db
from app.models.user import User
from app.services.user_service import hash_password


class TestingConfig(TestConfig):
    JWT_SECRET_KEY = "test-secret-key-for-learning-project-2026"


@pytest.fixture()
def app():
    app = create_app(TestingConfig)

    with app.app_context():
        db.drop_all()
        db.create_all()
        admin = User(
            username="admin",
            password_hash=hash_password("admin123456"),
            role="admin",
            status="active",
        )
        user = User(
            username="student",
            password_hash=hash_password("student123"),
            role="user",
            status="active",
        )
        db.session.add_all([admin, user])
        db.session.commit()

    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def sample_image_file():
    from PIL import Image

    image = Image.new("RGB", (200, 200), color=(255, 255, 255))
    output = BytesIO()
    image.save(output, format="PNG")
    output.seek(0)
    return output


def login(client, username: str, password: str) -> str:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    return response.get_json()["token"]
