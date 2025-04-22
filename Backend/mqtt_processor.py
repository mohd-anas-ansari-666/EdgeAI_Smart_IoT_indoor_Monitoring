import paho.mqtt.client as mqtt
import time
from datetime import datetime
import pymongo
import numpy as np
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

# MongoDB connection
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["iot_monitoring"]
sensor_data_collection = db["sensor_data"]

# MQTT settings
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_KEEPALIVE = 60

# Topics
TEMP_TOPIC = "home/sensors/temperature"
HUMID_TOPIC = "home/sensors/humidity"
AIR_QUALITY_TOPIC = "home/sensors/air_quality"

# Control topics
AC_CONTROL_TOPIC = "home/devices/ac"
PURIFIER_CONTROL_TOPIC = "home/devices/purifier"
DEHUMIDIFIER_CONTROL_TOPIC = "home/devices/dehumidifier"

# Device states
ac_state = "OFF"
purifier_state = "OFF"
dehumidifier_state = "OFF"

# Load ML models
try:
    temp_model = joblib.load('models/temp_model.pkl')
    humid_model = joblib.load('models/humid_model.pkl')
    air_quality_model = joblib.load('models/air_quality_model.pkl')
    scaler = joblib.load('models/scaler.pkl')
    models_loaded = True
    print("ML models loaded successfully")
except FileNotFoundError:
    models_loaded = False
    print("ML models not found. Will create new models with incoming data.")
    # Initialize data storage for training
    train_data = pd.DataFrame(columns=['timestamp', 'temperature', 'humidity', 'air_quality'])


# Data storage for predictions
current_data = {
    'temperature': None,
    'humidity': None,
    'air_quality': None,
    'timestamp': None
}

# Get historical data for prediction
def get_historical_data(hours=24):
    end_time = datetime.now()
    start_time = end_time - pd.Timedelta(hours=hours)
    
    cursor = sensor_data_collection.find({
        'timestamp': {'$gte': start_time, '$lte': end_time}
    })
    
    data = pd.DataFrame(list(cursor))
    if not data.empty and 'timestamp' in data.columns:
        data['hour'] = data['timestamp'].dt.hour
        data['day_of_week'] = data['timestamp'].dt.dayofweek
    
    return data

# Predict using ML models
def predict_values():
    if not models_loaded or None in current_data.values():
        return None, None, None
    
    # Get time features for prediction
    now = datetime.now()
    hour = now.hour
    day_of_week = now.weekday()
    
    # # Create feature vector for prediction
    # features = np.array([[
    #     current_data['temperature'], 
    #     current_data['humidity'],
    #     current_data['air_quality'],
    #     hour,
    #     day_of_week
    # ]])
    
    # # Scale features
    # scaled_features = scaler.transform(features)
    # Define feature names in the same order used during training
    feature_names = ['temperature', 'humidity', 'air_quality', 'hour', 'day_of_week']
    features = pd.DataFrame([[
        current_data['temperature'], 
        current_data['humidity'],
        current_data['air_quality'],
        hour,
        day_of_week
    ]], columns=feature_names)

    # Now transform safely
    scaled_features = scaler.transform(features)
    
    # Make predictions for next hour
    temp_pred = temp_model.predict(scaled_features)[0]
    humid_pred = humid_model.predict(scaled_features)[0]
    air_quality_pred = air_quality_model.predict(scaled_features)[0]
    
    return temp_pred, humid_pred, air_quality_pred

# Determine comfort level
def determine_comfort_level(temp, humid, air_quality):
    comfort = "comfortable"
    reasons = []
    
    # Temperature checks
    if temp > 28:
        comfort = "uncomfortable"
        reasons.append("high temperature")
    elif temp < 18:
        comfort = "uncomfortable"
        reasons.append("low temperature")
    
    # Humidity checks
    if humid > 65:
        comfort = "uncomfortable"
        reasons.append("high humidity")
    elif humid < 30:
        comfort = "uncomfortable"
        reasons.append("low humidity")
    
    # Air quality checks (assuming PPM scale where higher is worse)
    if air_quality > 700:
        comfort = "poor air"
        reasons.append("poor air quality")
    
    return comfort, reasons

# Control devices based on comfort level
def control_devices(comfort, reasons, mqtt_client):
    global ac_state, purifier_state, dehumidifier_state
    
    # Default states if comfortable
    new_ac_state = "OFF"
    new_purifier_state = "OFF"
    new_dehumidifier_state = "OFF"
    
    # Adjust for discomfort
    if "high temperature" in reasons:
        new_ac_state = "ON"
    
    if "poor air quality" in reasons:
        new_purifier_state = "ON"
    
    if "high humidity" in reasons:
        new_dehumidifier_state = "ON"
    
    # Publish changes if needed
    if new_ac_state != ac_state:
        mqtt_client.publish(AC_CONTROL_TOPIC, new_ac_state)
        ac_state = new_ac_state
    
    if new_purifier_state != purifier_state:
        mqtt_client.publish(PURIFIER_CONTROL_TOPIC, new_purifier_state)
        purifier_state = new_purifier_state
    
    if new_dehumidifier_state != dehumidifier_state:
        mqtt_client.publish(DEHUMIDIFIER_CONTROL_TOPIC, new_dehumidifier_state)
        dehumidifier_state = new_dehumidifier_state

# Create or update ML models
def update_ml_models():
    global temp_model, humid_model, air_quality_model, scaler, models_loaded
    
    # Get historical data
    data = get_historical_data(hours=72)  # Use 3 days of data
    
    if len(data) < 24:  # Need at least a day of data
        print("Not enough data to train models")
        return
    
    # Feature engineering
    data['hour'] = data['timestamp'].dt.hour
    data['day_of_week'] = data['timestamp'].dt.dayofweek
    
    # Prepare features and targets
    features = data[['temperature', 'humidity', 'air_quality', 'hour', 'day_of_week']].values
    temp_target = data['temperature'].shift(-6).dropna()  # Predict 1 hour ahead (assuming readings every 10 min)
    humid_target = data['humidity'].shift(-6).dropna()
    air_quality_target = data['air_quality'].shift(-6).dropna()
    
    # Drop NaN values from features to match target length
    features = features[:len(temp_target)]
    
    # Scale features
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)
    
    # Train models
    temp_model = RandomForestRegressor(n_estimators=50)
    temp_model.fit(scaled_features, temp_target)
    
    humid_model = RandomForestRegressor(n_estimators=50)
    humid_model.fit(scaled_features, humid_target)
    
    air_quality_model = RandomForestRegressor(n_estimators=50)
    air_quality_model.fit(scaled_features, air_quality_target)
    
    # Save models
    joblib.dump(temp_model, 'models/temp_model.pkl')
    joblib.dump(humid_model, 'models/humid_model.pkl')
    joblib.dump(air_quality_model, 'models/air_quality_model.pkl')
    joblib.dump(scaler, 'models/scaler.pkl')
    
    models_loaded = True
    print("ML models updated and saved")

# MQTT callbacks
def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe(TEMP_TOPIC)
    client.subscribe(HUMID_TOPIC)
    client.subscribe(AIR_QUALITY_TOPIC)

def on_message(client, userdata, msg):
    topic = msg.topic
    value = float(msg.payload.decode())
    timestamp = datetime.now()
    
    # Update current data
    if topic == TEMP_TOPIC:
        current_data['temperature'] = value
    elif topic == HUMID_TOPIC:
        current_data['humidity'] = value
    elif topic == AIR_QUALITY_TOPIC:
        current_data['air_quality'] = value
    
    current_data['timestamp'] = timestamp
    
    # Save to MongoDB
    if None not in current_data.values():
        sensor_data = {
            'temperature': current_data['temperature'],
            'humidity': current_data['humidity'],
            'air_quality': current_data['air_quality'],
            'timestamp': current_data['timestamp']
        }
        sensor_data_collection.insert_one(sensor_data)
        
        # Predict future values
        temp_pred, humid_pred, air_quality_pred = predict_values()
        
        # Determine comfort level
        comfort, reasons = determine_comfort_level(
            current_data['temperature'], 
            current_data['humidity'], 
            current_data['air_quality']
        )
        
        # Control devices based on comfort
        control_devices(comfort, reasons, client)
        
        # Save prediction and comfort to MongoDB
        if temp_pred is not None:
            prediction_data = {
                'temperature_pred': temp_pred,
                'humidity_pred': humid_pred,
                'air_quality_pred': air_quality_pred,
                'comfort_level': comfort,
                'comfort_reasons': reasons,
                'ac_state': ac_state,
                'purifier_state': purifier_state,
                'dehumidifier_state': dehumidifier_state,
                'timestamp': timestamp
            }
            db["predictions"].insert_one(prediction_data)

def main():
    # Setup MQTT client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    
    client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)
    
    # Start MQTT loop
    client.loop_start()
    
    try:
        while True:
            # Update ML models every 6 hours
            if not models_loaded or int(time.time()) % (6*60*60) < 10:
                update_ml_models()
            
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        print("Exiting program")
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()