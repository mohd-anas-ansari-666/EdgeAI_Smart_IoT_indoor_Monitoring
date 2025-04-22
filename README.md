# Edge AI IoT Indoor Environmental Monitoring & Smart Automation System

This project implements an Edge AI-based IoT system for indoor weather and air quality monitoring. The system collects environmental data from sensors, processes it on an edge server, and automatically controls devices like AC, Air Purifier, Humdifier, Dehumidifier to maintain optimal comfort levels.

## System Architecture

### Components
1. **ESP32 Microcontroller**
   - Connected to DHT11 (temperature/humidity) and MQ135 (air quality) sensors
   - Publishes sensor data to MQTT broker
   - Subscribes to control commands for device operation

2. **MQTT Broker (Eclipse Mosquitto)**
   - Handles message passing between ESP32 and edge server

3. **Edge Server (Python)**
   - Subscribes to sensor data
   - Stores data in MongoDB
   - Runs ML models for prediction analysis and evaluate environmental comfort levels
   - Controls devices through MQTT commands

4. **MongoDB Database**
   - Stores sensor readings and predictions

5. **Frontend Dashboard (Vite + Tailwind CSS)**
   - Displays real-time data and predictions
   - Shows comfort status and device states
   - Provides visual alerts for poor environmental conditions

## Getting Started

### Hardware Requirements
- ESP32 development board
- DHT11 temperature and humidity sensor
- MQ135 air quality sensor
- Relay modules for controlling AC, air purifier, and dehumidifier
- Power supply for ESP32 and sensors

### Software Requirements
- Arduino IDE (for ESP32 programming)
- Python 3.8+ with required packages
- Node.js and npm (for frontend)
- MongoDB
- Mosquitto MQTT broker

### Installation

#### 1. ESP32 Setup
1. Connect the DHT11 sensor to pin 4
2. Connect the MQ135 sensor to pin 34
3. Connect relay modules to pins 16, 17, and 18
4. Install the required Arduino libraries:
   - WiFi
   - PubSubClient
   - DHT
5. Upload the ESP32 code to your device, after updating WiFi and MQTT broker settings

#### 2. MQTT Broker Setup
1. Download Eclipse Mosquitto Installer
- Go to the official download page:  
  [https://mosquitto.org/download/](https://mosquitto.org/download/)  
- Download the Windows installer (e.g., `mosquitto-<version>-installer.exe`).

2. Run the Installer
- During installation, choose to install the **Service** when prompted.
- Also, make sure to install required dependencies (OpenSSL and pthreads).

3. Start Mosquitto Service
Open **Command Prompt as Administrator** and run:
```cmd
net start mosquitto
```

#### 3. MongoDB Setup
1. Download MongoDB
- Visit the official MongoDB Community Edition download page:  
  [https://www.mongodb.com/try/download/community](https://www.mongodb.com/try/download/community)
- Select your Windows version and download the **MSI installer**.

2. Install MongoDB
- Run the downloaded MSI installer.
- Choose the **Complete** setup type.
- Make sure the option **"Install MongoDB as a Service"** is checked.
- You may also install **MongoDB Compass** (optional GUI tool).

3. Start MongoDB Service
- Open **Command Prompt as Administrator**.
- Start the MongoDB service by running:
  ```cmd
  net start MongoDB
   ```

#### 4. Python Backend Setup
1. Install required Python packages:
   ```
   pip install paho-mqtt pymongo scikit-learn pandas numpy joblib flask
   ```

2. Create directories for ML models:
   ```
   mkdir -p models
   ```

3. Start the backend services:
   ```
   # Start ML model training and monitoring
   python train_models.py
   
   # Start MQTT subscriber service
   python mqtt_processor.py
   
   # Start API server
   python api_endpoints.py
   ```

#### 5. Frontend Setup
1. Navigate to the frontend directory
2. Install dependencies:
   ```
   npm install
   ```
3. Start development server:
   ```
   npm run dev
   ```

## Data Flow

1. **Data Collection**: ESP32 reads sensor values every 10 seconds
2. **Data Publishing**: Sensor data is published to MQTT topics
3. **Data Processing**: Python backend subscribes to data and stores in MongoDB
4. **Analysis**: ML models predict future values and determine comfort level
5. **Automation**: System sends commands to control devices based on analysis
6. **Visualization**: Frontend polls API endpoints to display real-time and historical data

## Code Structure

### ESP32 Arduino Code
- Handles sensor reading and MQTT communication
- Controls relay switches based on MQTT commands

### Python Backend
- `mqtt_processor.py`: Main MQTT subscriber and controller
- `train_models.py`: Trains and updates ML models
- `api_endpoints.py`: Provides REST API endpoints for frontend

### ML Model
- Uses Random Forest Regression to predict temperature, humidity, and air quality
- Determines comfort level based on sensor readings
- Recommends device states to maintain optimal environment

### Frontend
- `App.jsx`: Main application component
- Components:
  - `DashboardWidget.jsx`: Displays sensor values
  - `SensorChart.jsx`: Shows historical data
  - `DeviceControl.jsx`: Displays device status
  - `AlertPopup.jsx`: Shows environmental alerts

## MQTT Topics

### Data Topics
- `home/sensors/temperature`: Temperature readings
- `home/sensors/humidity`: Humidity readings
- `home/sensors/air_quality`: Air quality readings

### Control Topics
- `home/devices/ac`: AC control (ON/OFF)
- `home/devices/purifier`: Air purifier control (ON/OFF)
- `home/devices/dehumidifier`: Dehumidifier control (ON/OFF)

## API Endpoints

- `/api/latest-data`: Get latest sensor data and predictions
- `/api/historical-data`: Get historical sensor data for charts
- `/api/comfort-history`: Get comfort level history
- `/api/device-history`: Get device state history

## Comfort Levels

The system defines three comfort levels:
1. **Comfortable**: Optimal environmental conditions
2. **Uncomfortable**: Temperature or humidity outside optimal range
3. **Poor Air**: Air quality below acceptable level

## Troubleshooting

### ESP32 Connectivity Issues
- Check WiFi credentials in the ESP32 code
- Verify MQTT broker address and port
- Ensure ESP32 has sufficient power

### Data Not Appearing in Frontend
- Check that MongoDB service is running
- Verify that the Python backend is receiving MQTT messages
- Check API server logs for any errors

### Devices Not Responding
- Check relay connections
- Verify that MQTT commands are being published
- Check that ESP32 is subscribed to control topics

## Future Enhancements

- Add email/SMS notifications for critical alerts
- Implement user authentication for the dashboard
- Add manual control options in the frontend
- Implement energy usage optimization
- Extend ML models to include seasonal patterns
