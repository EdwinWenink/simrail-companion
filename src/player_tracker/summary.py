from datetime import datetime, timedelta, timezone

from .database import TrackerDatabase


def format_vehicle_info(session: dict) -> str:
    """Format vehicle information with optional weight and length."""
    vehicle_info = session.get("vehicle_summary", "Unknown")
    if session.get("total_weight"):
        vehicle_info += f" ({session['total_weight']:.0f}t)"
    if session.get("total_length"):
        vehicle_info += f" • {session['total_length']:.1f}m"
    return vehicle_info


def format_duration(seconds: float) -> str:
    """Format seconds into human-readable duration."""
    if seconds < 60:
        return f"{int(seconds)}s"
    if seconds < 3600:
        return f"{int(seconds / 60)}m {int(seconds % 60)}s"

    hours = int(seconds / 3600)
    minutes = int((seconds % 3600) / 60)
    return f"{hours}h {minutes}m"


def format_datetime(dt_str: str) -> str:
    """Format ISO datetime string to readable format."""
    dt = datetime.fromisoformat(dt_str)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def print_summary(db: TrackerDatabase, steam_id: str, session_limit: int = 10):
    """Print a comprehensive summary of tracked player data."""

    print("\n" + "=" * 80)
    print(f"PLAYER TRACKING SUMMARY - Steam ID: {steam_id}")
    print("=" * 80)

    # Get Steam stats
    latest_steam = db.get_latest_steam_stats(steam_id)
    steam_history = db.get_steam_stats_history(steam_id, limit=2)
    previous_steam = steam_history[1] if len(steam_history) > 1 else None

    # Get overall stats
    stats = db.get_stats(steam_id)

    # ===== STEAM STATISTICS =====
    if latest_steam:
        print("\n🎮 STEAM STATISTICS (Latest)")
        print("-" * 80)
        print(
            f"Total Distance:          {latest_steam['total_distance_meters']:,} m ({latest_steam['total_distance_meters'] / 1000:.2f} km)"
        )
        print(f"Total Score:             {latest_steam['total_score']:,}")
        print(
            f"Dispatcher Time:         {latest_steam['total_dispatcher_time_minutes']:,} min ({latest_steam['total_dispatcher_time_minutes'] / 60:.2f} hours)"
        )
        print(
            f"Last Synced:             {format_datetime(latest_steam['recorded_at'])}"
        )

        if previous_steam and previous_steam["id"] != latest_steam["id"]:
            distance_gain = (
                latest_steam["total_distance_meters"]
                - previous_steam["total_distance_meters"]
            )
            score_gain = latest_steam["total_score"] - previous_steam["total_score"]
            time_gain = (
                latest_steam["total_dispatcher_time_minutes"]
                - previous_steam["total_dispatcher_time_minutes"]
            )

            print(
                f"\nGain since previous sync ({format_datetime(previous_steam['recorded_at'])}):"
            )
            print(f"  Distance: +{distance_gain:,} m ({distance_gain / 1000:.2f} km)")
            print(f"  Score: +{score_gain:,}")
            print(f"  Dispatcher Time: +{time_gain} min ({time_gain / 60:.2f} hours)")

    # ===== OVERALL STATISTICS =====
    print("\n📊 TRACKED SESSION STATISTICS")
    print("-" * 80)
    print(
        f"Total Distance Traveled: {stats['total_distance_meters']:,} m ({stats['total_distance_meters'] / 1000:.2f} km)"
    )
    print(f"Total Points Earned:     {stats['total_points']:,}")
    print(
        f"Total Train Time:        {format_duration(stats['total_train_time_seconds'])} ({stats['total_train_time_seconds'] / 3600:.2f} hours)"
    )
    print(
        f"Total Dispatcher Time:   {format_duration(stats['total_dispatcher_time_seconds'])} ({stats['total_dispatcher_time_seconds'] / 3600:.2f} hours)"
    )
    print(f"Train Sessions:          {stats['train_sessions']}")
    print(f"Station Sessions:        {stats['station_sessions']}")

    # Compare with Steam stats if available
    if latest_steam:
        coverage = (
            (
                stats["total_distance_meters"]
                / latest_steam["total_distance_meters"]
                * 100
            )
            if latest_steam["total_distance_meters"] > 0
            else 0
        )
        print(f"\nTracking Coverage:       {coverage:.1f}% of Steam distance tracked")

    # ===== TRAINS BY TYPE =====
    if stats["trains_by_type"]:
        print("\n🚂 STATISTICS BY TRAIN TYPE")
        print("-" * 80)
        print(f"{'Train/Vehicle':<40} {'Distance':<15} {'Points':<12} {'Time':<12}")
        print("-" * 80)

        # Sort by distance
        sorted_trains = sorted(
            stats["trains_by_type"].items(),
            key=lambda x: x[1]["distance"],
            reverse=True,
        )

        for vehicle, data in sorted_trains:
            distance_km = data["distance"] / 1000
            time_str = format_duration(data["time"])
            # Truncate long vehicle names
            vehicle_display = vehicle[:38] + ".." if len(vehicle) > 40 else vehicle
            print(
                f"{vehicle_display:<40} {distance_km:>10,.2f} km {data['points']:>10,} {time_str:>12}"
            )

    # ===== STATIONS BY TIME =====
    if stats["stations_by_name"]:
        print("\n📍 DISPATCHER TIME BY STATION (Top 15)")
        print("-" * 80)
        print(f"{'Station Name':<40} {'Time':<15} {'Sessions':<10}")
        print("-" * 80)

        # Get station sessions for counting
        all_station_sessions = db.get_station_sessions(steam_id, limit=10000)
        station_session_counts = {}
        for session in all_station_sessions:
            if session["left_at"]:
                station = session["station_name"]
                station_session_counts[station] = (
                    station_session_counts.get(station, 0) + 1
                )

        # Sort by time
        sorted_stations = sorted(
            stats["stations_by_name"].items(), key=lambda x: x[1], reverse=True
        )

        for station, time_seconds in sorted_stations[:15]:
            time_str = format_duration(time_seconds)
            session_count = station_session_counts.get(station, 0)
            # Truncate long station names
            station_display = station[:38] + ".." if len(station) > 40 else station
            print(f"{station_display:<40} {time_str:<15} {session_count:<10}")

    # ===== STATIONS PASSED DURING TRAIN SESSIONS =====
    if stats.get("station_passages"):
        print("\n🚉 STATIONS PASSED WHILE DRIVING TRAINS (Top 20)")
        print("-" * 80)
        print(f"{'Station Name':<40} {'Total':<8} {'Pax':<8} {'Tech':<8} {'Pass':<8}")
        print("-" * 80)

        # Sort by total passages
        sorted_passages = sorted(
            stats["station_passages"].items(), key=lambda x: x[1]["total"], reverse=True
        )

        for station, data in sorted_passages[:20]:
            station_display = station[:38] + ".." if len(station) > 40 else station
            print(
                f"{station_display:<40} {data['total']:<8} {data['passenger_stops']:<8} "
                f"{data['technical_stops']:<8} {data['pass_through']:<8}"
            )

    # ===== RECENT TRAIN SESSIONS =====
    print(f"\n🚂 RECENT TRAIN SESSIONS (Last {session_limit})")
    print("-" * 80)

    recent_trains = db.get_train_sessions(steam_id, limit=session_limit)

    if not recent_trains:
        print("No train sessions recorded yet.")
    else:
        for session in recent_trains:
            status = "✅" if session["left_at"] else "🔄"

            # Calculate duration
            if session["left_at"]:
                start = datetime.fromisoformat(session["joined_at"])
                end = datetime.fromisoformat(session["left_at"])
                duration = format_duration((end - start).total_seconds())
            else:
                duration = "In Progress"

            # Format vehicle information with composition data
            vehicle_info = format_vehicle_info(session)

            print(
                f"\n{status} Train {session['train_number']} ({session['train_name']}) - {vehicle_info[:60]}"
            )
            print(f"   Route: {session['start_station']} → {session['end_station']}")
            print(f"   Server: {session['server_name']} ({session['server_code']})")
            print(f"   Started: {format_datetime(session['joined_at'])}")

            if session["left_at"]:
                print(f"   Ended: {format_datetime(session['left_at'])}")
                print(f"   Duration: {duration}")
                if session["distance_meters"]:
                    print(
                        f"   Distance: {session['distance_meters']:,} m ({session['distance_meters'] / 1000:.2f} km)"
                    )
                    print(f"   Points: {session['points']:,}")

    # ===== RECENT STATION SESSIONS =====
    print(f"\n📍 RECENT STATION SESSIONS (Last {session_limit})")
    print("-" * 80)

    recent_stations = db.get_station_sessions(steam_id, limit=session_limit)

    if not recent_stations:
        print("No station sessions recorded yet.")
    else:
        for session in recent_stations:
            status = "✅" if session["left_at"] else "🔄"

            # Calculate duration
            if session["left_at"]:
                start = datetime.fromisoformat(session["joined_at"])
                end = datetime.fromisoformat(session["left_at"])
                duration = format_duration((end - start).total_seconds())
            else:
                duration = "In Progress"

            print(f"\n{status} {session['station_name']} ({session['station_prefix']})")
            print(f"   Server: {session['server_name']} ({session['server_code']})")
            print(f"   Started: {format_datetime(session['joined_at'])}")

            if session["left_at"]:
                print(f"   Ended: {format_datetime(session['left_at'])}")
                print(f"   Duration: {duration}")

    # ===== ACTIVITY TIMELINE =====
    print("\n📅 RECENT ACTIVITY TIMELINE")
    print("-" * 80)

    # Combine and sort all sessions by time
    all_sessions = []

    for session in recent_trains[:5]:
        all_sessions.append(
            {"type": "train", "time": session["joined_at"], "data": session}
        )

    for session in recent_stations[:5]:
        all_sessions.append(
            {"type": "station", "time": session["joined_at"], "data": session}
        )

    all_sessions.sort(key=lambda x: x["time"], reverse=True)

    for item in all_sessions[:10]:
        dt = datetime.fromisoformat(item["time"]).replace(tzinfo=timezone.utc)
        time_ago = datetime.now(timezone.utc) - dt

        if time_ago < timedelta(hours=1):
            time_ago_str = f"{int(time_ago.total_seconds() / 60)} minutes ago"
        elif time_ago < timedelta(days=1):
            time_ago_str = f"{int(time_ago.total_seconds() / 3600)} hours ago"
        else:
            time_ago_str = f"{int(time_ago.total_seconds() / 86400)} days ago"

        if item["type"] == "train":
            session = item["data"]
            status = "✅" if session["left_at"] else "🔄 Active"
            print(f"{format_datetime(item['time'])} ({time_ago_str})")
            print(
                f"  🚂 {status} Train {session['train_number']} - {session['start_station']} → {session['end_station']}"
            )
        else:
            session = item["data"]
            status = "✅" if session["left_at"] else "🔄 Active"
            print(f"{format_datetime(item['time'])} ({time_ago_str})")
            print(f"  📍 {status} Station {session['station_name']}")

    print("\n" + "=" * 80)


def print_active_sessions(db: TrackerDatabase, steam_id: str):
    """Print only currently active sessions."""

    active_train = db.get_active_train_session(steam_id)
    active_station = db.get_active_station_session(steam_id)

    if not active_train and not active_station:
        print("\n❌ No active sessions")
        return

    print("\n🔄 ACTIVE SESSIONS")
    print("-" * 80)

    if active_train:
        start = datetime.fromisoformat(active_train["joined_at"])
        duration = datetime.now(timezone.utc) - start

        # Format vehicle information with composition data
        vehicle_info = format_vehicle_info(active_train)

        print(
            f"\n🚂 Driving Train {active_train['train_number']} ({active_train['train_name']})"
        )
        print(f"   Vehicle: {vehicle_info}")
        print(
            f"   Route: {active_train['start_station']} → {active_train['end_station']}"
        )
        print(
            f"   Server: {active_train['server_name']} ({active_train['server_code']})"
        )
        print(f"   Started: {format_datetime(active_train['joined_at'])}")
        print(f"   Duration: {format_duration(duration.total_seconds())}")

    if active_station:
        start = datetime.fromisoformat(active_station["joined_at"])
        duration = datetime.now(timezone.utc) - start

        print(
            f"\n📍 Dispatching at {active_station['station_name']} ({active_station['station_prefix']})"
        )
        print(
            f"   Server: {active_station['server_name']} ({active_station['server_code']})"
        )
        print(f"   Started: {format_datetime(active_station['joined_at'])}")
        print(f"   Duration: {format_duration(duration.total_seconds())}")

    print()
