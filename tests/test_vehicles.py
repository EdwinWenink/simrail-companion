"""Tests for vehicle composition models."""
import pytest
from simrail_tools_api.vehicle_types import Railcar, Vehicle, VehicleSequence, VehicleLoad


class TestRailcar:
    """Tests for Railcar model."""

    def test_create_railcar_minimal(self):
        """Test creating a Railcar with minimal required fields."""
        railcar = Railcar(
            id="EU07-001",
            displayName="EU07-001",
            type="LOCOMOTIVE",
            typeIdentifier="EU07",
            designation="EU07",
            producer="Pafawag",
            productionYears="1965-1974",
            weight=84.0,
            width=3.0,
            length=15.95,
            maxSpeed=125
        )

        assert railcar.id == "EU07-001"
        assert railcar.displayName == "EU07-001"
        assert railcar.name is None
        assert railcar.requiredDlcId is None
        assert railcar.maxSpeed == 125

    def test_create_railcar_with_name_and_dlc(self):
        """Test creating a Railcar with baptismal name and DLC requirement."""
        railcar = Railcar(
            id="ET22-001",
            displayName="ET22-001 'Stefan'",
            name="Stefan",
            type="LOCOMOTIVE",
            typeIdentifier="ET22",
            requiredDlcId="dlc-et22",
            designation="ET22",
            producer="Pafawag",
            productionYears="1969-1983",
            weight=120.0,
            width=3.0,
            length=19.2,
            maxSpeed=125
        )

        assert railcar.name == "Stefan"
        assert railcar.requiredDlcId == "dlc-et22"

    def test_railcar_physical_properties(self):
        """Test railcar physical properties are floats."""
        railcar = Railcar(
            id="test-001",
            displayName="Test Wagon",
            type="WAGON",
            typeIdentifier="TEST",
            designation="TEST-1",
            producer="Test Factory",
            productionYears="2020",
            weight=45.5,
            width=2.95,
            length=18.75,
            maxSpeed=100
        )

        assert isinstance(railcar.weight, float)
        assert isinstance(railcar.width, float)
        assert isinstance(railcar.length, float)
        assert railcar.weight == 45.5


class TestVehicle:
    """Tests for Vehicle model."""

    def test_create_vehicle_without_load(self):
        """Test creating a Vehicle without load (locomotive)."""
        railcar_data = {
            'id': 'EU07-001',
            'displayName': 'EU07-001',
            'type': 'LOCOMOTIVE',
            'typeIdentifier': 'EU07',
            'designation': 'EU07',
            'producer': 'Pafawag',
            'productionYears': '1965-1974',
            'weight': 84.0,
            'width': 3.0,
            'length': 15.95,
            'maxSpeed': 125
        }

        vehicle = Vehicle(
            indexInGroup=0,
            railcar=Railcar(**railcar_data)
        )

        assert vehicle.indexInGroup == 0
        assert vehicle.load is None
        assert vehicle.loadWeight is None
        assert vehicle.railcar.displayName == 'EU07-001'

    def test_create_vehicle_with_load(self):
        """Test creating a Vehicle with cargo load."""
        railcar_data = {
            'id': 'wagon-001',
            'displayName': 'Coal Wagon',
            'type': 'WAGON',
            'typeIdentifier': 'COAL_WAGON',
            'designation': 'Eaos',
            'producer': 'PKP Cargo',
            'productionYears': '2000',
            'weight': 22.0,
            'width': 2.9,
            'length': 14.5,
            'maxSpeed': 100
        }

        vehicle = Vehicle(
            indexInGroup=1,
            load='COAL',
            loadWeight=50,
            railcar=Railcar(**railcar_data)
        )

        assert vehicle.indexInGroup == 1
        assert vehicle.load == 'COAL'
        assert vehicle.loadWeight == 50

    def test_vehicle_load_types(self):
        """Test various vehicle load types."""
        railcar_data = {
            'id': 'wagon-002',
            'displayName': 'Cargo Wagon',
            'type': 'WAGON',
            'typeIdentifier': 'CARGO',
            'designation': 'Cargo',
            'producer': 'Test',
            'productionYears': '2000',
            'weight': 20.0,
            'width': 2.8,
            'length': 13.0,
            'maxSpeed': 100
        }

        load_types = ['COAL', 'PETROL', 'CONTAINER', 'WOOD_LOGS', 'UNKNOWN']
        for load_type in load_types:
            vehicle = Vehicle(
                indexInGroup=0,
                load=load_type,  # type: ignore
                loadWeight=30,
                railcar=Railcar(**railcar_data)
            )
            assert vehicle.load == load_type


class TestVehicleSequence:
    """Tests for VehicleSequence model."""

    def test_create_vehicle_sequence_empty(self):
        """Test creating an empty VehicleSequence."""
        sequence = VehicleSequence(
            journeyId='journey-123',
            status='ACTIVE',
            lastUpdated='2024-01-01T12:00:00+01:00',
            vehicles=[]
        )

        assert sequence.journeyId == 'journey-123'
        assert sequence.status == 'ACTIVE'
        assert len(sequence.vehicles) == 0

    def test_create_vehicle_sequence_with_train(self):
        """Test creating a VehicleSequence with a complete train."""
        loco_data = {
            'id': 'EU07-001',
            'displayName': 'EU07-001',
            'type': 'LOCOMOTIVE',
            'typeIdentifier': 'EU07',
            'designation': 'EU07',
            'producer': 'Pafawag',
            'productionYears': '1965-1974',
            'weight': 84.0,
            'width': 3.0,
            'length': 15.95,
            'maxSpeed': 125
        }

        wagon_data = {
            'id': 'wagon-001',
            'displayName': 'Passenger Coach',
            'type': 'WAGON',
            'typeIdentifier': 'PASSENGER',
            'designation': 'B',
            'producer': 'PESA',
            'productionYears': '2010',
            'weight': 40.0,
            'width': 3.0,
            'length': 24.5,
            'maxSpeed': 160
        }

        sequence = VehicleSequence(
            journeyId='journey-456',
            status='ACTIVE',
            lastUpdated='2024-01-01T14:30:00+01:00',
            vehicles=[
                Vehicle(indexInGroup=0, railcar=Railcar(**loco_data)),
                Vehicle(indexInGroup=1, railcar=Railcar(**wagon_data)),
                Vehicle(indexInGroup=2, railcar=Railcar(**wagon_data)),
                Vehicle(indexInGroup=3, railcar=Railcar(**wagon_data)),
            ]
        )

        assert sequence.journeyId == 'journey-456'
        assert len(sequence.vehicles) == 4
        assert sequence.vehicles[0].railcar.type == 'LOCOMOTIVE'
        assert all(v.railcar.type == 'WAGON' for v in sequence.vehicles[1:])

    def test_vehicle_sequence_indexing(self):
        """Test that vehicles maintain proper indexing."""
        railcar_data = {
            'id': 'test',
            'displayName': 'Test',
            'type': 'WAGON',
            'typeIdentifier': 'TEST',
            'designation': 'T',
            'producer': 'Test',
            'productionYears': '2000',
            'weight': 20.0,
            'width': 2.8,
            'length': 10.0,
            'maxSpeed': 100
        }

        vehicles = [
            Vehicle(indexInGroup=i, railcar=Railcar(**railcar_data))
            for i in range(5)
        ]

        sequence = VehicleSequence(
            journeyId='test-journey',
            status='ACTIVE',
            lastUpdated='2024-01-01T12:00:00Z',
            vehicles=vehicles
        )

        for i, vehicle in enumerate(sequence.vehicles):
            assert vehicle.indexInGroup == i


class TestVehicleLoadEnum:
    """Tests for VehicleLoad enum."""

    def test_all_load_types_valid(self):
        """Test that all defined load types can be used."""
        load_types = [
            'TIE', 'T_BEAM', 'PIPELINE', 'CONTAINER', 'TREE_TRUNK',
            'WOODEN_BEAM', 'METAL_SHEET', 'STEEL_CIRCLE', 'CONCRETE_SLAB',
            'GAS_CONTAINER', 'PETROL', 'ETHANOL', 'CRUDE_OIL', 'HEATING_OIL',
            'COAL', 'SAND', 'BALLAST', 'WOOD_LOGS', 'UNKNOWN'
        ]

        railcar_data = {
            'id': 'wagon',
            'displayName': 'Cargo Wagon',
            'type': 'WAGON',
            'typeIdentifier': 'CARGO',
            'designation': 'Cargo',
            'producer': 'Test',
            'productionYears': '2000',
            'weight': 20.0,
            'width': 2.8,
            'length': 13.0,
            'maxSpeed': 100
        }

        for load_type in load_types:
            vehicle = Vehicle(
                indexInGroup=0,
                load=load_type,  # type: ignore
                loadWeight=30,
                railcar=Railcar(**railcar_data)
            )
            assert vehicle.load == load_type


class TestVehicleSequencePrintable:
    """Tests for VehicleSequence printable representation."""

    def test_str_representation_with_locomotive(self):
        """Test string representation with a locomotive and wagons."""
        loco_data = {
            'id': 'EU07-001',
            'displayName': 'EU07-001',
            'type': 'LOCOMOTIVE',
            'typeIdentifier': 'EU07',
            'designation': 'EU07',
            'producer': 'Pafawag',
            'productionYears': '1965-1974',
            'weight': 84.0,
            'width': 3.0,
            'length': 15.95,
            'maxSpeed': 125
        }

        wagon_data = {
            'id': 'wagon-001',
            'displayName': 'Coal Wagon',
            'type': 'WAGON',
            'typeIdentifier': 'EAOS',
            'designation': 'Eaos',
            'producer': 'PKP',
            'productionYears': '2000',
            'weight': 22.0,
            'width': 2.9,
            'length': 14.5,
            'maxSpeed': 100
        }

        sequence = VehicleSequence(
            journeyId='journey-123',
            status='ACTIVE',
            lastUpdated='2024-01-01T12:00:00+01:00',
            vehicles=[
                Vehicle(indexInGroup=0, railcar=Railcar(**loco_data)),
                Vehicle(indexInGroup=1, load='COAL', loadWeight=50, railcar=Railcar(**wagon_data)),
                Vehicle(indexInGroup=2, load='COAL', loadWeight=50, railcar=Railcar(**wagon_data)),
            ]
        )

        result = str(sequence)

        # Check locomotive info is present
        assert 'EU07-001' in result
        assert 'EU07' in result
        assert 'Pafawag' in result
        assert '1965-1974' in result
        assert '125 km/h' in result

        # Check stats are present
        assert 'Vehicles: 3' in result
        assert '128.0t (railcars)' in result  # 84 + 22 + 22
        assert '100t (load)' in result  # 50 + 50
        assert '228.0t' in result  # total
        assert '44.95m' in result  # 15.95 + 14.5 + 14.5

    def test_str_representation_without_locomotive(self):
        """Test string representation without a locomotive."""
        wagon_data = {
            'id': 'wagon-001',
            'displayName': 'Wagon',
            'type': 'WAGON',
            'typeIdentifier': 'WAGON',
            'designation': 'W',
            'producer': 'Test',
            'productionYears': '2000',
            'weight': 20.0,
            'width': 2.8,
            'length': 10.0,
            'maxSpeed': 100
        }

        sequence = VehicleSequence(
            journeyId='journey-456',
            status='ACTIVE',
            lastUpdated='2024-01-01T12:00:00+01:00',
            vehicles=[
                Vehicle(indexInGroup=0, railcar=Railcar(**wagon_data)),
            ]
        )

        result = str(sequence)

        assert 'No locomotive found' in result
        assert 'Vehicles: 1' in result

    def test_str_representation_empty_sequence(self):
        """Test string representation of empty sequence."""
        sequence = VehicleSequence(
            journeyId='journey-789',
            status='INACTIVE',
            lastUpdated='2024-01-01T12:00:00+01:00',
            vehicles=[]
        )

        result = str(sequence)

        assert result == "Empty vehicle composition"

    def test_str_representation_no_load(self):
        """Test string representation with vehicles but no cargo load."""
        loco_data = {
            'id': 'EU07-001',
            'displayName': 'EU07-001',
            'type': 'LOCOMOTIVE',
            'typeIdentifier': 'EU07',
            'designation': 'EU07',
            'producer': 'Pafawag',
            'productionYears': '1965-1974',
            'weight': 84.0,
            'width': 3.0,
            'length': 15.95,
            'maxSpeed': 125
        }

        passenger_data = {
            'id': 'coach-001',
            'displayName': 'Passenger Coach',
            'type': 'WAGON',
            'typeIdentifier': 'B',
            'designation': 'B',
            'producer': 'PESA',
            'productionYears': '2010',
            'weight': 40.0,
            'width': 3.0,
            'length': 24.5,
            'maxSpeed': 160
        }

        sequence = VehicleSequence(
            journeyId='journey-pass',
            status='ACTIVE',
            lastUpdated='2024-01-01T12:00:00+01:00',
            vehicles=[
                Vehicle(indexInGroup=0, railcar=Railcar(**loco_data)),
                Vehicle(indexInGroup=1, railcar=Railcar(**passenger_data)),
            ]
        )

        result = str(sequence)

        # Check that load is 0 when no cargo
        assert '124.0t (railcars)' in result  # 84 + 40
        assert '0t (load)' in result
        assert '124.0t' in result  # total equals railcar weight
