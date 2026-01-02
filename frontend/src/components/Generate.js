import React, { useState, useEffect } from "react";
import axios from "axios";
import { useAuth } from "../context/AuthContext";
import "./Generate.css";
import API_BASE_URL from "../config";

const Generate = () => {
  const [numRows, setNumRows] = useState(100);
  const [generatedData, setGeneratedData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [trainingLoading, setTrainingLoading] = useState(false);
  const [trainingResult, setTrainingResult] = useState(null);
  const [trainingError, setTrainingError] = useState(null);
  const [numSyntheticSamples, setNumSyntheticSamples] = useState(1000);
  const [useSyntheticData, setUseSyntheticData] = useState(true);
  const { token } = useAuth();

  // Falling numbers animation effect
  useEffect(() => {
    const createFallingNumber = () => {
      const number = document.createElement('div');
      number.className = 'falling-number';
      number.textContent = Math.floor(Math.random() * 10);
      number.style.left = Math.random() * 100 + '%';
      number.style.animationDuration = (Math.random() * 5 + 3) + 's';
      number.style.opacity = Math.random() * 0.5 + 0.3;
      
      const container = document.querySelector('.generate-container');
      if (container) {
        container.appendChild(number);
        
        // Remove the number after animation completes
        setTimeout(() => {
          if (number.parentNode) {
            number.parentNode.removeChild(number);
          }
        }, 8000);
      }
    };

    const interval = setInterval(createFallingNumber, 200);

    return () => {
      clearInterval(interval);
    };
  }, []);

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    setGeneratedData(null);

    try {
      const response = await axios.post(
        `${API_BASE_URL}/generate/`,
        { num_samples: numRows },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      setGeneratedData(response.data);
    } catch (err) {
      console.error("Generation error:", err);
      
      if (err.response) {
        // Server responded with an error status
        switch (err.response.status) {
          case 503:
            setError("CTGAN model is not available. The synthetic data generation feature requires trained CTGAN models. Please contact your administrator to set up the CTGAN models.");
            break;
          case 401:
            setError("Authentication failed. Please log in again.");
            break;
          case 400:
            setError("Invalid request. Please check your input parameters.");
            break;
          case 500:
            setError("Server error occurred. Please try again later.");
            break;
          default:
            setError(`Error generating synthetic data: ${err.response.data?.detail || err.response.statusText}`);
        }
      } else if (err.request) {
        // Network error
        setError("Network error. Please check your connection and try again.");
      } else {
        // Other error
        setError("An unexpected error occurred. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleTrainModel = async () => {
    setTrainingLoading(true);
    setTrainingError(null);
    setTrainingResult(null);

    try {
      const response = await axios.post(
        `${API_BASE_URL}/train/`,
        { 
          num_synthetic_samples: numSyntheticSamples,
          use_synthetic_data: useSyntheticData,
          retrain_ctgan: false
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      setTrainingResult(response.data);
    } catch (err) {
      console.error("Training error:", err);
      
      if (err.response) {
        switch (err.response.status) {
          case 401:
            setTrainingError("Authentication failed. Please log in again.");
            break;
          case 400:
            setTrainingError("Invalid training parameters. Please check your input.");
            break;
          case 500:
            setTrainingError(`Training failed: ${err.response.data?.detail || "Server error occurred"}`);
            break;
          default:
            setTrainingError(`Error training models: ${err.response.data?.detail || err.response.statusText}`);
        }
      } else if (err.request) {
        setTrainingError("Network error. Please check your connection and try again.");
      } else {
        setTrainingError("An unexpected error occurred during training. Please try again.");
      }
    } finally {
      setTrainingLoading(false);
    }
  };

  return (
    <div className="generate-container">
      <h1 className="generate-title">Generate Synthetic Data</h1>
      <div className="input-section">
        <label htmlFor="numRows" className="label">Number of Rows:</label>
        <input
          type="number"
          id="numRows"
          value={numRows}
          onChange={(e) => setNumRows(e.target.value)}
          min="1"
          className="input-field"
        />
        <button onClick={handleGenerate} disabled={loading} className="generate-button">
          {loading ? "Generating..." : "Generate Data"}
        </button>
      </div>

      {error && <p className="error-message">{error}</p>}

      {generatedData && (
        <div className="generated-data-results">
          <h2 className="results-title">Generated Data:</h2>
          <pre className="data-output">
            {JSON.stringify(generatedData, null, 2)}
          </pre>
        </div>
      )}

      {/* Training Section */}
      <div className="training-section">
        <h2 className="section-title">Train IDS Models</h2>
        <div className="training-controls">
          <div className="control-group">
            <label htmlFor="useSyntheticData" className="checkbox-label">
              <input
                type="checkbox"
                id="useSyntheticData"
                checked={useSyntheticData}
                onChange={(e) => setUseSyntheticData(e.target.checked)}
                className="checkbox-input"
              />
              Use Synthetic Data for Training
            </label>
          </div>
          
          {useSyntheticData && (
            <div className="control-group">
              <label htmlFor="numSyntheticSamples" className="label">
                Number of Synthetic Samples:
              </label>
              <input
                type="number"
                id="numSyntheticSamples"
                value={numSyntheticSamples}
                onChange={(e) => setNumSyntheticSamples(e.target.value)}
                min="100"
                max="10000"
                className="input-field"
              />
            </div>
          )}
          
          <button 
            onClick={handleTrainModel} 
            disabled={trainingLoading} 
            className="train-button"
          >
            {trainingLoading ? "Training Models..." : "Train IDS Models"}
          </button>
        </div>

        {trainingError && <p className="error-message">{trainingError}</p>}

        {trainingResult && (
          <div className="training-results">
            <h3 className="results-title">Training Results:</h3>
            <div className="training-details">
              <p><strong>Status:</strong> {trainingResult.status}</p>
              <p><strong>Message:</strong> {trainingResult.message}</p>
              {trainingResult.details && (
                <div className="training-stats">
                  <h4>Training Statistics:</h4>
                  <ul>
                    <li>Original Samples: {trainingResult.details.original_samples}</li>
                    <li>Synthetic Samples: {trainingResult.details.synthetic_samples_used}</li>
                    <li>Total Training Samples: {trainingResult.details.total_training_samples}</li>
                    <li>Models Saved To: {trainingResult.details.models_saved_to}</li>
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Logout Button */}
      {/* <button className="logout-button" onClick={() => logout({ returnTo: window.location.origin })}>
        Logout
      </button> */}
    </div>
  );
};

export default Generate;