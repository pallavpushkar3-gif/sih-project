"""Strict, labelled fixture ingestion for the declared demonstrator schema."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class FixtureRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_.-]+$")


class AircraftFixture(FixtureRecord):
    tail_number: str = Field(min_length=1, max_length=64)
    label: str = Field(min_length=1, max_length=120)


class ComponentFixture(FixtureRecord):
    aircraft_id: str = Field(min_length=1, max_length=64)
    serial_number: str = Field(min_length=1, max_length=80)
    kind: Literal["engine"] = "engine"


class PartFixture(FixtureRecord):
    name: str = Field(min_length=1, max_length=120)
    on_hand: int = Field(ge=0, le=1000000)
    lead_time_slots: int = Field(default=0, ge=0, le=10000)


class TaskFixture(FixtureRecord):
    component_id: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=160)
    duration_slots: int = Field(ge=1, le=14)
    earliest_slot: int = Field(default=0, ge=0, le=13)
    deadline_slot: int = Field(ge=1, le=14)
    required_skill: Literal["engine"] = "engine"
    required_part_id: str | None = Field(default=None, max_length=64)
    required_part_quantity: int = Field(default=0, ge=0, le=1000000)
    fixed_start: int | None = Field(default=None, ge=0, le=13)
    predecessors: list[str] = Field(default_factory=list, max_length=1000)
    grouping_key: str | None = Field(default=None, max_length=64)
    mandatory: bool = True


class WorkspaceFixture(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    source_version: str = Field(min_length=1, max_length=80)
    provenance: Literal["synthetic"]
    scheduling_unit: Literal["8_hour_slots"]
    aircraft: list[AircraftFixture] = Field(default_factory=list, max_length=1000)
    components: list[ComponentFixture] = Field(default_factory=list, max_length=1000)
    parts: list[PartFixture] = Field(default_factory=list, max_length=1000)
    tasks: list[TaskFixture] = Field(default_factory=list, max_length=1000)
