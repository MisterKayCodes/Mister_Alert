# Mister Alert Infrastructure (Docker)

This directory contains everything needed to run the PostgreSQL database for Mister Alert.

## The Port Strategy
To avoid conflicts with other projects (like SkyPunt), we use port **5433** on the host.

- **Host Port (5433)**: This is what our `.env` connects to.
- **Container Port (5432)**: This is the internal Postgres port.
- **Why?**: This allows you to run multiple PostgreSQL instances (Mister Alert, SkyPunt, etc.) on the same machine without them fighting for the same "door".

## Redis (Caching & Rate Limiting)
We use a containerized **Redis 7-alpine** instance for fast, temporary data.
- **Port**: `6379:6379` (standard mapping).

## VPS Deployment (24/7 Cloud)
When moving to your Ubuntu VPS, follow these steps for a "Senior-grade" launch:

1. **Pull & Start Stack**:
   ```bash
   git pull
   docker compose up -d
   ```

2. **Liftoff (Background Process)**:
   This keeps the bot alive after you log out:
   ```bash
   nohup python3 main.py > bot.log 2>&1 &
   ```

3. **Monitor**:
   ```bash
   tail -f bot.log
   ```

## Key Files
- `docker-compose.yml`: Defines the database service and its volume.
- `setup_db.ps1`: An automation script to launch the container and run migrations.

## Basic Commands

### 1. Launch the Database
```powershell
docker-compose up -d
```

### 2. View Database Logs
```powershell
docker logs mister_alert_db
```

### 3. Reset the Database (Dangerous!)
To wipe common data and start fresh:
```powershell
docker-compose down -v
docker-compose up -d
```

## Note for Multiple Projects
If you build a new project, just copy this pattern but change the **first number** in the port mapping (e.g., `5434:5432`).
