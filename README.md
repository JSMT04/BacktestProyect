# BacktestPro 📊

**Plataforma local de backtesting de estrategias de trading** con datos reales, ejecución asíncrona y reportes profesionales.

![Stack](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square)
![Stack](https://img.shields.io/badge/Frontend-React%20+%20TypeScript-61DAFB?style=flat-square)
![Stack](https://img.shields.io/badge/Engine-vectorbt-blueviolet?style=flat-square)
![Stack](https://img.shields.io/badge/Charts-TradingView%20Lightweight-131722?style=flat-square)

---

## Características

- **Datos Reales** — Descarga automática de OHLCV desde yfinance, Binance (CCXT) y Alpha Vantage con caché Parquet local.
- **Gráficos Interactivos** — TradingView Lightweight Charts con velas, volumen, indicadores técnicos (SMA, EMA, RSI, MACD, Bollinger Bands) y marcadores de trades.
- **Constructor Visual de Estrategias** — Crea reglas de entrada/salida usando condiciones visuales (cruces, comparaciones) sin escribir código.
- **Editor de Código Python** — Monaco Editor integrado para escribir estrategias avanzadas con `pandas`, `numpy` y `pandas-ta`.
- **Motor vectorbt** — Ejecución rápida de backtests con stop-loss, take-profit, trailing stop y comisiones.
- **Progreso en Tiempo Real** — WebSocket nativo para monitorear el progreso del backtest con barra flotante y botón de cancelar.
- **Reportes Completos** — Panel con métricas (PnL, Win Rate, Profit Factor, Drawdown), curva de equity con Recharts y tabla de trades con TanStack Table.
- **Exportación** — Descarga de reportes en PDF (reportlab), CSV y JSON.
- **Guardado de Estrategias** — Persistencia en SQLite con versionamiento automático.
- **Historial de Backtests** — Consulta y recarga de simulaciones anteriores.
- **Autenticación JWT** (opcional) — Registro/login con bcrypt + JWT activable vía variable de entorno.

---

## Estructura del Proyecto

```
backtestpro/
├── backend/
│   ├── core/              # Configuración, seguridad, estado global, excepciones
│   ├── models/            # SQLAlchemy ORM, Pydantic schemas, database setup
│   ├── routers/           # Endpoints REST (data, backtest, strategies, reports, auth)
│   ├── services/          # DataManager, IndicatorService, BacktestEngine, ReportGenerator
│   ├── data/              # SQLite DB + caché Parquet (auto-generado)
│   ├── main.py            # FastAPI app, CORS, WebSocket, exception handlers
│   ├── requirements.txt   # Dependencias Python
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/    # Chart, Sidebar, Report, shared (TopBar, ProgressBar, etc.)
│   │   ├── stores/        # Zustand stores (chartStore, backtestStore, strategyStore)
│   │   ├── services/      # API client (axios)
│   │   ├── types/         # TypeScript interfaces (contratos API)
│   │   ├── App.tsx         # Layout principal
│   │   └── index.css      # Design system (CSS variables + Tailwind)
│   ├── package.json
│   ├── vite.config.ts     # Proxy /api → backend, /ws → WebSocket
│   ├── tailwind.config.js
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Requisitos

- **Python** 3.11+
- **Node.js** 18+ y npm
- **Docker** y Docker Compose (opcional, para ejecución containerizada)

---

## Instalación y Ejecución

### Requisitos Previos
Asegúrate de tener instalado en tu sistema:
- **Git** para clonar el repositorio.
- **Python 3.11** o superior. Puedes verificarlo con `python --version`.
- **Node.js 18** o superior (incluye `npm`). Verifícalo con `node -v` y `npm -v`.
- Opcionalmente, **Docker Desktop** si prefieres la Opción B.

---

### Opción A: Desarrollo Local paso a paso (Recomendado)

Esta opción es ideal si deseas editar el código o probar las funcionalidades directamente en tu entorno. Requiere abrir dos terminales separadas (una para el backend y otra para el frontend).

#### Paso 1: Configurar el entorno virtual y levantar el Backend (Terminal 1)

1. Abre una terminal y navega hasta la carpeta del backend:
   ```bash
   cd backtestpro/backend
   ```

2. Crea un entorno virtual de Python. Esto asegura que las dependencias del proyecto no interfieran con otras aplicaciones de tu sistema:
   ```bash
   python -m venv venv
   ```

3. Activa el entorno virtual:
   - **En Windows:**
     ```cmd
     venv\Scripts\activate
     ```
   - **En Mac / Linux:**
     ```bash
     source venv/bin/activate
     ```
   *(Sabrás que está activado porque verás `(venv)` al inicio de tu línea de comandos).*

4. Instala todas las dependencias requeridas (esto puede tomar unos minutos la primera vez):
   ```bash
   pip install -r requirements.txt
   ```

5. Copia el archivo de variables de entorno de ejemplo para crear tu configuración local:
   - **En Windows:**
     ```cmd
     copy ..\.env.example .env
     ```
   - **En Mac / Linux:**
     ```bash
     cp ../.env.example .env
     ```

6. Inicia el servidor de FastAPI:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```
   *✅ El backend estará corriendo exitosamente. Puedes probar que funciona ingresando a `http://localhost:8000/docs` en tu navegador para ver la documentación interactiva de la API.*

#### Paso 2: Instalar dependencias y levantar el Frontend (Terminal 2)

1. Abre una **nueva** ventana de terminal (manteniendo abierta la primera) y navega a la carpeta del frontend:
   ```bash
   cd backtestpro/frontend
   ```

2. Instala los paquetes de Node.js necesarios:
   ```bash
   npm install
   ```

3. Inicia el servidor de desarrollo de Vite:
   ```bash
   npm run dev
   ```
   *✅ El frontend estará listo. Abre `http://localhost:3000` en tu navegador para comenzar a utilizar BacktestPro.*

---

### Opción B: Ejecución con Docker Compose (Más sencillo)

Si prefieres no instalar Python o Node.js directamente en tu máquina, puedes correr todo en contenedores usando Docker. Esta opción levanta tanto el frontend como el backend con un solo comando.

1. Abre una terminal en la raíz del proyecto (`backtestpro`).

2. Crea tu archivo de variables de entorno copiando la plantilla:
   - **En Windows:**
     ```cmd
     copy .env.example .env
     ```
   - **En Mac / Linux:**
     ```bash
     cp .env.example .env
     ```

3. Construye y levanta los servicios:
   ```bash
   docker-compose up --build
   ```
   *(La primera vez tomará algo de tiempo descargar las imágenes base y construir el proyecto).*

4. Una vez finalizado, ingresa a `http://localhost:3000` en tu navegador. 

*Para detener la aplicación, simplemente presiona `Ctrl+C` en la terminal o ejecuta `docker-compose down`.*

---

## Configuración (.env)

| Variable | Descripción | Default |
|----------|-------------|---------|
| `ALPHA_VANTAGE_KEY` | API key de Alpha Vantage | `your_key_here` |
| `BINANCE_API_KEY` | API key de Binance (opcional) | `your_key_here` |
| `DATABASE_URL` | URL de la base de datos SQLite | `sqlite+aiosqlite:///./data/backtestpro.db` |
| `BACKEND_PORT` | Puerto del servidor FastAPI | `8000` |
| `FRONTEND_PORT` | Puerto del servidor Vite | `3000` |
| `AUTH_ENABLED` | Activar autenticación JWT | `false` |
| `SECRET_KEY` | Clave secreta para JWT | Cambiar en producción |
| `CACHE_MAX_AGE_HOURS` | Horas antes de refrescar caché | `24` |

---

## API Endpoints

### Datos
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/v1/data/symbols/search?q=BTC` | Buscar símbolos |
| GET | `/api/v1/data/ohlcv?symbol=BTC/USDT&timeframe=1d&start=...&end=...` | Obtener velas OHLCV |
| GET | `/api/v1/data/timeframes` | Listar timeframes disponibles |
| POST | `/api/v1/data/indicators` | Calcular indicadores técnicos |

### Backtesting
| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/v1/backtest/run` | Iniciar un backtest |
| GET | `/api/v1/backtest/{job_id}` | Consultar resultado |
| DELETE | `/api/v1/backtest/{job_id}` | Cancelar un backtest |
| GET | `/api/v1/backtest/history/list` | Historial de backtests |
| WS | `/ws/backtest/{job_id}` | Progreso en tiempo real |

### Estrategias
| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/v1/strategies` | Crear estrategia |
| GET | `/api/v1/strategies` | Listar estrategias |
| GET | `/api/v1/strategies/{id}` | Obtener estrategia + versiones |
| PUT | `/api/v1/strategies/{id}` | Actualizar (nueva versión) |
| DELETE | `/api/v1/strategies/{id}` | Eliminar estrategia |

### Reportes
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/v1/reports/{backtest_id}/pdf` | Descargar reporte PDF |
| GET | `/api/v1/reports/{backtest_id}/csv` | Descargar trades CSV |
| GET | `/api/v1/reports/{backtest_id}/json` | Descargar resultado JSON |

### Autenticación (cuando AUTH_ENABLED=true)
| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/v1/auth/register` | Registrar usuario |
| POST | `/api/v1/auth/login` | Login y obtener JWT |

---

## Tecnologías

**Backend**: FastAPI, SQLAlchemy (async), vectorbt, pandas-ta, reportlab, python-jose, passlib  
**Frontend**: React 18, TypeScript, Vite, Zustand, TradingView Lightweight Charts, Monaco Editor, Recharts, TanStack Table, Tailwind CSS, Lucide Icons  
**Infraestructura**: Docker, Docker Compose, SQLite (aiosqlite), Parquet (pyarrow)

---

## Licencia

Proyecto académico / personal. Todos los derechos reservados.
