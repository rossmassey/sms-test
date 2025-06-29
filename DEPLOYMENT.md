# Deployment configurations for various ASGI hosts

## Render (render.yaml)
```yaml
services:
  - type: web
    name: sms-outreach-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: FIREBASE_CRED_PATH
        value: /opt/render/project/src/firebase-service-account.json
      - key: FIREBASE_PROJECT_ID
        sync: false
      - key: TWILIO_ACCOUNT_SID
        sync: false
      - key: TWILIO_AUTH_TOKEN
        sync: false
      - key: TWILIO_PHONE_NUMBER
        sync: false
      - key: OPENAI_API_KEY
        sync: false
      - key: API_KEY
        sync: false
```

## Railway
```toml
# railway.toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
```

## Fly.io (fly.toml)
```toml
app = "sms-outreach-backend"
primary_region = "ord"

[build]

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0

[env]
  PORT = "8000"
```

## Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Environment Variables to Set
All platforms require these environment variables:
- FIREBASE_CRED_PATH
- FIREBASE_PROJECT_ID  
- TWILIO_ACCOUNT_SID
- TWILIO_AUTH_TOKEN
- TWILIO_PHONE_NUMBER
- OPENAI_API_KEY
- API_KEY
