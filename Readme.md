# 🛡️ Intelligent Intrusion Detection System

## 🌐 Project Overview

In the ever-evolving landscape of cybersecurity, our Intrusion Detection System (IDS) stands as a sentinel, leveraging cutting-edge machine learning to protect digital infrastructures from sophisticated network threats.

## ✨ Key Innovations

### 🔍 Advanced Threat Detection
- **Intelligent Neural Architecture**
  - Deep learning model trained on NSL-KDD dataset
  - Stacked encoders for nuanced feature extraction
  - Gated convolution for adaptive threat weighting
  - Precision-driven multi-class attack classification

### 🧬 Synthetic Data Mastery
- **CTGAN: Synthetic Data Generation**
  - Generates high-fidelity network security datasets
  - Addresses data scarcity and class imbalance
  - Enhances model generalization and resilience

### 🚀 Real-Time Network Vigilance
- **Live Network Monitoring**
  - Seamless Wireshark integration
  - Millisecond-level threat detection
  - Comprehensive network traffic analysis

## 🏗️ System Architecture

### 💻 User Interface
- **React.js Powered Frontend**
  - Responsive, intuitive design
  - Real-time threat visualization
  - Interactive security dashboards

### 🖥️ Backend Infrastructure
- **FastAPI Microservices**
  - High-performance API framework
  - Scalable architecture
  - Robust error handling

## 🛠️ Technology Constellation

| Domain | Technologies |
|--------|--------------|
| **Frontend** | React.js |
| **Backend** | Python 3.8+ • FastAPI |
| **ML Framework** | PyTorch • Scikit-learn |
| **Data Processing** | Pandas • NumPy |
| **Network Tools** | Wireshark |

## 🚀 Quick Start

### 🔧 Prerequisites
- Python 3.8+
- Node.js 14.x
- npm 6.x
- Git

### 🔨 Installation

```bash
# Clone the guardian
git clone https://github.com/vishruth2005/IntrusionDetectionSystem.git
cd ids

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend ignition
cd ../frontend
npm install
npm start
```

## 🌳 Project Topology
```
ids/
├── 🔒 backend/
│   ├── 🔧 api/
│   └── 📋 config.py
├── 🖥️ frontend/
│   ├── 💻 src/
│   └── 📦 package.json
└── 🧠 src/
    ├── 📊 CTGAN/
    └── 🔮 IDS/
```

## 🙏 Acknowledgments
- NSL-KDD Dataset Pioneers
- Open-Source Community Innovators