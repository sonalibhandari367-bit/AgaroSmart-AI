from pydantic import BaseModel, ConfigDict, Field


class RecommendationInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid", allow_inf_nan=False)
    nitrogen: float = Field(ge=0, le=200)
    phosphorus: float = Field(ge=0, le=200)
    potassium: float = Field(ge=0, le=250)
    ph: float = Field(ge=0, le=14)
    temperature_c: float = Field(ge=-20, le=60)
    humidity_pct: float = Field(ge=0, le=100)
    rainfall_mm: float = Field(ge=0, le=2000)
    soil_type: str | None = Field(default=None, max_length=80)
    location: str | None = Field(default=None, max_length=200)
    growing_season: str | None = Field(default=None, max_length=80)


class RecommendationRequest(RecommendationInput):
    limit: int = Field(default=5, ge=1, le=22)
