"""
Template configuration file for the IoT server application.
Copy this file to config.py and fill in your actual credentials.
"""

# MongoDB Configuration
MONGODB_CONNECTION_STRING = "your_mongodb_connection_string_here"
MONGODB_DATABASE = "your_database_name"
MONGODB_COLLECTION = "your_collection_name"

# Device IDs
DEVICE_IDS = {
    "FRIDGE1": "your_fridge1_device_id",
    "DISHWASHER": "your_dishwasher_device_id",
    "FRIDGE2": "your_fridge2_device_id"
}

# Sensor Configuration
SENSOR_CONFIG = {
    "MOISTURE": {
        "MAX_VALUE": 999,
        "SENSOR_KEY": "Moisture Meter - MoistureMeter"
    },
    "WATER_FLOW": {
        "MAX_FLOW_RATE_LPM": 10,
        "SENSOR_KEY": "WaterConsumptionSensor",
        "CONVERSION_FACTOR": 0.264172  # LPM to GPM conversion
    },
    "ELECTRICITY": {
        "VOLTAGE": 240,
        "HOURS": 1,
        "SENSOR_KEYS": {
            "FRIDGE1": "Ammeter",
            "DISHWASHER": "Ammeter2",
            "FRIDGE2": "Ammeter1"
        }
    }
} 