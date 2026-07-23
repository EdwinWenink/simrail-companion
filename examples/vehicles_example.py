#!/usr/bin/env python3
"""Example script demonstrating vehicle composition retrieval."""
import asyncio
import sys
from simrail_tools_api import SimRailToolsClient

# Configure UTF-8 output for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


async def main():
    if len(sys.argv) < 3:
        print("Usage: python example_vehicles.py <server_code> <train_number>")
        print("Example: python example_vehicles.py int1 4144")
        return

    server_code = sys.argv[1]
    train_number = sys.argv[2]

    client = SimRailToolsClient()

    try:
        # Step 1: Find the journey by train number
        print(f"🔍 Looking up train {train_number} on {server_code}...")
        journey_id = await client.find_journey_by_train_number(server_code, train_number)

        if not journey_id:
            print(f"❌ Train {train_number} not found on {server_code}")
            return

        print(f"✓ Found journey: {journey_id[:8]}...\n")

        # Step 2: Get vehicle composition
        print("🚂 Fetching vehicle composition...")
        vehicles = await client.get_vehicle_composition(journey_id)

        if not vehicles:
            print("❌ No vehicle composition available for this journey")
            return

        print(f"✓ Loaded vehicle data (updated: {vehicles.lastUpdated})")
        print(f"   Status: {vehicles.status}\n")

        # Step 3: Display summary using printable representation
        print("=" * 80)
        print(vehicles)  # Uses __str__ method
        print("=" * 80)
        print()

        # Step 4: Display detailed vehicle composition
        print("📋 DETAILED COMPOSITION")
        print("=" * 100)
        print(f"{'#':<4} {'Railcar':<35} {'Type':<20} {'Load':<20} {'Weight':<10}")
        print("=" * 100)

        for vehicle in vehicles.vehicles:
            railcar = vehicle.railcar
            index = vehicle.indexInGroup + 1  # Display as 1-based
            load_info = vehicle.load or "-"
            weight_info = f"{vehicle.loadWeight}t" if vehicle.loadWeight else "-"

            print(f"{index:<4} {railcar.displayName:<35} {railcar.type:<20} {load_info:<20} {weight_info:<10}")

        print("=" * 100)

        # Step 5: Show detailed railcar info for the first vehicle (locomotive)
        if vehicles.vehicles:
            print("\n📋 Locomotive Details:")
            loco = vehicles.vehicles[0].railcar
            print(f"  Name: {loco.displayName}")
            if loco.name:
                print(f"  Baptismal Name: {loco.name}")
            print(f"  Designation: {loco.designation}")
            print(f"  Producer: {loco.producer}")
            print(f"  Production Years: {loco.productionYears}")
            print(f"  Specifications:")
            print(f"    Weight: {loco.weight}t")
            print(f"    Length: {loco.length}m")
            print(f"    Width: {loco.width}m")
            print(f"    Max Speed: {loco.maxSpeed} km/h")
            if loco.requiredDlcId:
                print(f"  DLC Required: {loco.requiredDlcId}")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
