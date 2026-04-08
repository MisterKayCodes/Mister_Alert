# Mister Alert Database Setup Script (PostgreSQL)

# 1. Start the Docker Container
Write-Host "🚀 Launching PostgreSQL container..." -ForegroundColor Cyan
docker-compose up -d

# 2. Wait for Postgres to be ready (brief pause)
Write-Host "⏳ Waiting for database to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# 3. Synchronize migrations
Write-Host "📝 Running database migrations (Alembic)..." -ForegroundColor Cyan
.\venv\Scripts\python.exe -m alembic upgrade head

Write-Host "`n✅ PostgreSQL Setup Complete!" -ForegroundColor Green
Write-Host "Your bot is now connected to port 5433." -ForegroundColor Gray
