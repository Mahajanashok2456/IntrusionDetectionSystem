import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import './Home.css';
import { useAuth } from '../context/AuthContext';

function Home() {
  const { logout } = useAuth();

  const handleLogout = () => {
    logout();
  };

  // Falling numbers background effect
  useEffect(() => {
    const createFallingNumber = () => {
      const number = document.createElement('div');
      number.className = 'falling-number';
      number.textContent = Math.floor(Math.random() * 10);
      number.style.left = Math.random() * 100 + '%';
      number.style.animationDuration = (Math.random() * 3 + 2) + 's';
      number.style.opacity = Math.random() * 0.8 + 0.2;
      
      const container = document.querySelector('.home-container');
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

  return (
    <div className="home-container">
      <button onClick={handleLogout} className="logout-button">Logout</button>
      <header className="home-header">
        <h1>Welcome to the Intrusion Detection System</h1>
      </header>
      <nav className="home-nav">
        <ul>
          <li><Link to="/predict">Predict</Link></li>
          <li><Link to="/generate">Generate</Link></li>
          <li><Link to="/capture">Capture</Link></li>
        </ul>
      </nav>
      <main className="home-main">
        <p>This system allows you to predict network intrusions, generate synthetic data, and capture network traffic.</p>
      </main>
    </div>
  );
}

export default Home;