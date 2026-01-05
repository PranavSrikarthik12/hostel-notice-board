# Hostel Assist – Notice Board System

## Problem Description

Hostel notice dissemination is a frequent requirement in university hostels. Traditional notice boards are static and require physical presence, while modern systems require real-time accessibility and centralized control.

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

##  Distributed Communication Model Used

- **Model:** Client–Server
- **Protocol:** HTTP
- **API Style:** RESTful RPC
- **State Handling:** Stateless APIs with centralized in-memory state

Each request is independent and carries all required data, making the system scalable and fault-tolerant.

---

##  In-Memory Storage Design

Notices are stored in a server-side **in-memory list**:
```text
[
  { title, message, date, expires_at }
]
```

### Why In-Memory Storage?
- Notices are **temporary and time-sensitive**
- Persistence is not mandatory for hostel notices
- Faster read/write operations
- Aligns with real-world systems such as:
  - Caches
  - Session stores
  - Live bulletin boards

 **Important:** Server restarts clear data intentionally, simulating **ephemeral distributed services**.

---

##  TTL-Based Notice Expiry (Unique Enhancement)

Each notice has an expiry timestamp (`expires_at`).

### Expiry Handling:
- Expired notices are **automatically removed**
- Cleanup occurs during read operations (lazy cleanup)
- No background jobs or schedulers required

This design simulates **time-bound data lifecycles** in real distributed caches.

---

##  API Endpoints

###  Add Notice (Admin)
```
POST /notices
```

**Request Body:**
```json
{
  "title": "Water Supply Interruption",
  "message": "No water from 10 AM to 2 PM",
  "date": "2025-03-25",
  "expires_at": "2025-03-25T14:00"
}
```

**Response:**
```json
{
  "message": "Notice added successfully"
}
```

---

###  Get Active Notices (Students)
```
GET /notices
```

**Response:**
```json
[
  {
    "title": "Water Supply Interruption",
    "message": "No water from 10 AM to 2 PM",
    "date": "2025-03-25",
    "expires_at": "2025-03-25T14:00"
  }
]
```

---

##  UI Features

### Admin UI
- Add notices with expiry time
- Client-side validation
- Visual feedback on success/failure

### Student UI
- Card-based notice display
- Highlight notices expiring within 24 hours
- Client-side search/filter
- Auto-refresh every 30 seconds (pull-based model)

---

##  Cloud Deployment

- Platform: **Render**
- Backend deployed as a cloud-hosted REST service
- Python version enforced using `runtime.txt`
- Dependencies managed via `requirements.txt`

### Deployment Characteristics
- Stateless execution
- Containerized runtime
- Cold starts clear in-memory data (by design)

---

##  Steps to Run the Application

### 1. Backend (Local)
```bash
cd backend
python app.py
```

### 2. Frontend
- Open `frontend/admin.html` in browser
- Open `frontend/student.html` in browser

(Frontend communicates with deployed Render backend.)

---

##  Limitations

- Data is not persistent across server restarts
- No authentication (kept stateless for simplicity)
- Designed for demonstration and academic use

---

##  Future Enhancements

- Role-based authentication
- Persistent storage (optional enhancement)
- WebSocket-based push notifications
- Admin notice deletion/editing

---

##  Conclusion

This project successfully demonstrates a **distributed, stateless web application** using RESTful communication and in-memory state management. By incorporating **TTL-based expiry**, **cloud deployment**, and **client-side optimizations**, the system reflects real-world distributed design principles while remaining simple, efficient, and usable.

---

## Team Contribution

Each module was designed and implemented with a focus on:
- Distributed systems concepts
- Clean architecture
- Practical usability
