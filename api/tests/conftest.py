import os

# app.* 를 import 하기 전에 DATABASE_URL을 테스트 DB로 돌려놓아야 한다 —
# app.config.settings는 import 시점에 값을 고정한다.
TEST_DB_NAME = "ansim_test"
ADMIN_DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+psycopg://ansim:ansim@db:5432/ansim")
TEST_DATABASE_URL = ADMIN_DATABASE_URL.rsplit("/", 1)[0] + "/" + TEST_DB_NAME
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

import io  # noqa: E402
import zipfile  # noqa: E402

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402


def _ensure_test_database():
    """compose의 postgres에 ansim_test가 없으면 만든다(마이그레이션 도구 없음 — 가정)."""
    admin = create_engine(ADMIN_DATABASE_URL, isolation_level="AUTOCOMMIT")
    try:
        with admin.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": TEST_DB_NAME}
            ).scalar()
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{TEST_DB_NAME}"'))
    finally:
        admin.dispose()


@pytest.fixture(scope="session")
def database():
    _ensure_test_database()
    from app.db import engine
    from app.models import Base

    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest_asyncio.fixture
async def client(database):
    # ASGITransport는 lifespan을 돌리지 않는다 — 테이블 생성은 database 픽스처가 맡는다.
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        yield c


@pytest.fixture
def small_zip():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("app/main.py", "import os\nx = 1\n")
    return buf.getvalue()
