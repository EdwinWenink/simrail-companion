"""Pydantic models for vehicle composition data."""
from typing import Optional, Literal
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
    """Summary information about a railcar (locomotive or wagon)."""
    id: str
    displayName: str
    name: Optional[str] = None
    type: VehicleType
    typeIdentifier: str
    requiredDlcId: Optional[str] = None
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
    loadWeight: Optional[int] = None
    load: Optional[VehicleLoad] = None
    railcar: Railcar


class VehicleSequence(BaseModel):
    """Vehicle composition for a journey."""
    journeyId: str
    status: str
    lastUpdated: str  # ISO-8601 with offset
    vehicles: list[Vehicle]

    def __str__(self) -> str:
        """Return a human-readable representation of the vehicle composition."""
        if not self.vehicles:
            return "Empty vehicle composition"

        # Find the first locomotive
        locomotive = None
        for vehicle in self.vehicles:
            if vehicle.railcar.type == "LOCOMOTIVE":
                locomotive = vehicle.railcar
                break

        # Calculate statistics
        num_vehicles = len(self.vehicles)
        total_railcar_weight = sum(v.railcar.weight for v in self.vehicles)
        total_load_weight = sum(v.loadWeight or 0 for v in self.vehicles)
        total_length = sum(v.railcar.length for v in self.vehicles)

        # Build the output
        lines = []

        # TODO what about double heading EU07-EU07, 2 locs!
        if locomotive:
            lines.append("🚂 LOC:")
            lines.append(f"   {locomotive.displayName} ({locomotive.typeIdentifier})")
            lines.append(f"   {locomotive.producer} • {locomotive.productionYears} • {locomotive.maxSpeed} km/h")
        else:
            lines.append("⚠️  No locomotive found in composition")

        lines.append("")
        lines.append("📊 COMPOSITION STATS")
        lines.append(f"   Vehicles: {num_vehicles}")
        lines.append(f"   Total Weight: {total_railcar_weight:.1f}t (railcars) + {total_load_weight}t (load) = {total_railcar_weight + total_load_weight:.1f}t")
        lines.append(f"   Total Length: {total_length:.2f}m")

        return "\n".join(lines)
