// src/App.jsx
import React, { useState, useEffect } from 'react';
import DashboardWidget from './components/DashboardWidget';
import SensorChart from './components/SensorChart';
import DeviceControl from './components/DeviceControl';
import AlertPopup from './components/AlertPopup';
import { fetchLatestData, fetchHistoricalData } from './services/api';

function App() {
  const [sensorData, setSensorData] = useState({
    temperature: 0,
    humidity: 0,
    airQuality: 0,
    timestamp: new Date()
  });
  
  const [predictions, setPredictions] = useState({
    temperature: 0,
    humidity: 0,
    airQuality: 0
  });
  
  const [comfort, setComfort] = useState({
    level: 'comfortable',
    reasons: []
  });
  
  const [devices, setDevices] = useState({
    ac: 'OFF',
    purifier: 'OFF',
    dehumidifier: 'OFF'
  });
  
  const [showAlert, setShowAlert] = useState(false);
  const [historicalData, setHistoricalData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Fetch latest data at regular intervals
  // useEffect(() => {
  //   const fetchData = async () => {
  //     try {
  //       setLoading(true);
  //       const data = await fetchLatestData();
        
  //       setSensorData({
  //         temperature: data.temperature,
  //         humidity: data.humidity,
  //         airQuality: data.air_quality,
  //         timestamp: new Date(data.timestamp)
  //       });
        
  //       setPredictions({
  //         temperature: data.temperature_pred,
  //         humidity: data.humidity_pred,
  //         airQuality: data.air_quality_pred
  //       });
        
  //       setComfort({
  //         level: data.comfort_level,
  //         reasons: data.comfort_reasons
  //       });
        
  //       setDevices({
  //         ac: data.ac_state,
  //         purifier: data.purifier_state,
  //         dehumidifier: data.dehumidifier_state
  //       });
        
  //       // Show alert if comfort level is not comfortable
  //       if (data.comfort_level !== 'comfortable' && !showAlert) {
  //         setShowAlert(true);
  //         // Auto-hide after 10 seconds
  //         setTimeout(() => setShowAlert(false), 10000);
  //       }
        
  //       setLoading(false);
  //     } catch (err) {
  //       setError('Failed to fetch latest data. Please check your connection.');
  //       setLoading(false);
  //       console.error('Error fetching latest data:', err);
  //     }
  //   };
    
  //   // Fetch historical data for charts
  //   const fetchHistory = async () => {
  //     try {
  //       const data = await fetchHistoricalData();
  //       setHistoricalData(data);
  //     } catch (err) {
  //       console.error('Error fetching historical data:', err);
  //     }
  //   };
    
  //   // Initial fetch
  //   fetchData();
  //   fetchHistory();
    
  //   // Set up polling
  //   const latestDataInterval = setInterval(fetchData, 10000); // every 10 seconds
  //   const historicalDataInterval = setInterval(fetchHistory, 60000); // every minute
    
  //   return () => {
  //     clearInterval(latestDataInterval);
  //     clearInterval(historicalDataInterval);
  //   };
  // }, [showAlert]);
  useEffect(() => {
    let lastComfortLevel = comfort.level; // track in outer scope
  
    const fetchData = async () => {
      try {
        setLoading(true);
        const data = await fetchLatestData();
  
        setSensorData({
          temperature: data.temperature,
          humidity: data.humidity,
          airQuality: data.air_quality,
          timestamp: new Date(data.timestamp)
        });
  
        setPredictions({
          temperature: data.temperature_pred,
          humidity: data.humidity_pred,
          airQuality: data.air_quality_pred
        });
  
        setDevices({
          ac: data.ac_state,
          purifier: data.purifier_state,
          dehumidifier: data.dehumidifier_state
        });
  
        const newComfort = {
          level: data.comfort_level,
          reasons: data.comfort_reasons
        };
  
        setComfort(newComfort);
  
        // ✅ Only show alert when it changes from comfortable → uncomfortable
        if (
          lastComfortLevel === 'comfortable' &&
          newComfort.level !== 'comfortable'
        ) {
          setShowAlert(true);
          setTimeout(() => setShowAlert(false), 10000);
        }
  
        lastComfortLevel = newComfort.level; // update tracker
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch latest data. Please check your connection.');
        setLoading(false);
        console.error('Error fetching latest data:', err);
      }
    };
  
    // Fetch history
    const fetchHistory = async () => {
      try {
        const data = await fetchHistoricalData();
        setHistoricalData(data);
      } catch (err) {
        console.error('Error fetching historical data:', err);
      }
    };
  
    fetchData();
    fetchHistory();
  
    const latestDataInterval = setInterval(fetchData, 10000);
    const historicalDataInterval = setInterval(fetchHistory, 60000);
  
    return () => {
      clearInterval(latestDataInterval);
      clearInterval(historicalDataInterval);
    };
  }, []);
  
  
  if (loading && historicalData.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-blue-500 border-t-transparent mb-4"></div>
          <p className="text-gray-600">Loading data...</p>
        </div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-red-600 text-xl font-bold mb-4">Error</h2>
          <p className="text-gray-700 mb-4">{error}</p>
          <button 
            onClick={() => window.location.reload()}
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-blue-600 text-white p-4 shadow-md">
        <h1 className="text-2xl font-bold">Indoor Environment Monitor</h1>
      </header>
      
      <main className="container mx-auto p-4">
        {/* Current readings */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <DashboardWidget 
            title="Temperature" 
            value={`${sensorData.temperature.toFixed(1)}°C`} 
            icon="temperature"
            prediction={`${predictions.temperature.toFixed(1)}°C`} 
          />
          <DashboardWidget 
            title="Humidity" 
            value={`${sensorData.humidity.toFixed(1)}%`} 
            icon="humidity"
            prediction={`${predictions.humidity.toFixed(1)}%`} 
          />
          <DashboardWidget 
            title="Air Quality" 
            value={`${sensorData.airQuality.toFixed(0)} PPM`} 
            icon="air"
            prediction={`${predictions.airQuality.toFixed(0)} PPM`} 
          />
        </div>
        
        {/* Comfort status */}
        <div className="bg-white rounded-lg shadow-md p-4 mb-8">
          <h2 className="text-xl font-semibold mb-2">Comfort Status</h2>
          <div className={`p-4 rounded-lg ${
            comfort.level === 'comfortable' ? 'bg-green-100 text-green-800' :
            comfort.level === 'uncomfortable' ? 'bg-yellow-100 text-yellow-800' :
            'bg-red-100 text-red-800'
          }`}>
            <p className="font-bold text-lg capitalize">{comfort.level}</p>
            {comfort.reasons.length > 0 && (
              <p>Reasons: {comfort.reasons.join(', ')}</p>
            )}
          </div>
        </div>
        
        {/* Charts */}
        <div className="bg-white rounded-lg shadow-md p-4 mb-8">
          <h2 className="text-xl font-semibold mb-4">Historical Data</h2>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <SensorChart 
              data={historicalData} 
              dataKey="temperature" 
              label="Temperature (°C)" 
              color="#f87171" 
            />
            <SensorChart 
              data={historicalData} 
              dataKey="humidity" 
              label="Humidity (%)" 
              color="#60a5fa" 
            />
            <SensorChart 
              data={historicalData} 
              dataKey="air_quality" 
              label="Air Quality (PPM)" 
              color="#4ade80" 
            />
          </div>
        </div>
        
        {/* Device controls */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <DeviceControl 
            name="AC" 
            status={devices.ac} 
            icon="ac" 
          />
          <DeviceControl 
            name="Air Purifier" 
            status={devices.purifier} 
            icon="purifier" 
          />
          <DeviceControl 
            name="Dehumidifier" 
            status={devices.dehumidifier} 
            icon="dehumidifier" 
          />
        </div>
      </main>
      
      {/* Alert popup */}
      {showAlert && (
        <AlertPopup 
          comfort={comfort} 
          onClose={() => setShowAlert(false)} 
        />
      )}
    </div>
  );
}

export default App;