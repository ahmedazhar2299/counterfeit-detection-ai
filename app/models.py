from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


class Listing(Base):
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(512), nullable=False)
    description = Column(Text, nullable=False)
    brand = Column(String(128), nullable=False)
    category = Column(String(128), nullable=False)
    price = Column(Float, nullable=False)
    currency = Column(String(8), nullable=False, default="USD")
    seller_age_days = Column(Integer, nullable=True)
    seller_rating = Column(Float, nullable=True)
    seller_sales_count = Column(Integer, nullable=True)
    review_count = Column(Integer, nullable=True)
    shipping_country = Column(String(64), nullable=True)
    return_policy_days = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    analyses = relationship("Analysis", back_populates="listing", cascade="all, delete-orphan")


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False)
    structured_prob = Column(Float, nullable=False)
    text_prob = Column(Float, nullable=False)
    fused_prob = Column(Float, nullable=False)
    risk_score = Column(Float, nullable=False)
    action = Column(String(16), nullable=False)
    explanations_json = Column(JSON, nullable=False)
    highlights_json = Column(JSON, nullable=False)
    model_version = Column(String(64), nullable=False)
    training_timestamp = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    listing = relationship("Listing", back_populates="analyses")
    feedback = relationship("Feedback", back_populates="analysis", cascade="all, delete-orphan")


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False)
    label = Column(String(32), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    analysis = relationship("Analysis", back_populates="feedback")


class TrainingRun(Base):
    __tablename__ = "training_runs"

    id = Column(Integer, primary_key=True, index=True)
    model_version = Column(String(64), nullable=False)
    metrics_json = Column(JSON, nullable=False)
    artifacts_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
