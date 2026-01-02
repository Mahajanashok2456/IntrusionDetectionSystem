import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import './Landing.css';

const Landing = () => {
    useEffect(() => {
        const matrixBackground = document.querySelector('.matrix-background');
        if (!matrixBackground) return;

        const characters = '0123456789ABCDEF'; // Hexadecimal characters for a hacker-like feel
        const generateRandomChar = () => characters[Math.floor(Math.random() * characters.length)];

        const createMatrixEffect = () => {
            const numberOfSpans = 100; // Adjust as needed for density
            matrixBackground.innerHTML = ''; // Clear previous spans

            for (let i = 0; i < numberOfSpans; i++) {
                const span = document.createElement('span');
                span.textContent = generateRandomChar();
                span.style.left = `${Math.random() * 100}vw`;
                span.style.animationDuration = `${Math.random() * 3 + 2}s`; // 2-5 seconds
                span.style.animationDelay = `${Math.random() * 5}s`; // Staggered animation
                matrixBackground.appendChild(span);
            }
        };

        createMatrixEffect();

        // Re-generate on window resize to adjust for new dimensions
        window.addEventListener('resize', createMatrixEffect);

        return () => {
            window.removeEventListener('resize', createMatrixEffect);
        };
    }, []);

    return (
        <div className="landing-container">
            <div className="matrix-background"></div> {/* This will be our matrix background */}
            <header className="landing-header">
                <h1>Intrusion Detection System</h1>
                <p>Detect and analyze network intrusions with advanced machine learning.</p>
            </header>
            <main className="landing-main">
                <section className="features">
                    <div className="feature-item">
                        <h2>Real-time Monitoring</h2>
                        <p>Monitor network traffic for suspicious activities.</p>
                    </div>
                    <div className="feature-item">
                        <h2>Threat Analysis</h2>
                        <p>Analyze detected threats and generate comprehensive reports.</p>
                    </div>
                    <div className="feature-item">
                        <h2>Customizable Rules</h2>
                        <p>Define your own rules to enhance detection capabilities.</p>
                    </div>
                </section>
                <section className="call-to-action">
                    <Link to="/login" className="enter-app-button">
                        Enter Application
                    </Link>
                </section>
            </main>
            <footer className="landing-footer">
                <p>&copy; 2023 Intrusion Detection System. All rights reserved.</p>
            </footer>
        </div>
    );
};

export default Landing;