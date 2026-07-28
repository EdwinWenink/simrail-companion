"""Pydantic models for vehicle composition data."""

from typing import Literal

from pydantic import BaseModel

# Type alias for vehicle loads
VehicleLoad = Literal[
    "TIE",
    "T_BEAM",
    "PIPELINE",
    "CONTAINER",
    "TREE_TRUNK",
    "WOODEN_BEAM",
    "METAL_SHEET",
    "STEEL_CIRCLE",
    "CONCRETE_SLAB",
    "GAS_CONTAINER",
    "PETROL",
    "ETHANOL",
    "CRUDE_OIL",
    "HEATING_OIL",
    "COAL",
    "SAND",
    "BALLAST",
    "WOOD_LOGS",
    "UNKNOWN",
]

VehicleType = Literal["WAGON", "LOCOMOTIVE", "ELECTRIC_MULTIPLE_UNIT"]


class Railcar(BaseModel):
    """Summary information about a railcar (locomotive, emu, or wagon)."""

    id: str
    displayName: str
    name: str | None = None
    type: VehicleType
    typeIdentifier: str
    requiredDlcId: str | None = None
    designation: str
    producer: str
    productionYears: str
    weight: float  # in tons
    width: float  # in meters
    length: float  # in meters
    maxSpeed: int  # in km/h


class Vehicle(BaseModel):
    """A vehicle in a train composition."""

    indexInGroup: int
    loadWeight: int | None = None
    load: VehicleLoad | None = None
    railcar: Railcar


class VehicleSequence(BaseModel):
    """Vehicle composition for a journey."""

    journeyId: str
    status: str
    lastUpdated: str  # ISO-8601 with offset
    vehicles: list[Vehicle]

    @property
    def locomotives(self) -> list[Railcar]:
        """Get all locomotives in the composition (supports double-headed trains)."""
        return [
            vehicle.railcar for vehicle in self.vehicles if vehicle.railcar.type == "LOCOMOTIVE"
        ]

    @property
    def wagons(self) -> list[Railcar]:
        """Get all wagons in the composition."""
        return [vehicle.railcar for vehicle in self.vehicles if vehicle.railcar.type == "WAGON"]

    @property
    def emus(self) -> list[Railcar]:
        """Get all electric multiple units (EMUs) in the composition."""
        return [
            vehicle.railcar
            for vehicle in self.vehicles
            if vehicle.railcar.type == "ELECTRIC_MULTIPLE_UNIT"
        ]

    @property
    def is_double_headed(self) -> bool:
        """Check if this is a double-headed train (multiple locomotives)."""
        return len(self.locomotives) > 1

    @property
    def primary_locomotive(self) -> Railcar | None:
        """Get the first (primary) locomotive, or None if no locomotive exists."""
        locs = self.locomotives
        return locs[0] if locs else None

    @property
    def num_vehicles(self) -> int:
        """Total number of vehicles in the sequence."""
        return len(self.vehicles)

    @property
    def total_railcar_weight(self) -> float:
        """Total weight of all railcars (excluding load)."""
        return sum(v.railcar.weight for v in self.vehicles)

    @property
    def total_load_weight(self) -> float:
        """Total weight of all loads on wagons."""
        return sum(v.loadWeight or 0 for v in self.vehicles)

    @property
    def total_weight(self) -> float:
        """Total weight including railcars and loads."""
        return self.total_railcar_weight + self.total_load_weight

    @property
    def total_length(self) -> float:
        """Total length of all vehicles."""
        return sum(v.railcar.length for v in self.vehicles)

    def __str__(self) -> str:
        """Return a human-readable representation of the vehicle composition."""
        if not self.vehicles:
            return "Empty vehicle composition"

        # Build the output
        lines = []

        # Display locomotive(s)
        locomotives = self.locomotives
        if locomotives:
            if len(locomotives) == 1:
                lines.append("🚂 LOCOMOTIVE:")
                loc = locomotives[0]
                lines.append(f"   {loc.displayName} ({loc.typeIdentifier})")
                lines.append(f"   {loc.producer} • {loc.productionYears} • {loc.maxSpeed} km/h")
            else:
                lines.append(f"🚂🚂 LOCOMOTIVES (Double-Headed, {len(locomotives)} units):")
                for i, loc in enumerate(locomotives, 1):
                    lines.append(f"   {i}. {loc.displayName} ({loc.typeIdentifier})")
                    if i == 1:  # Only show detailed specs for first loc to avoid clutter
                        lines.append(
                            f"      {loc.producer} • {loc.productionYears} • {loc.maxSpeed} km/h"
                        )
        else:
            lines.append("⚠️  No locomotive found in composition")

        lines.append("")
        lines.append("📊 COMPOSITION STATS")
        lines.append(f"   Vehicles: {self.num_vehicles}")
        lines.append(
            f"   Total Weight: {self.total_railcar_weight:.1f}t (railcars) + {self.total_load_weight}t (load) = {self.total_weight:.1f}t"
        )
        lines.append(f"   Total Length: {self.total_length:.2f}m")

        return "\n".join(lines)
