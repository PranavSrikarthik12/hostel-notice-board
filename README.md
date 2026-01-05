# Hostel Assist – Notice Board System

## Problem Description

Hostel notice dissemination is a frequent requirement in university hostels.  
Traditional notice boards are static and require physical presence, while modern systems require real-time accessibility and centralized control.

This project implements a **distributed Hostel Notice Board system** where:
- Admins can publish hostel notices
- Students can view active notices via a web interface
- Notices are time-bound and automatically expire

The system is designed as a **stateless distributed web application** using REST APIs and **in-memory storage**, aligning with real-world distributed service principles.

---

## Objectives

- To demonstrate **distributed client–server communication**
- To implement **stateless REST APIs**
- To manage application state using **ephemeral in-memory storage**
- To deploy the service on a **cloud platform (Render)**
- To build a **usable UI** for both admin and students

---

## System Architecture

The system follows a **Client–Server Architecture**:

- **Backend Server**
  - Exposes REST APIs
  - Maintains notices in memory
  - Handles expiry logic (TTL)

- **Admin Client (Web UI)**
  - Sends POST requests to add notices

- **Student Client (Web UI)**
  - Sends GET requests to fetch active notices

### Communication Model
- REST over HTTP
- JSON data exchange
- Stateless request–response model (RPC-style)

---

## Distributed Communication Model Used

- **Model:** Client–Server
- **Protocol:** HTTP
- **API Style:** RESTful RPC
- **State Handling:** Stateless APIs with centralized in-memory state

Each request is independent and carries all required data, making the system scalable and fault-tolerant.

---

## 🧠 In-Memory Storage Design

Notices are stored in a server-side **in-memory list**:

```text
[
  {
    title,
    message,
    date,
    expires_at
  }
]
