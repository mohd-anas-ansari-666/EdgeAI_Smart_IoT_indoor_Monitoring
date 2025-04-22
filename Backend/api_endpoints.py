from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["iot_monitoring"]
sensor_data_collection = db["sensor_data"]
predictions_collection = db["predictions"]

app = FastAPI(title="IoT Monitoring API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class SensorData(BaseModel):
    temperature: float
    humidity: float
    air_quality: float
    timestamp: datetime

class PredictionData(BaseModel):
    temperature_pred: float
    humidity_pred: float
    air_quality_pred: float
    comfort_level: str
    comfort_reasons: List[str]
    ac_state: str
    purifier_state: str
    dehumidifier_state: str
    timestamp: datetime

@app.get("/")
def read_root():
    return {"message": "IoT Monitoring API is running"}

@app.get("/api/latest-data")
def get_latest_data():
    # Get latest sensor readings
    latest_sensor = sensor_data_collection.find_one(
        sort=[("timestamp", -1)]  # Sort by timestamp descending
    )
    
    if not latest_sensor:
        raise HTTPException(status_code=404, detail="No sensor data found")
    
    # Convert ObjectId to string for JSON serialization
    latest_sensor["_id"] = str(latest_sensor["_id"])
    
    # Get latest prediction
    latest_prediction = predictions_collection.find_one(
        sort=[("timestamp", -1)]
    )
    
    if not latest_prediction:
        # If no prediction exists, use current values as prediction
        latest_prediction = {
            "temperature_pred": latest_sensor["temperature"],
            "humidity_pred": latest_sensor["humidity"],
            "air_quality_pred": latest_sensor["air_quality"],
            "comfort_level": "comfortable",  # Default
            "comfort_reasons": [],
            "ac_state": "OFF",
            "purifier_state": "OFF",
            "dehumidifier_state": "OFF",
            "timestamp": latest_sensor["timestamp"]
        }
    else:
        # Convert ObjectId to string for JSON serialization
        latest_prediction["_id"] = str(latest_prediction["_id"])
    
    # Combine sensor data and prediction data
    combined_data = {**latest_sensor, **latest_prediction}
    
    return combined_data

@app.get("/api/historical-data")
def get_historical_data(hours: int = 24):
    """Get historical sensor data for charts"""
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)
    
    # Query MongoDB for data in the specified time range
    cursor = sensor_data_collection.find({
        "timestamp": {"$gte": start_time, "$lte": end_time}
    }).sort("timestamp", 1)  # Sort by timestamp ascending
    
    data = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])  # Convert ObjectId to string
        data.append(doc)
    
    # If there's too much data for the chart, reduce it by sampling
    if len(data) > 100:
        # Perform basic sampling by taking every Nth record
        sampling_rate = len(data) // 100
        data = data[::sampling_rate]
    
    return data

@app.get("/api/comfort-history")
def get_comfort_history(days: int = 7):
    """Get historical comfort levels for analysis"""
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    
    cursor = predictions_collection.find({
        "timestamp": {"$gte": start_time, "$lte": end_time}
    }).sort("timestamp", 1)
    
    data = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        data.append(doc)
    
    # If there's too much data, sample it
    if len(data) > 100:
        sampling_rate = len(data) // 100
        data = data[::sampling_rate]
    
    return data

@app.get("/api/device-status")
def get_device_status():
    """Get current status of all devices"""
    latest_prediction = predictions_collection.find_one(
        sort=[("timestamp", -1)]
    )
    
    if not latest_prediction:
        return {
            "ac": "OFF",
            "purifier": "OFF",
            "dehumidifier": "OFF",
            "last_updated": datetime.now()
        }
    
    return {
        "ac": latest_prediction["ac_state"],
        "purifier": latest_prediction["purifier_state"],
        "dehumidifier": latest_prediction["dehumidifier_state"],
        "last_updated": latest_prediction["timestamp"]
    }

@app.get("/api/dashboard-summary")
def get_dashboard_summary():
    """Get a summary of all data for the dashboard"""
    # Get latest sensor readings
    latest_sensor = sensor_data_collection.find_one(
        sort=[("timestamp", -1)]
    )
    
    if not latest_sensor:
        raise HTTPException(status_code=404, detail="No sensor data found")
    
    # Get latest prediction
    latest_prediction = predictions_collection.find_one(
        sort=[("timestamp", -1)]
    )
    
    # Get 24-hour averages
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=24)
    
    pipeline = [
        {"$match": {"timestamp": {"$gte": start_time, "$lte": end_time}}},
        {"$group": {
            "_id": None,
            "avg_temperature": {"$avg": "$temperature"},
            "avg_humidity": {"$avg": "$humidity"},
            "avg_air_quality": {"$avg": "$air_quality"},
        }}
    ]
    
    averages = list(sensor_data_collection.aggregate(pipeline))
    
    # Format the response
    return {
        "current": {
            "temperature": latest_sensor["temperature"],
            "humidity": latest_sensor["humidity"],
            "air_quality": latest_sensor["air_quality"],
            "timestamp": latest_sensor["timestamp"],
        },
        "prediction": latest_prediction if latest_prediction else None,
        "averages": averages[0] if averages else {
            "avg_temperature": latest_sensor["temperature"],
            "avg_humidity": latest_sensor["humidity"],
            "avg_air_quality": latest_sensor["air_quality"],
        },
        "devices": {
            "ac": latest_prediction["ac_state"] if latest_prediction else "OFF",
            "purifier": latest_prediction["purifier_state"] if latest_prediction else "OFF",
            "dehumidifier": latest_prediction["dehumidifier_state"] if latest_prediction else "OFF",
        }
    }

if __name__ == "__main__":
    import uvicorn
    # Start the API server on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)