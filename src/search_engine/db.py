"""Database models and session management.

Schema is a simplified subset of the full design (docs/schema/schema.dbml),
scoped to what the MVP needs: universities, professors, opportunities, and search cache.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker

from . import config


class Base(DeclarativeBase):
    pass


class University(Base):
    __tablename__ = "universities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    openalex_id = Column(String(256), unique=True, nullable=True)
    name = Column(String(512), nullable=False)
    country_code = Column(String(8), nullable=True)
    type = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    professors = relationship("Professor", back_populates="university")


class Professor(Base):
    __tablename__ = "professors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    openalex_id = Column(String(256), unique=True, nullable=True)
    name = Column(String(512), nullable=False)
    orcid = Column(String(64), nullable=True)
    university_id = Column(Integer, ForeignKey("universities.id"), nullable=True)
    homepage_url = Column(Text, nullable=True)
    lab_url = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    university = relationship("University", back_populates="professors")
    opportunities = relationship("ResearchOpportunity", back_populates="professor")
    hiring_signals = relationship("LabHiringSignal", back_populates="professor", cascade="all, delete-orphan")


def _default_hiring_signal_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=config.HIRING_SIGNAL_TTL_DAYS)


class LabHiringSignal(Base):
    __tablename__ = "lab_hiring_signals"
    __table_args__ = (UniqueConstraint("professor_id", "hiring_url"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    professor_id = Column(Integer, ForeignKey("professors.id"), nullable=False, index=True)
    lab_url = Column(Text, nullable=True)
    hiring_url = Column(Text, nullable=False)
    hiring_paragraph = Column(Text, nullable=False)
    keywords_matched = Column(ARRAY(Text), nullable=True)
    scraped_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime(timezone=True), default=_default_hiring_signal_expiry, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    professor = relationship("Professor", back_populates="hiring_signals")


class ResearchOpportunity(Base):
    __tablename__ = "research_opportunities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    professor_id = Column(Integer, ForeignKey("professors.id"), nullable=False)
    query_topic = Column(Text, nullable=False)
    relevance_score = Column(Float, nullable=False, default=0.0)
    paper_count = Column(Integer, nullable=False, default=0)
    total_citations = Column(Integer, nullable=False, default=0)
    latest_paper_date = Column(String(32), nullable=True)
    latest_paper_title = Column(Text, nullable=True)
    composite_score = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    professor = relationship("Professor", back_populates="opportunities")


class SearchCache(Base):
    """Stores cached search results keyed by a normalised query hash."""

    __tablename__ = "search_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    query_hash = Column(String(64), unique=True, nullable=False, index=True)
    raw_query = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=False)

    results = relationship("SearchCacheResult", back_populates="cache_entry", cascade="all, delete-orphan")


class SearchCacheResult(Base):
    __tablename__ = "search_cache_results"
    __table_args__ = (UniqueConstraint("cache_id", "rank"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    cache_id = Column(Integer, ForeignKey("search_cache.id", ondelete="CASCADE"), nullable=False)
    opportunity_id = Column(Integer, ForeignKey("research_opportunities.id"), nullable=False)
    rank = Column(Integer, nullable=False)

    cache_entry = relationship("SearchCache", back_populates="results")
    opportunity = relationship("ResearchOpportunity")


_engine = None
_SessionLocal = None


def _engine_kwargs() -> dict:
    """Build connect_args for local vs hosted PostgreSQL."""
    kwargs: dict = {"echo": False, "pool_pre_ping": True}
    url = config.DATABASE_URL
    is_remote = not any(h in url for h in ("localhost", "127.0.0.1", "host.docker.internal"))
    if is_remote:
        kwargs["connect_args"] = {"sslmode": "require"}
    return kwargs


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(config.DATABASE_URL, **_engine_kwargs())
    return _engine


def get_session() -> Session:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine())
    return _SessionLocal()


def init_db():
    engine = get_engine()
    Base.metadata.create_all(engine)
