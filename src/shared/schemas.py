from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    expires_at: datetime


class PredictionRequest(BaseModel):
    text: str = Field(min_length=5, max_length=500)


class PredictionResponse(BaseModel):
    label: str
    confidence: float
    processing_time_ms: float


class HistoryItem(BaseModel):
    text: str
    predicted_label: str
    confidence: float
    created_at: datetime


class ClassifyResponse(BaseModel):
    result: PredictionResponse
    history: list[HistoryItem]


class HealthResponse(BaseModel):
    status: str


class ModelPredictionRequest(BaseModel):
    text: str


class ModelPredictionResponse(BaseModel):
    label: str
    confidence: float
    processing_time_ms: float
