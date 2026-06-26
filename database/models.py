from sqlalchemy import BigInteger, String, Boolean, DateTime, text, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from datetime import date, datetime

class Base(DeclarativeBase):
    pass

class Vacancy(Base):
    __tablename__ = "vacancies"
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    company: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(String(512))

    salary: Mapped[str | None] = mapped_column(String(500), nullable=True)
    experience: Mapped[str | None] = mapped_column(String(500), nullable=True)

    is_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    is_applied: Mapped[bool] = mapped_column(Boolean, default=False)
    parsed_at: Mapped[datetime] = mapped_column(
        DateTime, 
        server_default=text("TIMEZONE('utc', now())")
    )

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(32))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        server_default=text("TIMEZONE('utc', now())")
    )
    search_keyword: Mapped[str] = mapped_column(String(100), default="FastAPI")
    cover_letter_template: Mapped[str | None] = mapped_column(
        String(2000),
        default="Здравствуйте! Меня очень заинтересовала ваша вакансия. Мой стек..."
    )