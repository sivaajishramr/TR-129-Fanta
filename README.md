[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/BX0G0ttc)

# ♿ AccessAudit AI — Inclusive Public Transport Accessibility Auditor

> **Tensor'26 Hackathon** | Team FANTA (TR-129)

An AI-powered web platform that audits public transport accessibility across Tamil Nadu, identifies infrastructure gaps for persons with disabilities, and generates actionable recommendations aligned with **SDG 10 (Reduced Inequalities)** and **SDG 11 (Sustainable Cities)**.

---

## 🎯 Problem Statement

Public transport systems across India often lack critical accessibility infrastructure for persons with disabilities — missing ramps, broken tactile paths, locked accessible toilets, and absent audio announcements. There is no centralized, data-driven system to audit, visualize, and prioritize these gaps.

## 💡 Our Solution

**AccessAudit AI** combines NLP-powered grievance analysis with a weighted scoring engine to:

1. **Score every transit stop** using a weighted accessibility gap formula.
2. **Classify citizen grievances** into 6 categories using TF-IDF keyword matching
3. **Visualize gaps on an interactive map** covering all 38 districts of Tamil Nadu
4. **Generate actionable prevention suggestions** for each grievance
5. **Track 12-month improvement trends** with historical data analysis
6. **Export professional PDF audit reports** for government stakeholders

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│                  Frontend                    │
│   HTML + CSS + JavaScript + Chart.js         │
│   Leaflet.js Map + jsPDF Report Generator    │
├─────────────────────────────────────────────┤
│                Backend (Flask)               │
│   REST API  ·  Scoring Engine  ·  NLP Engine │
├─────────────────────────────────────────────┤
│                  Data Layer                  │
│   transit_stops.json  ·  grievances.json     │
│   accessibility_checklist.json               │
│   historical_trends.json                     │
└─────────────────────────────────────────────┘
```

## ✨ Key Features

### 📊 Dashboard
- Real-time summary cards showing Critical / Warning / Good stop counts
- Gap score distribution bar chart
- Priority breakdown doughnut chart
- **12-month historical accessibility improvement trend** (dual-axis line chart)

### 🗺️ Interactive Priority Map
- All 38 districts of Tamil Nadu with 100+ bus stands mapped
- Color-coded markers (🔴 Critical, 🟡 Warning, 🟢 Good)
- Search bar to find any stop instantly
- GPS "My Location" button
- Tamil Nadu state boundary overlay with city labels

### 🔍 Deep Analytics Modal
Click any map marker → **"View Deep Analytics 🔍"** to see:
- **Last Audit Date** for the specific stop
- **Categorical Grievance Breakdown** bar chart (6 categories)
- **Raw Citizen Grievances** with NLP-classified tags
- **💡 AI Prevention Suggestions** for each grievance

### 🧠 NLP Grievance Classification
Grievances are classified into 6 categories:
| Category | Color |
|----------|-------|
| Ramp & Wheelchair Access | 🔴 Red |
| Audio & Visual Signals | 🟠 Orange |
| Signage & Braille | 🟣 Purple |
| Toilet & Facilities | 🔵 Cyan |
| Staff & Assistance | 🟢 Green |
| Infrastructure & Safety | 🟡 Yellow |

### 📋 Stops Table
- Full accessibility feature matrix for every stop (✅/❌)
- Searchable and sortable
- Covers ramps, tactile paths, audio signals, wheelchair space, braille, elevators, toilets, and staff assistance

### 📄 PDF Report Export
- Professional multi-page PDF with executive summary
- Top 10 priority stops with gap scores
- Grievance cluster analysis
- 8 actionable recommendations
- SDG alignment section

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/sivaajishramr/TR-129-Fanta.git
cd TR-129-Fanta

# Install Python dependencies
pip install -r requirements.txt

# Run the server
cd backend
python app.py
```

### Access the App
Open your browser and navigate to: **http://localhost:5000**

---

## 📁 Project Structure

```
tensor-26-hackathon-fanta/
├── backend/
│   ├── app.py                     # Flask API server
│   └── services/
│       ├── scoring_engine.py      # Accessibility gap score calculator
│       └── nlp_engine.py          # TF-IDF grievance classifier
├── Frontend/
│   ├── index.html                 # Main application page
│   ├── css/
│   │   └── styles.css             # Premium white theme styles
│   └── js/
│       ├── api.js                 # API communication layer
│       ├── app.js                 # Main application controller
│       ├── charts.js              # Chart.js visualizations
│       ├── map.js                 # Leaflet.js map module
│       └── report.js              # PDF generation module
├── data/
│   ├── transit_stops.json         # 100+ stops across Tamil Nadu
│   ├── grievances.json            # Citizen grievance reports
│   ├── accessibility_checklist.json # RPWD Act standards
│   └── historical_trends.json     # 12-month trend data
├── requirements.txt
└── README.md
```

---

## 🔧 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/stops` | All stops with gap scores |
| GET | `/api/grievances` | NLP-clustered grievance analysis |
| GET | `/api/report` | Full audit report data |
| GET | `/api/checklist` | Accessibility standards checklist |
| GET | `/api/trends` | 12-month historical trend data |
| GET | `/api/stops/<id>/details` | Deep analytics for a specific stop |

---

## 📐 Scoring Algorithm

```
Gap Score = (Σ missing feature weights / max possible score) × 100

Priority Score = Gap Score × 0.5 + Normalized Grievances × 0.3 + Normalized Footfall × 0.2
```

**Silhouette Score** validates NLP clustering quality (target: > 0.5 = Good).

---

## 🎯 SDG Alignment

- **SDG 10 — Reduced Inequalities**: Ensuring equal access to public transport for persons with disabilities
- **SDG 11 — Sustainable Cities**: Making urban transport inclusive, safe, and accessible for all

---

## 👥 Team FANTA (TR-129)

Built with ❤️ for **Tensor'26 Hackathon**

---

## 📜 References

- Rights of Persons with Disabilities (RPWD) Act, 2016
- Accessible India Campaign (Sugamya Bharat Abhiyan)
- Ministry of Housing and Urban Affairs — Urban Transport Guidelines
- Bureau of Indian Standards — IS 17802:2021 (Accessibility Standards)
