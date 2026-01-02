import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import { useAuth } from "../context/AuthContext";
import "./Predict.css";
import API_BASE_URL from "../config";

const Predict = () => {
  const [file, setFile] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef(null);
  const { token } = useAuth();

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
    setPrediction(null);
    setError(null);
  };

  const handleButtonClick = () => {
    fileInputRef.current.click();
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Please select a file first.");
      return;
    }

    setLoading(true);
    setError(null);
    setPrediction(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const cleanApiUrl = API_BASE_URL.replace(/\/$/, "");
      // Determine endpoint based on file type
      const isCSV = file.name.toLowerCase().endsWith('.csv');
      const endpoint = isCSV ? 
        `${cleanApiUrl}/predict/` : 
        `${cleanApiUrl}/predict/pcap`;

      const response = await axios.post(
        endpoint,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
            Authorization: `Bearer ${token}`,
          },
        }
      );
      setPrediction(response.data);
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || "Error uploading file or getting prediction.";
      setError(errorMessage);
      console.error("Prediction error:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="predict-container">
      <h1 className="predict-title">&gt; INTRUSION_DETECTION_SYSTEM</h1>
      <div className="upload-section">
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          className="file-input"
          accept=".pcap,.pcapng,.csv"
        />
        <button onClick={handleButtonClick} className="select-file-button">
          {file ? file.name : "Select PCAP or CSV File"}
        </button>
        <button onClick={handleUpload} disabled={loading} className="upload-button">
          {loading ? "Uploading..." : "Upload and Predict"}
        </button>
      </div>

      {error && <p className="error-message">{error}</p>}

      {prediction && (
        <div className="prediction-results">
          <h2 className="results-title">Prediction Results:</h2>
          {prediction.filename && (prediction.total_connections || prediction.total_rows) ? (
            // Structured file results (PCAP or CSV)
            <div className="pcap-results">
              <div className="summary-section">
                <h3>Summary for {prediction.filename}</h3>
                <p><strong>Total {prediction.total_connections ? 'Connections' : 'Rows'}:</strong> {prediction.total_connections || prediction.total_rows}</p>
                <p><strong>Normal Traffic:</strong> {prediction.summary.normal}</p>
                <p><strong>Potential Attacks:</strong> {prediction.summary.attacks}</p>
              </div>
              
              <div className="connections-section">
                <h3>{prediction.total_connections ? 'Connection' : 'Row'} Details:</h3>
                <div className="connections-table">
                  {prediction.predictions.slice(0, 10).map((item) => (
                    <div key={item.connection_id || item.row_id} className={`connection-row ${item.prediction.toLowerCase().includes('normal') ? 'normal' : 'attack'}`}>
                      <div><strong>{prediction.total_connections ? 'Connection' : 'Row'} {item.connection_id || item.row_id}:</strong></div>
                      {item.service && <div>Service: {item.service}</div>}
                      {item.protocol && <div>Protocol: {item.protocol}</div>}
                      <div>Prediction: <span className="prediction-label">{item.prediction}</span></div>
                      {item.duration && <div>Duration: {item.duration.toFixed(2)}s</div>}
                    </div>
                  ))}
                  {prediction.predictions.length > 10 && (
                    <div className="more-results">
                      ... and {prediction.predictions.length - 10} more {prediction.total_connections ? 'connections' : 'rows'}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ) : (
            // Fallback for any other format
            <pre className="prediction-output">
              {JSON.stringify(prediction, null, 2)}
            </pre>
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

export default Predict;