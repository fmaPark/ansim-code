from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
# expire_on_commit=False: 파이프라인이 commit 뒤에도 같은 Scan 객체의 필드를 계속 읽는다.
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
