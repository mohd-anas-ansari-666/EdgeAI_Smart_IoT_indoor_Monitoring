import pandas as pd
import numpy as np
import joblib
from datetime import datetime, timedelta
import pymongo
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score

# MongoDB connection
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["iot_monitoring"]
sensor_data_collection = db["sensor_data"]

def generate_sample_data(days=5, readings_per_hour=6):
    """Generate sample data for initial model training"""
    data = []
    now = datetime.now()
    
    for day in range(days):
        for hour in range(24):
            for reading in range(readings_per_hour):
                timestamp = now - timedelta(days=day, hours=hour, minutes=reading*(60//readings_per_hour))
                
                # Generate reasonable values with daily patterns
                # Temperature: cooler at night, warmer during day
                base_temp = 22 + 5 * np.sin(np.pi * hour / 12)
                temp = base_temp + np.random.normal(0, 1)
                
                # Humidity: higher at night, lower during day
                base_humid = 50 + 10 * np.sin(np.pi * (hour + 18) / 12)
                humid = base_humid + np.random.normal(0, 3)
                
                # Air quality: worse during peak hours
                base_air = 500 + 100 * np.sin(np.pi * hour / 12)
                air_quality = base_air + np.random.normal(0, 50)
                
                # Ensure values in reasonable ranges
                temp = max(15, min(30, temp))
                humid = max(30, min(70, humid))
                air_quality = max(300, min(800, air_quality))
                
                data.append({
                    'timestamp': timestamp,
                    'temperature': temp,
                    'humidity': humid,
                    'air_quality': air_quality
                })
    
    return pd.DataFrame(data)

def get_real_data():
    """Get real data from MongoDB"""
    cursor = sensor_data_collection.find()
    data = list(cursor)
    
    if not data:
        print("No real data found, using generated sample data.")
        return generate_sample_data()
    
    return pd.DataFrame(data)

def preprocess_data(df):
    """Preprocess data for model training"""
    # Sort by timestamp
    df = df.sort_values('timestamp')
    
    # Extract time features
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    
    # Create target variables (next hour predictions)
    # Assuming readings every 10 minutes, shift by 6 to get 1 hour ahead
    df['next_temp'] = df['temperature'].shift(-6)
    df['next_humid'] = df['humidity'].shift(-6)
    df['next_air_quality'] = df['air_quality'].shift(-6)
    
    # Drop rows with NaN in target
    df = df.dropna()
    
    return df

def train_models(df):
    """Train prediction models"""
    # Define features and targets
    features = df[['temperature', 'humidity', 'air_quality', 'hour', 'day_of_week']]
    temp_target = df['next_temp']
    humid_target = df['next_humid']
    air_quality_target = df['next_air_quality']
    
    # Split data
    X_train, X_test, y_temp_train, y_temp_test = train_test_split(
        features, temp_target, test_size=0.2, random_state=42)
    _, _, y_humid_train, y_humid_test = train_test_split(
        features, humid_target, test_size=0.2, random_state=42)
    _, _, y_air_train, y_air_test = train_test_split(
        features, air_quality_target, test_size=0.2, random_state=42)
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train temperature model
    temp_model = RandomForestRegressor(n_estimators=100, random_state=42)
    temp_model.fit(X_train_scaled, y_temp_train)
    temp_preds = temp_model.predict(X_test_scaled)
    temp_rmse = np.sqrt(mean_squared_error(y_temp_test, temp_preds))
    temp_r2 = r2_score(y_temp_test, temp_preds)
    
    # Train humidity model
    humid_model = RandomForestRegressor(n_estimators=100, random_state=42)
    humid_model.fit(X_train_scaled, y_humid_train)
    humid_preds = humid_model.predict(X_test_scaled)
    humid_rmse = np.sqrt(mean_squared_error(y_humid_test, humid_preds))
    humid_r2 = r2_score(y_humid_test, humid_preds)
    
    # Train air quality model
    air_quality_model = RandomForestRegressor(n_estimators=100, random_state=42)
    air_quality_model.fit(X_train_scaled, y_air_train)
    air_preds = air_quality_model.predict(X_test_scaled)
    air_rmse = np.sqrt(mean_squared_error(y_air_test, air_preds))
    air_r2 = r2_score(y_air_test, air_preds)
    
    # Print model performance
    print(f"Temperature Model - RMSE: {temp_rmse:.2f}, R²: {temp_r2:.2f}")
    print(f"Humidity Model - RMSE: {humid_rmse:.2f}, R²: {humid_r2:.2f}")
    print(f"Air Quality Model - RMSE: {air_rmse:.2f}, R²: {air_r2:.2f}")
    
    # Save models
    joblib.dump(temp_model, 'models/temp_model.pkl')
    joblib.dump(humid_model, 'models/humid_model.pkl')
    joblib.dump(air_quality_model, 'models/air_quality_model.pkl')
    joblib.dump(scaler, 'models/scaler.pkl')
    
    print("Models saved successfully")
    
    return temp_model, humid_model, air_quality_model, scaler

def determine_comfort_level(temp, humid, air_quality):
    """Determine comfort level based on sensor readings"""
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
    
    # Air quality checks
    if air_quality > 700:
        comfort = "poor air"
        reasons.append("poor air quality")
    
    return comfort, reasons

def get_device_recommendations(comfort, reasons):
    """Get device control recommendations based on comfort level"""
    devices = {
        'ac': 'OFF',
        'purifier': 'OFF',
        'dehumidifier': 'OFF'
    }
    
    if "high temperature" in reasons:
        devices['ac'] = 'ON'
    
    if "poor air quality" in reasons:
        devices['purifier'] = 'ON'
    
    if "high humidity" in reasons:
        devices['dehumidifier'] = 'ON'
    
    return devices

def infer_on_new_data(temp, humid, air_quality, hour, day_of_week, 
                      temp_model, humid_model, air_model, scaler):
    """Make predictions on new data"""
    # Create feature vector
    # features = np.array([[temp, humid, air_quality, hour, day_of_week]])
    features = pd.DataFrame([[
    temp, humid, air_quality, hour, day_of_week
    ]], columns=['temperature', 'humidity', 'air_quality', 'hour', 'day_of_week'])

    
    # Scale features
    scaled_features = scaler.transform(features)
    
    # Make predictions
    temp_pred = temp_model.predict(scaled_features)[0]
    humid_pred = humid_model.predict(scaled_features)[0]
    air_pred = air_model.predict(scaled_features)[0]
    
    # Current comfort level
    current_comfort, current_reasons = determine_comfort_level(temp, humid, air_quality)
    
    # Predicted comfort level
    pred_comfort, pred_reasons = determine_comfort_level(temp_pred, humid_pred, air_pred)
    
    # Device recommendations
    device_recommendations = get_device_recommendations(current_comfort, current_reasons)
    
    return {
        'current': {
            'temperature': temp,
            'humidity': humid,
            'air_quality': air_quality,
            'comfort': current_comfort,
            'reasons': current_reasons
        },
        'prediction': {
            'temperature': temp_pred,
            'humidity': humid_pred,
            'air_quality': air_pred,
            'comfort': pred_comfort,
            'reasons': pred_reasons
        },
        'device_recommendations': device_recommendations
    }

def main():
    """Main function to train and test models"""
    # Create models directory if it doesn't exist
    import os
    if not os.path.exists('models'):
        os.makedirs('models')
    
    # Get data (real or sample)
    print("Getting data...")
    data = get_real_data()
    
    # Preprocess data
    print("Preprocessing data...")
    processed_data = preprocess_data(data)
    
    # Train models
    print("Training models...")
    temp_model, humid_model, air_model, scaler = train_models(processed_data)
    
    # Test inference
    print("\nTesting inference with sample data:")
    test_temp = 25.0
    test_humid = 55.0
    test_air = 550.0
    test_hour = 14
    test_day = 2  # Wednesday
    
    results = infer_on_new_data(
        test_temp, test_humid, test_air, test_hour, test_day,
        temp_model, humid_model, air_model, scaler
    )
    
    print("\nInference results:")
    print(f"Current conditions: {results['current']['temperature']:.1f}°C, " 
          f"{results['current']['humidity']:.1f}%, "
          f"{results['current']['air_quality']:.1f} PPM")
    print(f"Comfort level: {results['current']['comfort']}")
    if results['current']['reasons']:
        print(f"Reasons: {', '.join(results['current']['reasons'])}")
    
    print(f"\nPredicted conditions: {results['prediction']['temperature']:.1f}°C, "
          f"{results['prediction']['humidity']:.1f}%, "
          f"{results['prediction']['air_quality']:.1f} PPM")
    print(f"Predicted comfort: {results['prediction']['comfort']}")
    if results['prediction']['reasons']:
        print(f"Predicted reasons: {', '.join(results['prediction']['reasons'])}")
    
    print("\nDevice recommendations:")
    for device, state in results['device_recommendations'].items():
        print(f"  {device}: {state}")

if __name__ == "__main__":
    main()