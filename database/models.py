from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# ============================================================================
# 2. GAMES (Dimensão / Metadados)
# ============================================================================
class Game(Base):
    __tablename__ = "games"

    universe_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    root_place_id: Mapped[int | None] = mapped_column(BigInteger)
    creator_id: Mapped[int | None] = mapped_column(BigInteger)
    creator_name: Mapped[str | None] = mapped_column(Text)
    created_at_roblox: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    first_discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))

    snapshots: Mapped[list["GameSnapshot"]] = relationship(
        back_populates="game", cascade="all, delete-orphan", passive_deletes=True
    )
    passes: Mapped[list["GamePass"]] = relationship(
        back_populates="game", cascade="all, delete-orphan", passive_deletes=True
    )
    features: Mapped["MLGameFeatures | None"] = relationship(
        back_populates="game", cascade="all, delete-orphan", passive_deletes=True, uselist=False
    )


# ============================================================================
# 3. GAME SNAPSHOTS (Série Temporal de Performance)
# ============================================================================
class GameSnapshot(Base):
    __tablename__ = "game_snapshots"
    __table_args__ = (
        Index("ix_game_snapshots_universe_collected", "universe_id", "collected_at"),
        Index("ix_game_snapshots_collected_at", "collected_at"),
    )

    snapshot_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    universe_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("games.universe_id", ondelete="CASCADE"), nullable=False
    )
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    entry_price_robux: Mapped[int | None] = mapped_column(Integer, server_default=text("0"))

    # Métricas instantâneas e acumuladas
    genre_l1: Mapped[str | None] = mapped_column(String(100))
    genre_l2: Mapped[str | None] = mapped_column(String(100))
    playing: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    visits: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    favorites: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    up_votes: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    down_votes: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    max_players: Mapped[int | None] = mapped_column(Integer)

    updated_at_roblox: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Em quais listas (sorts) o jogo estava neste momento
    active_sorts: Mapped[list[str] | None] = mapped_column(
        ARRAY(Text), server_default=text("'{}'")
    )

    # No DBML estava como "timestamps" (tipo inválido); usei Date para particionar/agrupar por dia
    snapshot_date: Mapped[date | None] = mapped_column(Date)

    game: Mapped["Game"] = relationship(back_populates="snapshots")


# ============================================================================
# 4. GAME PASSES (Monetização)
# ============================================================================
class GamePass(Base):
    __tablename__ = "game_passes"
    __table_args__ = (Index("ix_game_passes_universe_id", "universe_id"),)

    pass_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    universe_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("games.universe_id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    price_robux: Mapped[int | None] = mapped_column(Integer)  # NULL se não estiver à venda
    is_for_sale: Mapped[bool | None] = mapped_column(Boolean, server_default=text("true"))
    last_checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    game: Mapped["Game"] = relationship(back_populates="passes")


# ============================================================================
# 5. ML GAME FEATURES (Feature Store)
# ============================================================================
class MLGameFeatures(Base):
    __tablename__ = "ml_game_features"

    universe_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("games.universe_id", ondelete="CASCADE"),
        primary_key=True,
        autoincrement=False,
    )
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Tração e crescimento
    age_in_days: Mapped[float | None] = mapped_column(Float)
    avg_playing_24h: Mapped[float | None] = mapped_column(Float)
    avg_playing_7d: Mapped[float | None] = mapped_column(Float)
    playing_growth_rate_24h: Mapped[float | None] = mapped_column(Float)
    playing_acceleration: Mapped[float | None] = mapped_column(Float)
    visits_gained_24h: Mapped[int | None] = mapped_column(BigInteger)

    # Engajamento e retenção
    approval_ratio: Mapped[float | None] = mapped_column(Float)
    favorites_per_1k_visits: Mapped[float | None] = mapped_column(Float)

    # Monetização
    total_gamepasses: Mapped[int | None] = mapped_column(Integer, server_default=text("0"))
    avg_gamepass_price: Mapped[float | None] = mapped_column(Float, server_default=text("0"))
    max_gamepass_price: Mapped[int | None] = mapped_column(Integer, server_default=text("0"))

    # NLP e clusterização
    extracted_mechanics: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    description_embedding: Mapped[str | None] = mapped_column(String)
    assigned_cluster_id: Mapped[int | None] = mapped_column(Integer)

    game: Mapped["Game"] = relationship(back_populates="features")


if __name__ == "__main__":
    from sqlalchemy import create_engine

    engine = create_engine("postgresql+psycopg://user:password@localhost:5432/roblox")
    Base.metadata.create_all(engine)
