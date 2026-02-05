# Database Setup & Data Seeding

This guide explains how to deploy the database using Docker and populate it with non-sensitive sample data for development and testing.

## Prerequisites

- [Docker](https://www.docker.com/) installed
- [Docker Compose](https://docs.docker.com/compose/) installed
- Python 3.9+ (if running scripts locally)

## 1. Deploy Database with Docker

We use `docker-compose` to spin up a MySQL 8.0 instance and the backend service.

### Start Services

Run the following command in the `smart-deal-app` directory:

```bash
cd smart-deal-app
docker-compose up -d db
```

This will start the `smartdeal_db` container on port `3306`.

- **Database Name**: `smartdeal`
- **User**: `root`
- **Password**: `root`

### Verify Connection

You can check if the database is running:

```bash
docker ps
# OR
docker logs smartdeal_db
```

## 2. Seed Non-Sensitive Sample Data

We have a built-in mock generator that creates realistic (but fake) German supermarket deals. This is safe for public demos and testing.

### Option A: Run via Backend API (Recommended)

If the backend is running (`docker-compose up backend` or `uvicorn`), you can trigger data generation via the Admin UI.

1.  Navigate to `http://localhost:3000/admin` (or wherever your frontend is running).
2.  Go to the **"Demo Data"** section.
3.  Click **"Generate Mock Data"**.

### Option B: Run Script Manually

You can directly run the Python script to insert 2000+ mock deals.

**Requirements**:
Ensure you have the backend dependencies installed (`pip install -r backend/requirements.txt`).

**Run the script**:

```bash
cd smart-deal-app/backend
python -m services.mock_generator
```

*Note: You might need to set environment variables if your DB host isn't localhost (e.g., if running from outside Docker while DB is in Docker).*

```bash
export DB_HOST=127.0.0.1
export DB_USER=root
export DB_PASSWORD=root
python -m services.mock_generator
```

## 3. Resetting the Database

To clear all data and start fresh:

1.  Stop the containers:
    ```bash
    docker-compose down
    ```
2.  Remove the volume (WARNING: deletions all data):
    ```bash
    docker volume rm smart-deal-app_db_data
    ```
3.  Restart:
    ```bash
    docker-compose up -d db
    ```
