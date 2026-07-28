"""Pydantic models for vehicle composition data."""

from typing import Literal

from pydantic import BaseModel


class TransportInfo(BaseModel):
    """Transport information from journey API."""

    category: str
    category_external: str | None = None
    number: str
    line: str | None = None
    label: str | None = None
    type: str
    max_speed: int


class LocomotiveInfo(BaseModel):
    """Locomotive summary information."""

    displayName: str
    typeIdentifier: str


class EMUInfo(BaseModel):
    """EMU (Electric Multiple Unit) summary information."""

    displayName: str
    typeIdentifier: str


class VehicleInfo(BaseModel):
    """Detailed vehicle information."""

    indexInGroup: int
    id: str
    displayName: str
    name: str | None = None
    type: Literal["LOCOMOTIVE", "ELECTRIC_MULTIPLE_UNIT", "WAGON", "RAILCAR"]
    typeIdentifier: str
    designation: str | None = None
    producer: str | None = None
    productionYears: str | None = None
    weight: float
    length: float
    maxSpeed: int
    loadWeight: float | None = None
    load: str | None = None


class VehicleComposition(BaseModel):
    """Complete vehicle composition for a train.

    This model represents the full composition stored in composition_json,
    including locomotives, EMUs, wagons, and summary statistics.
    """

    traction_type: Literal["LOCOMOTIVE", "ELECTRIC_MULTIPLE_UNIT", "UNKNOWN"]
    transport: TransportInfo | None = None
    locomotives: list[LocomotiveInfo] = []
    emus: list[EMUInfo] = []
    vehicles: list[VehicleInfo] = []
    num_wagons: int = 0
    total_vehicles: int
    total_length: float
    total_weight: float

    def get_transport_summary(self) -> str:
        """Format transport information as text summary.

        Returns:
            Formatted transport info string with line breaks, or empty string if no transport data
        """
        if not self.transport:
            return ""

        info_parts = []
        if self.transport.type:
            info_parts.append(f"Type: {self.transport.type}")
        if self.transport.category_external:
            info_parts.append(f"Category (external): {self.transport.category_external}")
        if self.transport.line:
            info_parts.append(f"Line: {self.transport.line}")
        if self.transport.label:
            info_parts.append(f"Label: {self.transport.label}")
        if self.transport.max_speed:
            info_parts.append(f"Max Speed: {self.transport.max_speed} km/h")

        return "\n" + "\n".join(info_parts) if info_parts else ""
