# IoT Server Application

This server application processes and analyzes data from various IoT devices in a household setting, including moisture sensors, water flow meters, and electricity consumption meters. It connects to a PostgreSQL database to store and retrieve device data.

## Features

- Real-time data processing from multiple IoT devices
- Moisture level monitoring
- Water flow rate calculation
- Electricity consumption tracking
- PostgreSQL database integration using psycopg2
- Socket-based client-server communication

## Prerequisites

- Python 3.8 or higher
- PostgreSQL database (local or remote)
- Network access to the PostgreSQL database

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-directory>
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Configure the application:
   - Copy `config.example.py` to `config.py`:
     ```bash
     cp config.example.py config.py
     ```
   - Edit `config.py` with your actual credentials and settings:
     - PostgreSQL connection parameters (host, port, database, user, password)
     - Device IDs
     - Sensor configurations
   - Make sure to never commit your `config.py` file to version control

## Usage

1. Start the server:
```bash
python server.py
```

2. Enter the server IP address and port number when prompted

3. Connect a client to the server using the same IP and port

4. The server accepts the following commands:
   - "1": Get average moisture level for Fridge1
   - "2": Get average water flow for DishWasher
   - "3": Get maximum electricity consumption across all devices

## Configuration

The application settings are managed through the `config.py` file:

1. Create your configuration:
   - Copy `config.example.py` to `config.py`
   - Fill in your actual credentials and settings
   - The `config.py` file is ignored by git (see `.gitignore`)

2. Configuration options:
   - NeonDB connection settings
   - Device IDs
   - Sensor configurations
   - Conversion factors and constants

## License

This project is licensed under the MIT License - see the LICENSE file for details.
