# AIMA API Reference

This document provides technical details for the FastAPI REST API backend of the **Incident Management Assistant (AIMA)**. The backend powers data ingestion, historical tickets retrieval, health metrics diagnostics, and real-time dashboard analytics.

---

## Service Overview

The backend is built in [server.py](file:///c:/Users/kavad/New%20folder%20(6)/server.py) and operates by default on port `8000`.

*   **API Base URL**: `http://localhost:8000`
*   **CORS Policy**: Configured with permissive origins (`allow_origins=["*"]`) to allow seamless integrations with external dashboards or custom web portals.

---

## Endpoint Details

### 1. Root Redirect (`GET /`)
*   **Description**: Automatically redirects root visits to the client-facing Glassmorphism portal interface.
*   **Response**: `HTTP 307 Temporary Redirect` to `/static/index.html`.

---

### 2. Submit Incident (`POST /api/incidents/submit`)
*   **Description**: Ingests a new incident description, executes the complete LangGraph state machine workflow synchronously, saves the result to the CSV database, and returns the final state metadata.
*   **Request Content-Type**: `application/json`
*   **Request Schema**:
    ```json
    {
      "issue": "VPN access denied on connection attempt from home network",
      "source": "Gmail" // Optional. Defaults to "Employee Portal" if omitted
    }
    ```
*   **Response Content-Type**: `application/json`
*   **Response Model (`IncidentResponse`)**:
    ```json
    {
      "ticket_id": "IT-20260617-A1B2",
      "issue": "VPN access denied on connection attempt from home network",
      "source": "Gmail",
      "category": "IT",
      "priority": "Medium",
      "escalated": false,
      "escalation_contact": "",
      "response": "Your issue has been logged as Ticket IT-20260617-A1B2 and assigned to the IT Support Team...",
      "reasoning_trace": [
        "✓ Incident received",
        "✓ Memory retrieved",
        "✓ Category assigned",
        "✓ Priority calculated",
        "✓ Ticket generated",
        "✓ Escalation checked",
        "✓ Response generated"
      ],
      "sla_hours": 24,
      "due_date": "2026-06-18 09:15:00"
    }
    ```
*   **Errors**:
    *   `400 Bad Request`: Ingested issue text is empty.
    *   `500 Internal Server Error`: The LangGraph state machine execution failed.

---

### 3. Get Tickets List (`GET /api/tickets`)
*   **Description**: Fetches all logged incidents stored inside the local database file.
*   **Response Content-Type**: `application/json`
*   **Response**: A list of incident objects, matching the `IncidentResponse` schema structure, including additional tracking fields like `status` and `timestamp`.
*   **Data Standardizations**: Automatically converts CSV string boolean values (`"true"`, `"1"`) back to JSON boolean types, and parses empty SLAs back to `0`.

---

### 4. Fetch Analytics Data (`GET /api/analytics`)
*   **Description**: Generates real-time performance KPI statistics and exports pre-styled Plotly charts configurations for UI rendering.
*   **Response Content-Type**: `application/json`
*   **Response Object Structure**:
    ```json
    {
      "statistics": {
        "total_incidents": 8,
        "escalated_incidents": 3,
        "critical_incidents": 3,
        "avg_resolution_time_hours": 19.2,
        "resolved_incidents": 5,
        "open_incidents": 1,
        "in_progress_incidents": 2
      },
      "charts": {
        "category_chart": { /* Serialized Plotly JSON Config */ },
        "priority_chart": { /* Serialized Plotly JSON Config */ },
        "escalation_chart": { /* Serialized Plotly JSON Config */ },
        "daily_chart": { /* Serialized Plotly JSON Config */ }
      }
    }
    ```

---

### 5. Fetch Corporate Policies (`GET /api/kb`)
*   **Description**: Returns the raw content of the policy handbook loaded directly from the filesystem.
*   **Response Content-Type**: `application/json`
*   **Response**: A list of raw records containing fields: `policy_id`, `category`, `title`, and `content`.
*   **Errors**:
    *   `404 Not Found`: [policies.csv](file:///c:/Users/kavad/New%20folder%20(6)/policies.csv) is missing from the project root.

---

### 6. Health Probe (`GET /api/health`)
*   **Description**: Diagnostic probe endpoint checking service status, local data directories, and RAG configuration details.
*   **Response Content-Type**: `application/json`
*   **Response Example**:
    ```json
    {
      "status": "Healthy",
      "database": {
        "incidents_csv_present": true,
        "policies_csv_present": true,
        "chromadb_dir_present": true
      },
      "rag_engine": "Active (ChromaDB + SentenceTransformers)",
      "api_server": "Running"
    }
    ```

---

## Static Assets Server

FastAPI mounts the local `./static/` folder on the `/static` endpoint space:
```python
app.mount("/static", StaticFiles(directory="static"), name="static")
```
This is used to serve [static/index.html](file:///c:/Users/kavad/New%20folder%20(6)/static/index.html) as the primary Glassmorphism customer portal dashboard, enabling employees to submit tickets and view real-time statistics directly from their web browsers.
