from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

write_engine = create_engine(
    settings.mysql_write_url,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    echo=settings.debug,
)

WriteSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=write_engine)

Base = declarative_base()


def get_db():
    db = WriteSessionLocal()
    try:
        yield db
    finally:
        db.close()
