# Estado del Lab — AROS Platform

**Última actualización:** 2026-05-13  
**Proyecto:** `/Users/aimarhp/Desktop/creador-webs-ai`

---

## Máquina host

| Campo | Valor |
|-------|-------|
| IP LAN | `192.168.1.15` |
| OS | macOS Darwin 24.6.0 |
| Docker | 27.5.1 |
| Docker network (interna) | `172.20.0.0/16` (gateway `172.20.0.1`) |

---

## Contenedores en red (docker compose)

| Contenedor | IP interna | Puerto host | Puerto container | Estado |
|------------|-----------|-------------|-----------------|--------|
| `creador-webs-ai-redis-1` | `172.20.0.2` | `6379` | `6379` | healthy |
| `creador-webs-ai-postgres-1` | `172.20.0.3` | `5432` | `5432` | healthy |
| `creador-webs-ai-backend-1` | `172.20.0.4` | `8000` | `8000` | running |
| `creador-webs-ai-celery_worker-1` | `172.20.0.5` | — | `8000` | running |
| `creador-webs-ai-celery_beat-1` | `172.20.0.6` | — | `8000` | running |
| `creador-webs-ai-frontend-1` | `172.20.0.7` | `3000` | `3000` | running |

> Los contenedores se comunican entre sí usando sus nombres de servicio como hostname:
> `postgres:5432`, `redis:6379`, `backend:8000`

---

## URLs de acceso (desde el host)

| Servicio | URL |
|---------|-----|
| Dashboard web | http://localhost:3000 |
| API REST | http://localhost:8000 |
| Swagger / Docs | http://localhost:8000/docs |
| Sitios generados | http://localhost:8000/static/sites/{repo-name}/ |
| Health check | http://localhost:8000/health |

---

## Configuración activa del backend (`backend/.env`)

| Variable | Valor actual |
|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://aros:aros_pass@postgres:5432/aros_db` |
| `REDIS_URL` | `redis://redis:6379/0` |
| `AROS_API_URL` | `http://localhost:8000` |
| `AROS_API_KEY` | *(vacío — acceso abierto en dev)* |
| `JWT_ALGORITHM` | `HS256` |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `60` |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | `7` |
| `JWT_SECRET_KEY` | `aros-super-secret-jwt-key-change-in-production` |
| `CORS_ORIGINS` | `["http://localhost:3000","http://localhost:3001"]` |
| `DEBUG` | `true` |
| `ANTHROPIC_API_KEY` | *(configurada — no se muestra)* |

---

## Base de datos PostgreSQL

**DB:** `aros_db` · **User:** `aros` · **Password:** `aros_pass`

### Tablas activas

| Tabla | Filas actuales | Descripción |
|-------|---------------|-------------|
| `users` | 2 | Inversores registrados (demo_investor, aros_admin) |
| `wallets` | 2 | Wallets virtuales — €1.000 demo por usuario |
| `wallet_transactions` | ≥1 | Historial de depósitos y movimientos |
| `assets` | 15 | Activos digitales generados por el pipeline |
| `deployments` | — | Deployments de cada asset (local/github/vercel) |
| `metrics` | — | Métricas diarias de tráfico por asset |
| `activity_events` | 21 | Feed de actividad en tiempo real |

---

## Celery (workers y beat)

| Worker | Tareas registradas |
|--------|-------------------|
| `celery_worker` | `tasks.run_pipeline`, `tasks.optimize_portfolio`, `app.workers.simulation.simulate_traffic_tick` |
| `celery_beat` | `simulate-traffic-tick` cada **60 segundos** |

El beat dispara `simulate_traffic_tick` automáticamente — genera visitas/conversiones/revenue simulado
para todos los assets con status `live`, `scaling` u `optimizing`.

---

## Configuraciones realizadas en esta sesión

### Backend — nuevas funcionalidades (v2.0)

#### 1. Autenticación JWT
- **Archivo:** `backend/app/services/auth_service.py`
- Registro de usuarios (`POST /api/auth/register`) con wallet demo de €1.000 auto-creada
- Login OAuth2 (`POST /api/auth/login`) devuelve `access_token` + `refresh_token`
- Endpoint `/api/auth/me` retorna perfil + saldo de wallet
- Hash de contraseñas con **bcrypt 4.2.1** (passlib descartado por incompatibilidad con Python 3.12)
- JWT con `HS256`, expiración configurable via `.env`

#### 2. Investment Wallet
- **Archivos:** `backend/app/models/wallet.py`, `backend/app/routes/wallet.py`
- Modelo `Wallet` + `WalletTransaction` (native_enum=False en todos los Enum de SQLAlchemy)
- Endpoints: `GET /api/wallet`, `POST /api/wallet/deposit`, `GET /api/wallet/transactions`
- ROI calculado sobre capital invertido (no depositado) para evitar mostrar -100% en cuentas nuevas

#### 3. Activity Feed + WebSocket
- **Archivo:** `backend/app/routes/activity.py`
- `GET /api/activity` — lista de eventos paginados
- `WS /api/activity/ws?token=<jwt>` — stream de eventos en tiempo real
- `ConnectionManager` en memoria para broadcast por usuario y global
- Helper `emit_event()` usado internamente para emitir a DB + WebSocket simultáneamente

#### 4. Traffic Simulation Engine
- **Archivo:** `backend/app/workers/simulation.py`
- Celery task `simulate_traffic_tick` disparado cada 60s por celery_beat
- Genera visitas (3–40/tick, ×3 para assets en scaling), conversiones y revenue
- Revenue por modelo: affiliates ~€5-45/conv, ads CPM, ecommerce ~€20-150/conv, leads ~€3-15/conv
- Actualiza tabla `metrics` (upsert diario) y tabla `assets` (acumula revenue)
- Emite `ActivityEvent` si revenue > €10 o visitas > 25

#### 5. Enterprise Asset Factory v2
- **Archivo:** `backend/app/services/asset_factory.py`
- Genera **8 archivos** por pipeline (antes: 3)
- Pipeline: 9 llamadas a la API de Claude en 4 fases paralelas (~320s total)
  - Fase 0: Plan compacto JSON (brand, copy, outlines de posts)
  - Fase 1 (×3 paralelas): `index.html` + `styles.css` + `scripts.js`
  - Fase 2 (×3 paralelas): `post-1.html` + `post-2.html` + `post-3.html`
  - Fase 3 (×2 paralelas): `blog.html` + `contact.html`
- Diseño: Tailwind CDN + Google Fonts (Inter + Playfair Display) + paleta slate/accent
- SEO: `<title>` único, `<meta description>`, OpenGraph, JSON-LD (WebPage/Article/Blog/ContactPage)
- Artículos: 2.000–2.700 palabras cada uno, TOC con anchors, barra de progreso, sidebar sticky
- JS compartido: mobile menu, FAQ accordion, stats counter, IntersectionObserver, form handler
- Pixel de tracking inyectado en **todos** los .html (antes solo index.html)

#### 6. Nuevas dependencias añadidas
```
python-jose[cryptography]==3.3.0
bcrypt==4.2.1
websockets==13.1
email-validator==2.2.0
```

### Frontend — nuevas páginas y componentes

| Ruta | Descripción |
|------|-------------|
| `/login` | Formulario auth + botón de acceso demo |
| `/register` | Registro de inversor, cuenta con €1.000 demo |
| `/wallet` | Saldo, depósito, historial de transacciones |
| `/activity` | Feed WebSocket en tiempo real con iconos por tipo de evento |
| `/dashboard` | Actualizado con gráficos Recharts (revenue por asset, breakdown de estados) |

**Nuevas dependencias npm:**
```
recharts 2.x, zustand 5.x, framer-motion 11.x, @tanstack/react-query 5.x,
js-cookie 3.x, date-fns 4.x
```

**Auth store (Zustand):** `frontend/src/store/auth.ts` — persiste tokens en localStorage,
`setTokenGetter()` inyecta el JWT en todas las llamadas de `api.ts` automáticamente.

**Sidebar:** muestra `@username` + saldo de wallet en tiempo real, botón de logout.

---

## Notas de operación

- **Para levantar el lab:** `docker compose up -d` (desde `/Users/aimarhp/Desktop/creador-webs-ai`)
- **Para reconstruir tras cambios en `requirements.txt`:** `docker compose build backend && docker compose up -d --force-recreate backend celery_worker celery_beat`
- **Para ver logs en vivo:** `docker compose logs -f backend celery_worker`
- **Usuarios demo creados:**
  - `demo@aros.ai` / `demo123` (demo_investor)
  - `admin@aros.ai` / `admin123` (aros_admin)
- **JWT_SECRET_KEY** en `.env` usa valor por defecto — cambiar antes de cualquier exposición pública
- **AROS_API_KEY** vacío = sin autenticación por API key (modo dev). Rellenar para producción.
