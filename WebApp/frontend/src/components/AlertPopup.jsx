// src/components/AlertPopup.jsx
import React from 'react';

function AlertPopup({ comfort, onClose }) {
  return (
    <div className="fixed inset-0 flex items-center justify-center z-50 bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-lg p-6 max-w-md w-full">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold text-red-600">Environment Alert</h2>
          <button 
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 focus:outline-none"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div className={`p-4 rounded-lg mb-4 ${
          comfort.level === 'uncomfortable' ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'
        }`}>
          <p className="font-bold text-lg capitalize mb-2">{comfort.level} Environment Detected</p>
          {comfort.reasons.length > 0 && (
            <p>Issues detected: {comfort.reasons.join(', ')}</p>
          )}
        </div>
        
        <p className="text-gray-600 mb-4">
          The system is automatically adjusting your environment for optimal comfort.
        </p>
        
        <button
          onClick={onClose}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Got it
        </button>
      </div>
    </div>
  );
}

export default AlertPopup;
