#!/usr/bin/env python3
"""
Benchmark script for the DALI-ChatGPT LLM Bridge.
Sends 100 context queries to the LLM Bridge on 127.0.0.1:9000,
measures parse success rate, round-trip latency, and reports statistics.

Usage (inside the DALIA Docker container while the system is running):
    python3 /app/test_benchmark.py

Or from the host if port 9000 is exposed:
    python3 test_benchmark.py --host 127.0.0.1 --port 9000
"""

import socket
import time
import re
import json
import argparse
import statistics

LLM_HOST = "127.0.0.1"
LLM_PORT = 9000

# 50 emergency contexts + 50 agriculture contexts = 100 total
CONTEXTS = [
    # --- Emergency contexts (50) ---
    "fire detected at building_A",
    "earthquake magnitude 6.2 at city_center",
    "smoke detected at warehouse_7",
    "fire at hospital wing_B",
    "flood warning at riverside_district",
    "gas leak detected at factory_3",
    "earthquake magnitude 4.5 at suburb_north",
    "fire spreading at forest_area_12",
    "smoke detected at school_main_hall",
    "explosion reported at chemical_plant",
    "fire at residential_block_C",
    "earthquake magnitude 7.1 at downtown",
    "smoke detected at metro_station_5",
    "fire at oil_refinery",
    "flood at underground_parking",
    "gas leak at apartment_building_9",
    "earthquake magnitude 3.8 at industrial_zone",
    "fire at shopping_mall_east",
    "smoke detected at library_basement",
    "landslide warning at hillside_road",
    "fire at power_station_2",
    "earthquake magnitude 5.0 at old_town",
    "smoke detected at theater_main",
    "fire at airport_terminal_B",
    "tsunami warning at coastal_area",
    "fire at data_center_north",
    "earthquake magnitude 4.0 at university_campus",
    "smoke detected at restaurant_district",
    "fire at train_station_central",
    "volcanic_activity at mount_region",
    "fire at stadium_west",
    "earthquake magnitude 6.5 at port_area",
    "smoke detected at parking_garage_3",
    "fire at military_base_south",
    "hurricane warning at island_resort",
    "fire at construction_site_7",
    "earthquake magnitude 3.2 at village_east",
    "smoke detected at cinema_complex",
    "fire at nuclear_facility perimeter",
    "blizzard warning at mountain_pass",
    "fire at bridge_crossing_12",
    "earthquake magnitude 5.8 at financial_district",
    "smoke detected at hotel_lobby",
    "fire at farm_storage_building",
    "tornado warning at plains_region",
    "fire at museum_wing_A",
    "earthquake magnitude 4.3 at residential_area",
    "smoke detected at office_tower_15",
    "fire at port_warehouse_8",
    "wildfire approaching suburb_west",
    # --- Agriculture contexts (50) ---
    "soil moisture 20 pH 6.5 field north_field",
    "soil moisture 50 pH 4.0 field east_field",
    "soil moisture 15 pH 7.0 field south_field",
    "soil moisture 80 pH 5.5 field west_field",
    "soil moisture 35 pH 8.2 field greenhouse_1",
    "soil moisture 10 pH 6.0 field vineyard_A",
    "soil moisture 90 pH 5.0 field rice_paddy",
    "soil moisture 45 pH 7.5 field orchard_B",
    "soil moisture 25 pH 4.5 field blueberry_patch",
    "soil moisture 60 pH 6.8 field wheat_field_3",
    "temperature 42 humidity 15 forecast drought",
    "temperature 0 humidity 80 forecast frost",
    "temperature 38 humidity 90 forecast storm",
    "temperature -5 humidity 70 forecast snow",
    "temperature 35 humidity 25 forecast heatwave",
    "temperature 28 humidity 60 forecast clear",
    "temperature 15 humidity 85 forecast rain",
    "temperature 3 humidity 75 forecast frost",
    "temperature 45 humidity 10 forecast extreme_heat",
    "temperature 22 humidity 50 forecast cloudy",
    "soil moisture 5 pH 6.2 field potato_field",
    "soil moisture 70 pH 3.8 field tomato_row_2",
    "soil moisture 55 pH 7.8 field corn_field_A",
    "soil moisture 30 pH 5.2 field soybean_plot",
    "soil moisture 40 pH 6.0 field lettuce_bed",
    "soil moisture 12 pH 7.2 field carrot_patch",
    "soil moisture 85 pH 4.8 field strawberry_field",
    "soil moisture 48 pH 6.5 field sunflower_area",
    "soil moisture 22 pH 5.8 field olive_grove",
    "soil moisture 65 pH 7.0 field apple_orchard",
    "temperature 40 humidity 12 forecast drought",
    "temperature 1 humidity 90 forecast frost",
    "temperature 32 humidity 95 forecast thunderstorm",
    "temperature -2 humidity 65 forecast freezing",
    "temperature 36 humidity 20 forecast dry",
    "temperature 25 humidity 55 forecast partly_cloudy",
    "temperature 10 humidity 80 forecast sleet",
    "temperature 5 humidity 78 forecast frost",
    "temperature 43 humidity 8 forecast extreme_heat",
    "temperature 20 humidity 45 forecast mild",
    "soil moisture 8 pH 5.5 field pepper_garden",
    "soil moisture 75 pH 4.2 field cranberry_bog",
    "soil moisture 52 pH 8.0 field asparagus_bed",
    "soil moisture 28 pH 6.3 field pumpkin_patch",
    "soil moisture 38 pH 5.0 field herb_garden",
    "soil moisture 18 pH 7.4 field onion_field",
    "soil moisture 95 pH 4.5 field mushroom_house",
    "soil moisture 42 pH 6.7 field barley_field_2",
    "soil moisture 33 pH 5.3 field garlic_plot",
    "soil moisture 58 pH 7.1 field melon_field",
]

# Regex to check if response is a valid Prolog fact: functor(args...)
PROLOG_FACT_RE = re.compile(r'^[a-z_][a-zA-Z0-9_]*\(.*\)$', re.DOTALL)


def send_query(host, port, context, timeout=30):
    """Send a context string to the LLM Bridge and return (response, latency_ms, success)."""
    start = time.time()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        
        message = f"{context}.\n"
        sock.sendall(message.encode('utf-8'))
        
        response = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
            if b"\n" in response:
                break
        
        sock.close()
        elapsed_ms = (time.time() - start) * 1000
        
        text = response.decode('utf-8').strip().rstrip('.')
        
        is_valid = bool(PROLOG_FACT_RE.match(text))
        
        return text, elapsed_ms, is_valid, None
        
    except Exception as e:
        elapsed_ms = (time.time() - start) * 1000
        return None, elapsed_ms, False, str(e)


def main():
    parser = argparse.ArgumentParser(description="Benchmark DALI LLM Bridge")
    parser.add_argument("--host", default=LLM_HOST, help="LLM Bridge host")
    parser.add_argument("--port", type=int, default=LLM_PORT, help="LLM Bridge port")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between queries (seconds)")
    parser.add_argument("--output", default="benchmark_results.json", help="Output JSON file")
    args = parser.parse_args()
    
    print(f"=== DALI LLM Bridge Benchmark ===")
    print(f"Target: {args.host}:{args.port}")
    print(f"Queries: {len(CONTEXTS)}")
    print(f"Delay between queries: {args.delay}s")
    print()
    
    results = []
    successes = 0
    failures = []
    latencies = []
    
    for i, ctx in enumerate(CONTEXTS):
        print(f"[{i+1:3d}/{len(CONTEXTS)}] {ctx[:60]}...", end=" ", flush=True)
        
        response, latency_ms, is_valid, error = send_query(args.host, args.port, ctx)
        
        result = {
            "index": i + 1,
            "context": ctx,
            "response": response,
            "latency_ms": round(latency_ms, 1),
            "valid_prolog": is_valid,
            "error": error
        }
        results.append(result)
        
        if is_valid:
            successes += 1
            latencies.append(latency_ms)
            print(f"OK ({latency_ms:.0f}ms) -> {response}")
        elif error:
            failures.append(result)
            print(f"ERROR ({latency_ms:.0f}ms) -> {error}")
        else:
            failures.append(result)
            print(f"PARSE FAIL ({latency_ms:.0f}ms) -> {response}")
        
        if i < len(CONTEXTS) - 1:
            time.sleep(args.delay)
    
    # Statistics
    print()
    print("=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    
    total = len(CONTEXTS)
    print(f"Total queries:      {total}")
    print(f"Successful parses:  {successes} ({100*successes/total:.0f}%)")
    print(f"Failures:           {len(failures)} ({100*len(failures)/total:.0f}%)")
    
    if latencies:
        print()
        print("LATENCY (successful queries):")
        print(f"  Minimum:          {min(latencies):.0f} ms")
        print(f"  Maximum:          {max(latencies):.0f} ms")
        print(f"  Mean:             {statistics.mean(latencies):.0f} ms")
        print(f"  Median:           {statistics.median(latencies):.0f} ms")
        if len(latencies) >= 20:
            sorted_lat = sorted(latencies)
            p95_idx = int(0.95 * len(sorted_lat))
            print(f"  95th percentile:  {sorted_lat[p95_idx]:.0f} ms")
    
    if failures:
        print()
        print("FAILURE DETAILS:")
        for f in failures:
            print(f"  [{f['index']}] {f['context'][:50]}...")
            if f['error']:
                print(f"       Error: {f['error']}")
            else:
                print(f"       Response: {f['response']}")
    
    # Save full results to JSON
    summary = {
        "total_queries": total,
        "successes": successes,
        "success_rate_pct": round(100 * successes / total, 1),
        "failures_count": len(failures),
        "latency_min_ms": round(min(latencies), 1) if latencies else None,
        "latency_max_ms": round(max(latencies), 1) if latencies else None,
        "latency_mean_ms": round(statistics.mean(latencies), 1) if latencies else None,
        "latency_median_ms": round(statistics.median(latencies), 1) if latencies else None,
        "latency_p95_ms": round(sorted(latencies)[int(0.95 * len(latencies))], 1) if len(latencies) >= 20 else None,
        "results": results
    }
    
    with open(args.output, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print()
    print(f"Full results saved to: {args.output}")
    print()
    print("--- Copy these values into the paper ---")
    print(f"Parse success rate: {successes}/{total} ({100*successes/total:.0f}%)")
    if latencies:
        print(f"Latency min:    {min(latencies):.0f} ms")
        print(f"Latency max:    {max(latencies):.0f} ms")
        print(f"Latency mean:   {statistics.mean(latencies):.0f} ms")
        print(f"Latency median: {statistics.median(latencies):.0f} ms")
        if len(latencies) >= 20:
            print(f"Latency p95:    {sorted(latencies)[int(0.95 * len(latencies))]:.0f} ms")


if __name__ == "__main__":
    main()
