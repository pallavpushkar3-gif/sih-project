"""Supported immutable FD001 history contract; atomic batch validation."""

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, model_validator


class HistoryRow(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    cycle: int = Field(strict=True, ge=1)
    values: list[FiniteFloat | None] = Field(min_length=24, max_length=24)


class HistoryImport(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    source_version: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_.-]+$")
    engine_identity: str = Field(
        pattern=r"^NASA_CMAPSS:FD001:(train|test):[1-9][0-9]*$", max_length=120
    )
    rows: list[HistoryRow] = Field(min_length=1, max_length=10000)
    previous_id: str | None = Field(default=None, max_length=64)

    @model_validator(mode="after")
    def consecutive(self) -> "HistoryImport":
        if [row.cycle for row in self.rows] != list(range(1, len(self.rows) + 1)):
            raise ValueError("Cycles must start at one and be consecutive and ordered")
        return self
