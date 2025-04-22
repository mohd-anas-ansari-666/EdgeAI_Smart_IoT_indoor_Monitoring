// src/services/api.js
const API_BASE_URL = 'http://localhost:8000/api';

export const fetchLatestData = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/latest-data`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching latest data:', error);
    throw error;
  }
};

export const fetchHistoricalData = async (hours = 24) => {
  try {
    const response = await fetch(`${API_BASE_URL}/historical-data?hours=${hours}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching historical data:', error);
    throw error;
  }
};

export const fetchComfortHistory = async (days = 7) => {
  try {
    const response = await fetch(`${API_BASE_URL}/comfort-history?days=${days}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching comfort history:', error);
    throw error;
  }
};

export const fetchDeviceStatus = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/device-status`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching device status:', error);
    throw error;
  }
};

export const fetchDashboardSummary = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/dashboard-summary`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching dashboard summary:', error);
    throw error;
  }
};