# Auth0 + Django + Nuxt MFA System

A secure authentication system architecture combining Auth0 for identity provision, Django for business logic and MFA, and Nuxt 3 for the frontend.

## 🚀 Features

- **Auth0 Integration**: External Identity Provider (Google, etc.) handled by Auth0.
- **Django Backend**:
    - User Approval Workflow (Admin must approve new users).
    - **Dual MFA Support**:
        - **TOTP (High Security)**: Google Authenticator compatible.
        - **Email OTP (Medium Security)**: 6-digit code via email.
    - Custom User Model linked to Auth0 `sub`.
- **Nuxt 3 Frontend**:
    - Universal Login via Auth0.
    - Protected Dashboard.
    - MFA Setup & Verification UI.
- **Containerization**: Podman/Docker compatible setup.

## 🧱 Architecture

```
[Nuxt 3] <--> [Auth0 (Login)]
   |
   +---> [Django API]
            |
            +--> [PostgreSQL]
```

## 🛠️ Setup & Run

### 1. Prerequisites
- Docker (or Podman) & Docker Compose
- Auth0 Account (Tenant)

### 2. Configuration
Copy the template and edit `.env`:
```bash
cp .env.example .env
```

#### Environment Variables

| Variable | Description | Example |
| :--- | :--- | :--- |
| **Auth0** | | |
| `AUTH0_DOMAIN` | Auth0 Tenant Domain | `dev-xyz.auth0.com` |
| `AUTH0_CLIENT_ID` | Auth0 App Client ID | `AbCdEf123456...` |
| `AUTH0_CLIENT_SECRET` | Auth0 App Client Secret | `secret_key...` |
| `AUTH0_AUDIENCE` | API Identifier | `https://api.myapp.com` |
| **Django (Backend)** | | |
| `DJANGO_SECRET_KEY` | Django Security Key | `s3cr3t...` |
| `DATABASE_URL` | Postgres Connection URL | `postgresql://user:pass@db:5432/db` |
| `MFA_ISSUER_NAME` | Name in Authenticator App | `MyApp` |
| `MFA_METHOD` | `TOTP` or `EMAIL` | `TOTP` |
| `DEBUG` | Debug Mode | `True` |
| **Email (SMTP)** | | |
| `EMAIL_HOST` | SMTP Server | `smtp.gmail.com` |
| `EMAIL_PORT` | SMTP Port | `587` |
| `EMAIL_USE_TLS` | TLS Encryption | `True` |
| `EMAIL_HOST_USER` | SMTP Username | `user@example.com` |
| `EMAIL_HOST_PASSWORD` | SMTP Password | `password` |
| `DEFAULT_FROM_EMAIL` | Sender Address | `no-reply@example.com` |
| **Nuxt (Frontend)** | | |
| `NUXT_PUBLIC_AUTH0_DOMAIN` | Same as `AUTH0_DOMAIN` | |
| `NUXT_PUBLIC_AUTH0_CLIENT_ID`| Same as `AUTH0_CLIENT_ID` | |
| `NUXT_PUBLIC_AUTH0_AUDIENCE` | Same as `AUTH0_AUDIENCE` | |
| `NUXT_PUBLIC_API_BASE_URL` | Backend URL | `http://localhost:8000` |

### 3. Start System
```bash
docker-compose up --build
```

### 4. Database Migration (First Run)
```bash
docker-compose exec backend python manage.py migrate
```

### 5. First Login & Approval
1. Access `http://localhost:3000` and Login.
2. You will be redirected to Auth0.
3. Login with a Google Account or Auth0 User.
4. **First Time**: You will be redirected to the App.
   - If `is_approved` is False, you will see a "Not Approved" error (check console/network).
   - **Action**: Approve the user manually in Django.

```bash
# Approve user (replace email)
docker-compose exec backend python manage.py shell
>>> from app.models import User
>>> u = User.objects.get(email='your@email.com')
>>> u.is_approved = True
>>> u.save()
```

## 📚 API Endpoints

- `POST /api/auth/authorize`: Exchange Auth0 Token for User Session/Status.
- `POST /api/mfa/setup`: Initialize MFA (TOTP or Email).
- `POST /api/mfa/verify`: Verify code and enable MFA/Login.
- `GET /api/auth/me`: Get current user info.

## 📝 License
Apache 2.0
