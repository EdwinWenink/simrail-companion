"""Tests for double-headed locomotive support in VehicleSequence."""
import pytest
from simrail_tools_api.vehicle_types import VehicleSequence, Vehicle, Railcar


class TestDoubleHeadedLocomotives:
    """Test support for trains with multiple locomotives."""

    def test_single_locomotive(self):
        """Test that single locomotive trains work as before."""
        sequence = VehicleSequence(
            journeyId="test-123",
            status="active",
            lastUpdated="2024-01-01T12:00:00Z",
            vehicles=[
                Vehicle(
                    indexInGroup=0,
                    railcar=Railcar(
                        id="eu07-1",
                        displayName="EU07",
                        type="LOCOMOTIVE",
                        typeIdentifier="EU07",
                        designation="EU07-001",
                        producer="Pafawag",
                        productionYears="1965-1974",
                        weight=83.0,
                        width=3.0,
                        length=16.7,
                        maxSpeed=125,
                    )
                )
            ]
        )

        assert len(sequence.locomotives) == 1
        assert sequence.is_double_headed is False
        assert sequence.primary_locomotive is not None
        assert sequence.primary_locomotive.typeIdentifier == "EU07"

    def test_double_headed_locomotives(self):
        """Test double-headed configuration with two locomotives."""
        sequence = VehicleSequence(
            journeyId="test-456",
            status="active",
            lastUpdated="2024-01-01T12:00:00Z",
            vehicles=[
                Vehicle(
                    indexInGroup=0,
                    railcar=Railcar(
                        id="eu07-1",
                        displayName="EU07",
                        type="LOCOMOTIVE",
                        typeIdentifier="EU07",
                        designation="EU07-001",
                        producer="Pafawag",
                        productionYears="1965-1974",
                        weight=83.0,
                        width=3.0,
                        length=16.7,
                        maxSpeed=125,
                    )
                ),
                Vehicle(
                    indexInGroup=1,
                    railcar=Railcar(
                        id="eu07-2",
                        displayName="EU07",
                        type="LOCOMOTIVE",
                        typeIdentifier="EU07",
                        designation="EU07-002",
                        producer="Pafawag",
                        productionYears="1965-1974",
                        weight=83.0,
                        width=3.0,
                        length=16.7,
                        maxSpeed=125,
                    )
                ),
                Vehicle(
                    indexInGroup=2,
                    loadWeight=60,
                    load="COAL",
                    railcar=Railcar(
                        id="wagon-1",
                        displayName="Eanos",
                        type="WAGON",
                        typeIdentifier="Eanos",
                        designation="Eanos-001",
                        producer="Wagon Factory",
                        productionYears="1990-2000",
                        weight=20.0,
                        width=2.8,
                        length=12.0,
                        maxSpeed=100,
                    )
                )
            ]
        )

        assert len(sequence.locomotives) == 2
        assert sequence.is_double_headed is True
        assert sequence.primary_locomotive is not None
        assert sequence.primary_locomotive.designation == "EU07-001"

    def test_triple_headed_locomotives(self):
        """Test configuration with three locomotives (rare but possible)."""
        sequence = VehicleSequence(
            journeyId="test-789",
            status="active",
            lastUpdated="2024-01-01T12:00:00Z",
            vehicles=[
                Vehicle(
                    indexInGroup=i,
                    railcar=Railcar(
                        id=f"eu07-{i+1}",
                        displayName="EU07",
                        type="LOCOMOTIVE",
                        typeIdentifier="EU07",
                        designation=f"EU07-00{i+1}",
                        producer="Pafawag",
                        productionYears="1965-1974",
                        weight=83.0,
                        width=3.0,
                        length=16.7,
                        maxSpeed=125,
                    )
                )
                for i in range(3)
            ]
        )

        assert len(sequence.locomotives) == 3
        assert sequence.is_double_headed is True  # More than one
        assert sequence.primary_locomotive.designation == "EU07-001"

    def test_no_locomotive(self):
        """Test composition with no locomotives (wagons only)."""
        sequence = VehicleSequence(
            journeyId="test-000",
            status="active",
            lastUpdated="2024-01-01T12:00:00Z",
            vehicles=[
                Vehicle(
                    indexInGroup=0,
                    loadWeight=60,
                    load="COAL",
                    railcar=Railcar(
                        id="wagon-1",
                        displayName="Eanos",
                        type="WAGON",
                        typeIdentifier="Eanos",
                        designation="Eanos-001",
                        producer="Wagon Factory",
                        productionYears="1990-2000",
                        weight=20.0,
                        width=2.8,
                        length=12.0,
                        maxSpeed=100,
                    )
                )
            ]
        )

        assert len(sequence.locomotives) == 0
        assert sequence.is_double_headed is False
        assert sequence.primary_locomotive is None

    def test_string_representation_single_loc(self):
        """Test string output for single locomotive."""
        sequence = VehicleSequence(
            journeyId="test-str-1",
            status="active",
            lastUpdated="2024-01-01T12:00:00Z",
            vehicles=[
                Vehicle(
                    indexInGroup=0,
                    railcar=Railcar(
                        id="eu07-1",
                        displayName="EU07 Electric",
                        type="LOCOMOTIVE",
                        typeIdentifier="EU07",
                        designation="EU07-001",
                        producer="Pafawag",
                        productionYears="1965-1974",
                        weight=83.0,
                        width=3.0,
                        length=16.7,
                        maxSpeed=125,
                    )
                )
            ]
        )

        output = str(sequence)
        assert "🚂 LOCOMOTIVE:" in output
        assert "EU07 Electric" in output
        assert "Double-Headed" not in output

    def test_string_representation_double_headed(self):
        """Test string output for double-headed configuration."""
        sequence = VehicleSequence(
            journeyId="test-str-2",
            status="active",
            lastUpdated="2024-01-01T12:00:00Z",
            vehicles=[
                Vehicle(
                    indexInGroup=0,
                    railcar=Railcar(
                        id="eu07-1",
                        displayName="EU07-A",
                        type="LOCOMOTIVE",
                        typeIdentifier="EU07",
                        designation="EU07-001",
                        producer="Pafawag",
                        productionYears="1965-1974",
                        weight=83.0,
                        width=3.0,
                        length=16.7,
                        maxSpeed=125,
                    )
                ),
                Vehicle(
                    indexInGroup=1,
                    railcar=Railcar(
                        id="eu07-2",
                        displayName="EU07-B",
                        type="LOCOMOTIVE",
                        typeIdentifier="EU07",
                        designation="EU07-002",
                        producer="Pafawag",
                        productionYears="1965-1974",
                        weight=83.0,
                        width=3.0,
                        length=16.7,
                        maxSpeed=125,
                    )
                )
            ]
        )

        output = str(sequence)
        assert "🚂🚂 LOCOMOTIVES (Double-Headed, 2 units):" in output
        assert "1. EU07-A" in output
        assert "2. EU07-B" in output
        assert "Pafawag" in output  # Specs shown for first loc
