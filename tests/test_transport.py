"""Tests for JourneyTransport model fields."""
from simrail_tools_api.types import JourneyTransport, TransportType


class TestJourneyTransport:
    """Tests for JourneyTransport model."""

    def test_create_transport_minimal(self):
        """Test creating JourneyTransport with minimal fields."""
        transport = JourneyTransport(
            category='IC',
            number='1234',
            type='INTER_REGIONAL_TRAIN',
            maxSpeed=160
        )

        assert transport.category == 'IC'
        assert transport.number == '1234'
        assert transport.type == 'INTER_REGIONAL_TRAIN'
        assert transport.maxSpeed == 160
        assert transport.categoryExternal is None
        assert transport.line is None
        assert transport.label is None

    def test_create_transport_with_all_fields(self):
        """Test creating JourneyTransport with all optional fields."""
        transport = JourneyTransport(
            category='RPJ',
            categoryExternal='IR',
            number='5678',
            line='S1',
            label='InterRegio Premium',
            type='INTER_REGIONAL_TRAIN',
            maxSpeed=140
        )

        assert transport.category == 'RPJ'
        assert transport.categoryExternal == 'IR'
        assert transport.number == '5678'
        assert transport.line == 'S1'
        assert transport.label == 'InterRegio Premium'
        assert transport.type == 'INTER_REGIONAL_TRAIN'
        assert transport.maxSpeed == 140

    def test_transport_types(self):
        """Test all valid transport types."""
        valid_types = [
            'NATIONAL_EXPRESS_TRAIN',
            'INTER_NATIONAL_EXPRESS_TRAIN',
            'INTER_REGIONAL_EXPRESS_TRAIN',
            'INTER_REGIONAL_TRAIN',
            'REGIONAL_FAST_TRAIN',
            'REGIONAL_TRAIN',
            'ADDITIONAL_TRAIN',
            'MANEUVER_TRAIN',
            'EMPTY_TRANSFER_TRAIN',
            'INTER_NATIONAL_CARGO_TRAIN',
            'NATIONAL_CARGO_TRAIN',
            'MAINTENANCE_TRAIN',
        ]

        for transport_type in valid_types:
            transport = JourneyTransport(
                category='TEST',
                number='1234',
                type=transport_type,  # type: ignore
                maxSpeed=100
            )
            assert transport.type == transport_type

    def test_express_train(self):
        """Test creating an express train transport."""
        transport = JourneyTransport(
            category='EIP',
            categoryExternal='EC',
            number='1102',
            label='EuroCity Premium',
            type='INTER_NATIONAL_EXPRESS_TRAIN',
            maxSpeed=200
        )

        assert transport.type == 'INTER_NATIONAL_EXPRESS_TRAIN'
        assert transport.maxSpeed == 200
        assert transport.categoryExternal == 'EC'

    def test_cargo_train(self):
        """Test creating a cargo train transport."""
        transport = JourneyTransport(
            category='TŁ',
            number='98765',
            type='NATIONAL_CARGO_TRAIN',
            maxSpeed=80
        )

        assert transport.type == 'NATIONAL_CARGO_TRAIN'
        assert transport.maxSpeed == 80

    def test_maintenance_train(self):
        """Test creating a maintenance train transport."""
        transport = JourneyTransport(
            category='KON',
            number='999',
            type='MAINTENANCE_TRAIN',
            maxSpeed=40
        )

        assert transport.type == 'MAINTENANCE_TRAIN'
        assert transport.maxSpeed == 40
