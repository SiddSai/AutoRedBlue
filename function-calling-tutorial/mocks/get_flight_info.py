# Mocks a python function response

def get_flight_info(json):
    loc_origin = json["loc_origin"]
    loc_destination = json["loc_destination"]
    return {
        "next_flight": "10:00 AM",
        "destination": loc_destination,
        "departure_airport": loc_origin,
        "arrival_airport": loc_destination,
        "flight_number": "AA1234",
        "airline": "American Airlines",
        "number_of_stops": 0,
        "flight_duration": "3 hours 30 minutes",
    }
    