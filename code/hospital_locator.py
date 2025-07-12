import sys
import json
from geopy.distance import geodesic

HOSPITAL_DATA_PATH = "hospital_doctor_data.json"

def find_nearest_hospital(user_lat, user_lon, specialist):
    try:
        with open(HOSPITAL_DATA_PATH, 'r') as f:
            hospital_data = json.load(f)

        nearest = None
        min_distance = float("inf")
        for name, info in hospital_data.items():
            specialties = [doc['specialty'] for doc in info['doctors']]
            if specialist not in specialties:
                continue
            hosp_loc = (info['location']['lat'], info['location']['lon'])
            dist = geodesic((user_lat, user_lon), hosp_loc).miles
            if dist < min_distance:
                min_distance = dist
                nearest = {
                    "name": name,
                    "location": hosp_loc,
                    "distance": dist
                }

        if nearest:
            print(json.dumps(nearest))
        else:
            print(json.dumps({"message": "No hospital found with the required specialist."}))

    except Exception as e:
        print(json.dumps({"error": str(e)}))

if __name__ == "__main__":
    if len(sys.argv) == 4:
        try:
            user_lat = float(sys.argv[1])
            user_lon = float(sys.argv[2])
            specialist = sys.argv[3]
            find_nearest_hospital(user_lat, user_lon, specialist)
        except Exception as e:
            print(json.dumps({"error": f"Invalid input or processing error: {str(e)}"}))
    else:
        print(json.dumps({"error": "Usage: python hospital_locator.py <lat> <lon> <specialist>"}))
