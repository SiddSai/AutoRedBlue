# This defines the tool object that the LLM can call

get_flight_info = {
    "name": "get_flight_info",
    "description": "Get flight information between two locations",
    "parameters": {
        "type": "object",
        "properties": {
            "loc_origin": {
                "type": "string",
                "description": "The departure airport, e.g. DUS",
            },
            "loc_destination": {
                "type": "string",
                "description": "The destination airport, e.g. HAM",
            },
        },
        "required": ["loc_origin", "loc_destination"],
    },
}