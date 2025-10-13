# FastAPI WordPress Auth & License Middleware 🚀

A robust and secure middleware server built with FastAPI that acts as a bridge between a client application and a WordPress backend. It handles user authentication, license validation against WooCommerce API Manager (WC-AM), and persistent session management.

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi)
![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker)

---

## ✨ Key Features

- **Secure WordPress Authentication**: Authenticates users against a WordPress database, with full support for modern `bcrypt` (`$wp$`) password hashes.
- **JWT Token Management**: Interfaces with a WordPress JWT plugin to generate and manage authentication tokens.
- **WooCommerce License API Integration**: Manages the complete license lifecycle (`activate`, `deactivate`, `status`) by communicating with the WooCommerce API Manager (WC-AM).
- **Persistent Session Management**: Uses a dedicated PostgreSQL database to store and track active client sessions, ensuring stateful tracking across server restarts.
- **Automatic Session Cleanup**: A background `asyncio` task runs periodically to find and deactivate expired sessions, keeping the system clean.
- **Centralized & Configurable Logging**: All server and application logs are centralized, configurable, and can be piped to both the console and a log file (`app.log`).
- **Container-Ready**: Comes with a `dockerfile` for easy, reproducible deployments in any containerized environment.

---

## 🏗️ Architecture Overview

This server is designed as a secure middleware layer. It prevents direct exposure of your WordPress database and API keys to the client application.

```
┌────────────┐      ┌──────────────────┐      ┌──────────────────────────┐
| Client App | ───> |  FastAPI Server  | ───> |   WordPress MySQL DB     |
└────────────┘      │ (This Project)   |      │ (for user data & pw hash)│
                    └──────────────────┘      └──────────────────────────┘
                           │      │
                           │      └──────────> ┌──────────────────────────┐
                           │                   |   WordPress Site (WP-JSON) |
                           │                   │ (for JWT & WC-AM API)    │
                           │                   └──────────────────────────┘
                           │
                           └──────────> ┌──────────────────────────┐
                                        |   PostgreSQL DB          |
                                        │ (for Session Management) |
                                        └──────────────────────────┘
```

---

## 🔧 Getting Started

Follow these steps to get the server running locally.

### Prerequisites

- Python 3.11+
- Access to a WordPress database (MySQL/MariaDB)
- A running PostgreSQL database

### 1. Clone the Repository

```sh
git clone <your-repo-url>
cd websocket_test
```

### 2. Install Dependencies

It's recommended to use a virtual environment.

```sh
python -m venv .venv
source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root. Use the following template and fill in your database credentials and other details. **Remember to use quotes for all values to prevent parsing errors.**

```env
# .env

# WordPress Database (MySQL/MariaDB)
WP_MYSQL_USER="your_wp_db_user"
WP_MYSQL_PASS="your_wp_db_password"
WP_MYSQL_HOST="your_wp_db_host"
WP_MYSQL_PORT="3306"
WP_MYSQL_DB_NAME="your_wp_db_name"

# Session Database (PostgreSQL)
PG_USER="your_pg_user"
PG_PASSWORD="your_pg_password"
PG_HOST="your_pg_host"
PG_DB_NAME="your_pg_db_name"
```

### 4. Initialize the Session Database

Run the `create_pg_db.py` script once to create the necessary tables (`user_sessions` and `logs`) in your PostgreSQL database.

```sh
python create_pg_db.py
```

### 5. Run the Server

Use the `entry.py` script to start the Uvicorn server with live reloading and configured logging.

```sh
python entry.py
```

The server will be available at `http://127.0.0.1:8000`.

---

## 📚 API Endpoints

### User Authentication

#### `POST /login`
- **Description**: Authenticates a user with their WordPress credentials and returns a JWT token and user data.
- **Query Parameters**:
  - `user_login` (str): The user's username or email.
  - `user_pass` (str): The user's **Application Password** (required by the JWT plugin).
- **Success Response**: A `TokenData` JSON object.

### License Management

#### `POST /license/{action}`
- **Description**: Performs a license action (activate, deactivate, status) for a user.
- **Path Parameter**:
  - `action` (str): Can be `activate`, `deactivate`, or `status`.
- **Query Parameters**:
  - `username` (str)
  - `client_id` (int): The user's WordPress ID.
  - `token` (str): The JWT token obtained from `/login`.
  - `session_id` (str): A unique identifier for the client instance.
  - `client_ip` (str)
- **Success Response**: A `LicenseResponse` JSON object.

---

## 🐳 Deployment

This application is ready to be deployed as a Docker container. The included `dockerfile` sets up the environment and runs the application using a production-grade Gunicorn server.

Build the image:
```sh
docker build -t license-server .
```

Run the container (remember to pass your environment variables):
```sh
docker run -d --env-file .env -p 8080:8080 license-server
```

---

## 👨‍💻 Developer Guide

This guide provides additional details for developers working on this middleware.

### Core Logic

- **`login_server.py`**: This is the main FastAPI application file. It defines all API endpoints, data models (using SQLModel), and database interactions.
    - **Authentication Flow**: The `/login` endpoint takes a username and password. It first queries the WordPress MySQL database to get the user's data, including their hashed password. It then uses the `verify_pw_hash` function to securely check the provided password against the hash. If valid, it calls out to the WordPress site's JWT plugin to get an authentication token.
    - **License Management Flow**: The `/license/{action}` endpoint orchestrates license management. It first retrieves the user's license data (the `master_api_key`) from the `wp_wc_am_api_resource` table in the WordPress database. It then creates or updates a session in the local PostgreSQL database. Finally, it makes a server-to-server request to the WooCommerce API Manager endpoint on the live WordPress site to perform the requested action (`activate`, `deactivate`, or `status`).
    - **Session Handling**: The server maintains its own session state in a PostgreSQL database (`user_sessions` table). This allows it to track which users have active license sessions. A background task (`deactivate_expired_sessions`) runs continuously to clean up sessions that have been inactive for a set period, automatically deactivating the license on the WordPress side.

- **`login_client.py`**: This is a simple Python client script that demonstrates how to interact with the FastAPI server. It shows the full authentication and license activation/status check cycle. It's useful for testing the server endpoints locally.

### Database Models

The application uses `SQLModel` for ORM capabilities.

- **WordPress Models** (`WPUsers`, `WPWCAMApiActivation`, `WPWCAMApiResource`): These models map directly to tables in the WordPress database. They are used for read-only operations to fetch user and license data.
- **Session Models** (`UserSession`, `Logs`): These models map to tables created in the dedicated PostgreSQL database. They are used for read-write operations to manage sessions and log events.

### Setup and Configuration Notes

- **Password Hashing**: The `verify_pw_hash` function is critical. It correctly handles the modern `$wp$` bcrypt hashes used by recent WordPress versions. This requires the `bcrypt` and `passlib` libraries.
- **Environment Variables**: The use of a `.env` file is crucial for security. Never hard-code credentials in the source code. The `dotenv` library loads these variables at startup.
- **Asynchronous Operations**: The server uses `asyncio` and `asyncpg` for non-blocking database calls to the PostgreSQL session database, ensuring high performance. Interactions with the WordPress MySQL database are synchronous as `mysql-connector-python` does not have mature `asyncio` support.