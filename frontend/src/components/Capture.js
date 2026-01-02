import React, { useState, useEffect } from "react";
import axios from "axios";
import { useAuth } from "../context/AuthContext";
import "./Capture.css";
import API_BASE_URL from "../config";

const Capture = () => {
  const [captureDuration, setCaptureDuration] = useState(10);
  const [captureStatus, setCaptureStatus] = useState("idle"); // idle, capturing, finished, error
  const [capturedData, setCapturedData] = useState(null);
  const [error, setError] = useState(null);
  const { token } = useAuth();

  // Falling numbers background effect
  useEffect(() => {
    const createFallingNumber = () => {
      const number = document.createElement('div');
      number.className = 'falling-number';
      number.textContent = Math.floor(Math.random() * 2); // Random 0 or 1
      number.style.left = Math.random() * 100 + '%';
      number.style.animationDuration = (Math.random() * 3 + 2) + 's'; // 2-5 seconds
      number.style.opacity = Math.random() * 0.5 + 0.3; // 0.3-0.8 opacity
      
      const container = document.querySelector('.capture-container');
      if (container) {
        container.appendChild(number);
        
        // Remove the number after animation completes
        setTimeout(() => {
          if (number.parentNode) {
            number.parentNode.removeChild(number);
          }
        }, 5000);
      }
    };

    // Create falling numbers at intervals
    const interval = setInterval(createFallingNumber, 200);

    // Cleanup function
    return () => {
      clearInterval(interval);
      // Remove any remaining falling numbers
      const fallingNumbers = document.querySelectorAll('.falling-number');
      fallingNumbers.forEach(number => {
        if (number.parentNode) {
          number.parentNode.removeChild(number);
        }
      });
    };
  }, []);

  const handleStartCapture = async () => {
    setCaptureStatus("capturing");
    setError(null);
    setCapturedData(null);

    try {
      const response = await axios.post(
        `${API_BASE_URL}/capture/`,
        { duration: captureDuration },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
          responseType: 'blob', // Important: Handle response as blob for file download
        }
      );
      
      // Create blob URL and trigger download
      const blob = new Blob([response.data], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'Captured_data.csv';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      setCapturedData("CSV file downloaded successfully!");
      setCaptureStatus("finished");
    } catch (err) {
      setError("Error starting capture.");
      console.error("Capture error:", err);
      setCaptureStatus("error");
    }
  };

  return (
    <div className="capture-container">
      <h1 className="capture-title">Network Traffic Capture</h1>
      <div className="input-section">
        <label htmlFor="duration" className="label">Capture Duration (seconds):</label>
        <input
          type="number"
          id="duration"
          value={captureDuration}
          onChange={(e) => setCaptureDuration(e.target.value)}
          min="1"
          className="input-field"
        />
        <button
          onClick={handleStartCapture}
          disabled={captureStatus === "capturing"}
          className="capture-button"
        >
          {captureStatus === "capturing" && !capturedData?.summary ? "Capturing..." : "Download PCAP (CSV)"}
        </button>

        <button
          onClick={async () => {
             setCaptureStatus("capturing");
             setError(null);
             setCapturedData(null);
             try {
                const response = await axios.post(
                   `${API_BASE_URL}/capture/analyze`, 
                   { duration: captureDuration },
                  { headers: { Authorization: `Bearer ${token}` } }
                );
                setCapturedData(response.data);
                setCaptureStatus("finished");
             } catch(err) {
                 setError(err.response?.data?.detail || "Analysis failed. Ensure Wireshark is installed.");
                 setCaptureStatus("error");
             }
          }}
          disabled={captureStatus === "capturing"}
          className="capture-button analyze-button"
          style={{marginLeft: "10px", backgroundColor: "#e74c3c"}}
        >
          {captureStatus === "capturing" && !capturedData?.filename ? "Analyzing..." : "Real-Time Analyze"}
        </button>
      </div>

      {error && <p className="error-message">{error}</p>}

      {capturedData && (
        <div className="captured-data-results">
          <h2 className="results-title">Result:</h2>
          
          {typeof capturedData === 'string' ? (
              <p className="success-message">{capturedData}</p>
          ) : (
              <div className="analysis-summary">
                  <p><strong>Total Connections:</strong> {capturedData.total_connections}</p>
                  <p style={{color: '#2ecc71'}}><strong>Normal Traffic:</strong> {capturedData.summary.normal}</p>
                  <p style={{color: '#e74c3c'}}>
                      <strong>Attacks Detected:</strong> {capturedData.summary.attacks}
                      {capturedData.summary.attacks > 0 && " ⚠️ WARNING!"}
                  </p>
                  {capturedData.summary.attacks > 0 && (
                      <div className="attack-list">
                          <h3>Attack Details:</h3>
                          <ul>
                              {capturedData.details
                                  .filter(d => !d.prediction.toLowerCase().includes('normal'))
                                  .map((d, i) => (
                                      <li key={i}>
                                          {d.protocol} traffic detected as <strong>{d.prediction}</strong>
                                      </li>
                                  ))
                              }
                          </ul>
                      </div>
                  )}
              </div>
          )}
        </div>
      )}

      {/* Logout Button */}
      {/* <button className="logout-button" onClick={() => logout({ returnTo: window.location.origin })}>
        Logout
      </button> */}
    </div>
  );
};

export default Capture;