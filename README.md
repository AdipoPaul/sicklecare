# 🩸 SickleCare: AI-Powered WhatsApp Bot for Sickle Cell Support

SickleCare is an **AI-powered WhatsApp chatbot** designed to help patients, caregivers, and donors manage **Sickle Cell Disease (SCD)**.  
It provides **health information**, **crisis guidance**, and **local resource navigation**, with **personalized user interactions** powered by **DeepSeek AI** and deployed using **Django + Twilio WhatsApp API**.

---

## 🌍 Project Overview

SickleCare bridges the gap between **patients** and **health resources** by offering:
- 💬 24/7 WhatsApp-based communication  
- 🧠 AI-driven responses to medical and lifestyle questions  
- 🚨 Crisis detection and emergency guidance  
- 🏥 Resource discovery (coming soon)

This solution is especially valuable in regions with limited access to medical information or digital health platforms.

---

## ⚙️ Tech Stack

| Component | Technology Used |
|------------|----------------|
| **Backend Framework** | Django (Python) |
| **Messaging API** | Twilio WhatsApp Sandbox |
| **AI Engine** | DeepSeek Chat API (with OpenAI fallback option) |
| **Database** | SQLite (default) / PostgreSQL (optional) |
| **Hosting (optional)** | Render / Railway / Google Cloud |
| **Environment** | Python 3.10+, Django 5.x |

---

## 🧩 Core Features

| Phase | Description |
|--------|--------------|
| **Phase 1** | Twilio and Django setup, basic webhook configuration |
| **Phase 2** | User registration flow: Name + Role (Patient/Caregiver/Donor) |
| **Phase 3** | AI integration for educational responses and crisis detection |
| **Future Phases** | Resource mapping, health tracking, and multi-language support |

---


---

## 🧠 Core Features

- **AI Chatbot Integration** — Uses OpenAI API to generate natural and empathetic responses.  
- **WhatsApp Connectivity** — Connects through Twilio WhatsApp Sandbox or Business API.  
- **Health Education Support** — Provides verified Sickle Cell information from WHO and CDC references.  
- **Crisis Support Flow** — Guides users through self-care, hospital contacts, and symptom monitoring.  
- **User Session Management** — Tracks user conversations via Django models for continuity.  
- **Secure & Scalable** — Protected by Django middleware and environment-based configuration.

---

## ⚙️ Technology Stack

| Component          | Technology Used              |
|--------------------|-----------------------------|
| Backend Framework  | Django (Python)             |
| Messaging API      | Twilio WhatsApp API         |
| AI Engine          | OpenAI GPT API              |
| Database           | SQLite (Default) / PostgreSQL|
| Deployment Target  | Google Cloud / Azure / Localhost |
| Environment Mgmt   | `python-dotenv`             |

---

## 🧩 Setup Instructions

### 1️⃣ Prerequisites

Ensure you have installed:
- **Python 3.9+**
- **Pip & Virtualenv**
- **Django 5+**
- **Twilio Account**
- **OpenAI API Key**

### 2️⃣ Clone the Repository

```bash
git clone https://github.com/AdipoPaul/sicklecare.git
cd sicklecare


