#!/usr/bin/env python3
"""
List all available servers from SimRail Tools API.
"""

import asyncio
import sys
from simrail_tools_api import SimRailToolsClient


async def main():
    client = SimRailToolsClient()

    print("Fetching servers from SimRail Tools API...\n")

    try:
        servers = await client._fetch("sit-servers/v2/")

        print(f"Found {len(servers)} servers:\n")
        print("=" * 100)
        print(f"{'Code':<10} {'Name':<40} {'ID':<40}")
        print("=" * 100)

        for server in servers:
            code = server.get("code", "N/A")
            name = server.get("name", "N/A")
            server_id = server.get("id", "N/A")

            print(f"{code:<10} {name:<40} {server_id:<40}")

    except Exception as e:
        print(f"Error: {e}")

    await client.close()


if __name__ == "__main__":
    # Configure UTF-8 output for Windows
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    asyncio.run(main())
