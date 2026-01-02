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

    try {
      const response = await axios.post(`${API_BASE_URL}/auth/token`, new URLSearchParams({
        username: username,
        password: password,
      }), {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });
      login(response.data.access_token);
      navigate('/home');
    } catch (err) {
      setError('Invalid credentials or server error.');
      console.error('Login error:', err);
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