import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import axios from "axios";
import "./Login.css";
import API_BASE_URL from "../config";

function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const { login } = useAuth(); // Use the login function from AuthContext

  // Falling numbers background effect
  useEffect(() => {
    const createFallingNumber = () => {
      const number = document.createElement('div');
      number.className = 'falling-number';
      number.textContent = Math.floor(Math.random() * 10);
      number.style.left = Math.random() * 100 + '%';
      number.style.animationDuration = (Math.random() * 3 + 2) + 's';
      number.style.opacity = Math.random() * 0.8 + 0.2;
      
      const container = document.querySelector('.login-container');
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
    
    // Cleanup on component unmount
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

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    console.log("DEBUG: Using API URL:", API_BASE_URL); // Debugging line

    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const cleanApiUrl = API_BASE_URL.replace(/\/$/, "");

    try {
      const response = await axios.post(`${cleanApiUrl}/auth/token`, formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });
      login(response.data.access_token);
      navigate('/home');
    } catch (err) {
      console.error('Login error:', err);
      if (err.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        setError(`Login failed: ${err.response.status} ${err.response.data?.detail || err.response.statusText}`);
      } else if (err.request) {
        // The request was made but no response was received
        setError('Network Error: No response from server. Check your connection or API URL.');
      } else {
        // Something happened in setting up the request that triggered an Error
        setError(`Error: ${err.message}`);
      }
    }
  };

  return (
    <div className="login-container">
      <h2>Login</h2>
      <form onSubmit={handleSubmit}>
        {error && <p className="error-message">{error}</p>}
        <div className="form-group">
          <label htmlFor="username">Username:</label>
          <input
            type="text"
            id="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="password">Password:</label>
          <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        <button type="submit">Login</button>
      </form>
    </div>
  );
}

export default Login;