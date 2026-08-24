import time
import math
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from src import algorithm
app = Flask(__name__)


@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    return response


def direct_distance_km(a, b):
    """Great-circle distance in km between two [lat, lon] points."""
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dphi = lat2 - lat1
    dlmb = lon2 - lon1
    h = math.sin(dphi / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlmb / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))


@app.route('/', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "MARG by Shubham"}), 200


@app.route('/map', methods=['POST'])
def get_user_input():
    user_input = request.json
    print("Received user input:\n\n", user_input, "\n\n\n")

    t0 = time.perf_counter()
    x = algorithm.main(user_input['start'], user_input['end'], float(user_input['ship']['Speed']))
    computed_ms = int((time.perf_counter() - t0) * 1000)

    eta_hrs = float(x[1])
    route_km = float(x[2])
    direct_km = direct_distance_km(user_input['start'], user_input['end'])

    departure = datetime.utcnow()
    arrival = departure + timedelta(hours=eta_hrs)

    result = {
        "path": x[0],
        "eta": x[1],
        "km": x[2],
        "fuel": x[3],
        # ── MARG enriched analytics ──
        "waypoints": len(x[0]),
        "direct_km": round(direct_km, 1),
        "detour_pct": round((route_km / direct_km - 1) * 100, 1) if direct_km > 0 else None,
        "efficiency": round(direct_km / route_km * 100, 1) if route_km > 0 else None,
        "avg_kmh": round(route_km / eta_hrs, 1) if eta_hrs > 0 else None,
        "avg_kn": round((route_km * 0.53996) / eta_hrs, 2) if eta_hrs > 0 else None,
        "fuel_per_hr": round(float(x[3]) / eta_hrs, 1) if eta_hrs > 0 else None,
        "computed_ms": computed_ms,
        "departure": departure.strftime('%Y-%m-%dT%H:%M:%SZ'),
        "arrival": arrival.strftime('%Y-%m-%dT%H:%M:%SZ'),
    }

    return jsonify(result), 200


if __name__ == '__main__':
    import os
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False, use_reloader=False)
