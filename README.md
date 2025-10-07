# Websocket and FastAPI License Server for WooCommerce

This repository contains a Python-based server application that provides a licensing system for software, integrating with WooCommerce. It includes a WebSocket server for real-time communication and a FastAPI server for handling login and license management.

## Project Overview

The primary components of this project are:

*   **`login_server.py`**: A FastAPI application that handles user authentication and license key activation, deactivation, and status checks. It connects to a WordPress MySQL database to verify user data and a PostgreSQL database to manage user sessions.
*   **`login_client.py`**: A client-side script that demonstrates how to interact with the `login_server.py` API. It simulates a user logging in, activating a license, and periodically checking the license status.
*   **`s.py`**: An `aiohttp` WebSocket server that manages real-time communication with clients, using JWT for authentication and interacting with a license API.
*   **`c.py`**: A client-side script for the WebSocket server, demonstrating how to connect, authenticate, and exchange messages.

## Setup

### Prerequisites

*   Python 3.8+
*   Docker (optional, for containerized deployment)
*   Access to a WordPress database
*   A PostgreSQL database

### Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/your-repo-name.git
    cd your-repo-name
    ```

2.  **Create a virtual environment and install dependencies:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3.  **Configure environment variables:**

    Create a `.env` file in the root directory and add the following variables with your database credentials and other required values:

    ```
    WP_MYSQL_USER=your_wp_db_user
    WP_MYSQL_PASS=your_wp_db_password
    WP_MYSQL_HOST=your_wp_db_host
    WP_MYSQL_PORT=your_wp_db_port
    WP_MYSQL_DB_NAME=your_wp_db_name
    PG_USER=your_pg_db_user
    PG_PASSWORD=your_pg_db_password
    PG_HOST=your_pg_db_host
    PG_DB_NAME=your_pg_db_name
    WP_JWT=your_jwt_secret
    ```

## Usage

### Running the Login Server

To start the FastAPI login server, you will need `uvicorn`:
```bash
pip install uvicorn
```
Then run the following command:

```bash
uvicorn login_server:app --reload
```

The server will be available at `http://127.0.0.1:8000`.

### Running the Login Client

To test the login server, you can run the client script:

```bash
python login_client.py
```

This script will authenticate with the server, activate a license, and check its status.

### Running the WebSocket Server

To start the WebSocket server, run:

```bash
python s.py
```

### Running the WebSocket Client

To connect to the WebSocket server, run:
```bash
python c.py
```