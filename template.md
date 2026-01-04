# Template MLOps - Architecture Complète

Ce document décrit l'architecture complète d'un pipeline MLOps et explique comment créer un nouveau projet en suivant cette structure.

## 📋 Table des matières

1. [Vue d'ensemble de l'architecture](#vue-densemble-de-larchitecture)
2. [Technologies utilisées](#technologies-utilisées)
3. [Structure du projet](#structure-du-projet)
4. [Guide de création d'un nouveau projet](#guide-de-création-dun-nouveau-projet)
5. [Configuration détaillée de chaque composant](#configuration-détaillée-de-chaque-composant)

---

## Vue d'ensemble de l'architecture

Cette architecture MLOps complète comprend :

```
┌─────────────────────────────────────────────────────────────────┐
│                    Pipeline MLOps Complet                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │   Ingestion  │───▶│   Training   │───▶│   Serving    │     │
│  │  (Prefect)   │    │  (Prefect +  │    │  (FastAPI)   │     │
│  │              │    │   MLflow)    │    │              │     │
│  └──────────────┘    └──────────────┘    └──────────────┘     │
│         │                   │                    │              │
│         ▼                   ▼                    ▼              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │  PostgreSQL │    │   Feature    │    │  Monitoring   │     │
│  │  (Database) │    │   Store      │    │ (Prometheus + │     │
│  │             │    │   (Feast)    │    │   Grafana)   │     │
│  └──────────────┘    └──────────────┘    └──────────────┘     │
│         │                   │                    │              │
│         └───────────────────┴────────────────────┘              │
│                           │                                     │
│                           ▼                                     │
│                  ┌──────────────┐                              │
│                  │   Drift      │                              │
│                  │  Detection   │                              │
│                  │  (Evidently) │                              │
│                  └──────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
```

### Flux de données

1. **Ingestion** : Les données brutes sont ingérées via Prefect, validées avec Great Expectations, et stockées dans PostgreSQL avec des snapshots temporels
2. **Feature Engineering** : Feast gère les features de manière centralisée (offline pour training, online pour serving)
3. **Training** : Les modèles sont entraînés via Prefect, trackés avec MLflow, et stockés dans MLflow
4. **Serving** : FastAPI expose un endpoint de prédiction qui utilise Feast pour récupérer les features en temps réel
5. **Monitoring** : Prometheus collecte les métriques de l'API, Grafana les visualise, et Evidently détecte le drift de données

---

## Technologies utilisées

### 🗄️ Base de données
- **PostgreSQL 16** : Base de données relationnelle pour stocker les données brutes, les snapshots temporels, et les métadonnées
- **Rôle** : Source de vérité pour toutes les données du pipeline

### 🔄 Orchestration
- **Prefect 3.6.1** : Orchestrateur de workflows pour gérer les pipelines d'ingestion, de training et de monitoring
- **Rôle** : Automatisation et orchestration des tâches MLOps

### 📊 Feature Store
- **Feast 0.56.0** : Feature store open-source pour gérer les features de manière centralisée
- **Rôle** : 
  - Mode offline : récupération de features historiques pour l'entraînement
  - Mode online : récupération de features en temps réel pour les prédictions

### 🤖 Machine Learning
- **MLflow 2.16.0** : Plateforme de gestion du cycle de vie des modèles ML
- **Rôle** : 
  - Tracking des expériences (paramètres, métriques, artifacts)
  - Registry de modèles
  - Déploiement de modèles
- **Scikit-learn 1.7.2** : Bibliothèque ML pour l'entraînement des modèles

### 🌐 API de prédiction
- **FastAPI** : Framework web moderne pour créer l'API REST de prédiction
- **Uvicorn** : Serveur ASGI pour exécuter FastAPI
- **Rôle** : Exposition d'un endpoint HTTP pour servir les prédictions en production

### 📈 Monitoring et Observabilité
- **Prometheus 2.55.1** : Système de monitoring et collecte de métriques
- **Grafana 11.2.0** : Plateforme de visualisation et dashboards
- **Prometheus Client (Python)** : Bibliothèque pour instrumenter l'API avec des métriques
- **Rôle** : Monitoring des performances de l'API (RPS, latence, erreurs)

### 🔍 Détection de drift
- **Evidently 0.7.15** : Bibliothèque pour détecter le drift de données et la dégradation des modèles
- **Rôle** : Comparaison de distributions de données entre périodes pour détecter le drift

### ✅ Validation de données
- **Great Expectations 0.17.21** : Framework de validation de données
- **Rôle** : Validation de la qualité des données lors de l'ingestion

### 🐳 Containerisation
- **Docker** : Containerisation de tous les services
- **Docker Compose** : Orchestration multi-conteneurs
- **Rôle** : Isolation, reproductibilité et déploiement facile

### 📦 Gestion des dépendances
- **Python 3.11** : Langage de programmation principal
- **pip** : Gestionnaire de paquets Python
- **requirements.txt** : Fichiers de dépendances pour chaque service

---

## Structure du projet

```
mon-projet-mlops/
├── api/                          # Service API FastAPI
│   ├── app.py                    # Application FastAPI principale
│   ├── Dockerfile                # Image Docker pour l'API
│   └── requirements.txt          # Dépendances Python de l'API
│
├── services/                     # Services MLOps
│   ├── prefect/                  # Service Prefect (orchestration)
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── ingest_flow.py        # Flow d'ingestion de données
│   │   ├── train_baseline.py     # Script d'entraînement
│   │   └── monitor_flow.py       # Flow de monitoring/drift detection
│   │
│   ├── feast_repo/               # Repository Feast (Feature Store)
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── repo/                 # Configuration Feast
│   │       ├── feature_store.yaml
│   │       ├── entities.py       # Définition des entités
│   │       ├── data_sources.py   # Sources de données
│   │       └── feature_views.py  # Vues de features
│   │
│   ├── prometheus/                # Configuration Prometheus
│   │   └── prometheus.yml        # Configuration de scraping
│   │
│   └── grafana/                   # Configuration Grafana
│       └── provisioning/         # Provisioning automatique
│           ├── datasources/
│           │   └── prometheus.yml
│           └── dashboards/
│               └── json/
│
├── db/                           # Scripts de base de données
│   └── init/
│       └── 001_schema.sql        # Schéma initial PostgreSQL
│
├── data/                         # Données du projet
│   ├── seeds/                    # Données d'exemple
│   │   └── month_000/
│   │       ├── users.csv
│   │       ├── features.csv
│   │       └── labels.csv
│   └── processed/               # Données traitées
│
├── mlartifacts/                 # Artifacts MLflow
│   ├── artifacts/               # Modèles et artifacts
│   └── mlflow.db               # Base de données MLflow
│
├── reports/                     # Rapports et documentation
│   ├── rapport_tp1.md
│   ├── images TP1/
│   └── evidently/               # Rapports Evidently
│
├── docker-compose.yml           # Configuration Docker Compose
├── .env                        # Variables d'environnement (non versionné)
├── .gitignore                  # Fichiers à ignorer par Git
└── README.md                   # Documentation du projet
```

---

## Guide de création d'un nouveau projet

### Étape 1 : Initialisation du projet

```bash
# Créer le répertoire du projet
mkdir mon-projet-mlops
cd mon-projet-mlops

# Initialiser Git
git init
git remote add origin <votre-repo-git>

# Créer la structure de base
mkdir -p api services/prefect services/feast_repo/repo services/prometheus services/grafana/provisioning/datasources services/grafana/provisioning/dashboards/json
mkdir -p db/init data/seeds data/processed mlartifacts reports
```

### Étape 2 : Configuration Docker Compose

Créer `docker-compose.yml` :

```yaml
services:
  postgres:
    image: postgres:16
    env_file: .env
    volumes:
      - ./db/init:/docker-entrypoint-initdb.d
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  prefect:
    build: ./services/prefect
    depends_on:
      - postgres
      - mlflow
    env_file: .env
    environment:
      POSTGRES_HOST: postgres
      POSTGRES_PORT: 5432
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
      MLFLOW_TRACKING_URI: http://mlflow:5000
    volumes:
      - ./services/prefect:/opt/prefect/flows
      - ./data:/data
      - ./services/feast_repo/repo:/repo
      - ./reports:/reports

  feast:
    build: ./services/feast_repo
    depends_on:
      - postgres
    environment:
      FEAST_USAGE: "False"
    volumes:
      - ./services/feast_repo/repo:/repo

  api:
    build: ./api
    env_file: .env
    depends_on:
      - postgres
      - feast
      - mlflow
    ports:
      - "8000:8000"
    volumes:
      - ./api:/app
      - ./services/feast_repo/repo:/repo

  mlflow:
    image: ghcr.io/mlflow/mlflow:v2.16.0
    command: mlflow server --backend-store-uri sqlite:///mlartifacts/mlflow.db --default-artifact-root mlflow-artifacts:/ --host 0.0.0.0 --port 5000 --serve-artifacts --artifacts-destination /mlartifacts/artifacts
    volumes:
      - "./mlartifacts:/mlartifacts"
    ports:
      - "5000:5000"

  prometheus:
    image: prom/prometheus:v2.55.1
    volumes:
      - ./services/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
    ports:
      - "9090:9090"
    depends_on:
      - api

  grafana:
    image: grafana/grafana:11.2.0
    volumes:
      - ./services/grafana/provisioning:/etc/grafana/provisioning
      - grafana-data:/var/lib/grafana
    ports:
      - "3001:3000"
    depends_on:
      - prometheus

volumes:
  pgdata:
  mlartifacts:
  grafana-data:
```

### Étape 3 : Variables d'environnement

Créer `.env` :

```env
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=your_database
```

Créer `.gitignore` :

```
.env
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
mlartifacts/
*.db
*.sqlite
.DS_Store
```

### Étape 4 : Configuration de la base de données

Créer `db/init/001_schema.sql` avec votre schéma de base de données :

```sql
-- Exemple de schéma
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    -- autres colonnes
);

CREATE TABLE IF NOT EXISTS features (
    user_id TEXT,
    feature_date DATE,
    -- autres colonnes
    PRIMARY KEY (user_id, feature_date)
);

CREATE TABLE IF NOT EXISTS labels (
    user_id TEXT PRIMARY KEY,
    label_value BOOLEAN
);
```

### Étape 5 : Configuration de l'API FastAPI

Créer `api/app.py` :

```python
from fastapi import FastAPI
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import time
import mlflow
from feast import FeatureStore

app = FastAPI()

# Métriques Prometheus
REQUEST_COUNT = Counter("api_requests_total", "Total number of API requests")
REQUEST_LATENCY = Histogram("api_request_latency_seconds", "Latency of API requests in seconds")

# Charger le modèle depuis MLflow
mlflow.set_tracking_uri("http://mlflow:5000")
model = mlflow.sklearn.load_model("models:/your_model_name/Production")

# Feature Store
store = FeatureStore(repo_path="/repo")

class PredictionRequest(BaseModel):
    user_id: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/predict")
def predict(request: PredictionRequest):
    start_time = time.time()
    REQUEST_COUNT.inc()
    
    # Récupérer les features depuis Feast
    features = store.get_online_features(
        features=["your_feature_view:feature1", "your_feature_view:feature2"],
        entity_rows=[{"user_id": request.user_id}]
    )
    
    # Faire la prédiction
    prediction = model.predict(features.to_df())
    
    REQUEST_LATENCY.observe(time.time() - start_time)
    
    return {"user_id": request.user_id, "prediction": float(prediction[0])}
```

Créer `api/requirements.txt` :

```
fastapi
uvicorn[standard]
pydantic
scikit-learn
mlflow
feast
pandas
prometheus-client
psycopg2-binary
```

Créer `api/Dockerfile` :

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Étape 6 : Configuration Feast (Feature Store)

Créer `services/feast_repo/repo/feature_store.yaml` :

```yaml
project: your_project
registry: registry.db
provider: local
online_store:
  type: postgres
  connection_string: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
offline_store:
  type: postgres
  connection_string: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
```

Créer `services/feast_repo/repo/entities.py` :

```python
from feast import Entity

user = Entity(
    name="user_id",
    value_type=ValueType.STRING,
    description="User identifier",
)
```

Créer `services/feast_repo/repo/data_sources.py` :

```python
from feast.infra.offline_stores.contrib.postgres_offline_store.postgres_source import PostgreSQLSource

your_source = PostgreSQLSource(
    name="your_source",
    query="""
        SELECT user_id, feature_date,
               feature1, feature2, feature3
        FROM your_features_table
    """,
    timestamp_field="feature_date",
)
```

Créer `services/feast_repo/repo/feature_views.py` :

```python
from feast import FeatureView, Field
from feast.types import Float32, String
from .entities import user
from .data_sources import your_source

your_feature_view = FeatureView(
    name="your_feature_view",
    entities=[user],
    source=your_source,
    ttl=timedelta(days=1),
    schema=[
        Field(name="feature1", dtype=Float32),
        Field(name="feature2", dtype=Float32),
    ],
)
```

Créer `services/feast_repo/Dockerfile` :

```dockerfile
FROM python:3.11-slim

WORKDIR /repo

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

CMD ["bash", "-c", "tail -f /dev/null"]
```

Créer `services/feast_repo/requirements.txt` :

```
feast
pandas
psycopg2-binary
SQLAlchemy
```

### Étape 7 : Configuration Prefect

Créer `services/prefect/Dockerfile` :

```dockerfile
FROM prefecthq/prefect:3.0.3-python3.11

WORKDIR /opt/prefect/flows

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["bash", "-c", "prefect server start --host 0.0.0.0 --port 4200 & sleep 10 && prefect worker start --pool 'default-agent-pool' --work-queue 'default'"]
```

Créer `services/prefect/requirements.txt` :

```
prefect
feast
mlflow
scikit-learn
pandas
SQLAlchemy
psycopg2-binary
evidently
great_expectations
```

Créer `services/prefect/ingest_flow.py` (exemple) :

```python
import os
import pandas as pd
from sqlalchemy import create_engine
from prefect import flow, task

@task
def load_data(file_path: str) -> pd.DataFrame:
    return pd.read_csv(file_path)

@task
def validate_data(df: pd.DataFrame):
    # Validation avec Great Expectations ou pandas
    assert not df.empty, "DataFrame is empty"
    return True

@task
def save_to_db(df: pd.DataFrame, table_name: str):
    engine = create_engine(
        f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:"
        f"{os.getenv('POSTGRES_PASSWORD')}@"
        f"{os.getenv('POSTGRES_HOST')}:5432/"
        f"{os.getenv('POSTGRES_DB')}"
    )
    df.to_sql(table_name, engine, if_exists='append', index=False)

@flow(name="ingest_data")
def ingest_flow(file_path: str, table_name: str):
    df = load_data(file_path)
    validate_data(df)
    save_to_db(df, table_name)
    return f"Data ingested into {table_name}"

if __name__ == "__main__":
    ingest_flow("data/seeds/your_data.csv", "your_table")
```

### Étape 8 : Configuration Prometheus

Créer `services/prometheus/prometheus.yml` :

```yaml
global:
  scrape_interval: 10s

scrape_configs:
  - job_name: "api"
    metrics_path: /metrics
    static_configs:
      - targets: ["api:8000"]
```

### Étape 9 : Configuration Grafana

Créer `services/grafana/provisioning/datasources/prometheus.yml` :

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
```

### Étape 10 : Démarrage du projet

```bash
# Construire et démarrer tous les services
docker compose up -d

# Vérifier le statut
docker compose ps

# Voir les logs
docker compose logs -f api
```

### Étape 11 : Accès aux interfaces

- **API** : http://localhost:8000
- **MLflow UI** : http://localhost:5000
- **Prometheus** : http://localhost:9090
- **Grafana** : http://localhost:3001 (admin/admin par défaut)
- **Prefect UI** : http://localhost:4200 (si configuré)

---

## Configuration détaillée de chaque composant

### PostgreSQL

**Rôle** : Base de données principale pour stocker toutes les données

**Configuration** :
- Image : `postgres:16`
- Port : `5432`
- Volumes : 
  - Scripts d'initialisation dans `db/init/`
  - Données persistantes dans volume `pgdata`

**Utilisation** :
- Stocker les données brutes
- Stocker les snapshots temporels pour la reproductibilité
- Stocker les métadonnées Feast
- Backend pour MLflow (optionnel, ici on utilise SQLite)

### Prefect

**Rôle** : Orchestrateur de workflows

**Configuration** :
- Image de base : `prefecthq/prefect:3.0.3-python3.11`
- Port : `4200` (UI)
- Volumes : 
  - Scripts de flows dans `services/prefect/`
  - Données dans `data/`
  - Repository Feast dans `services/feast_repo/repo/`
  - Rapports dans `reports/`

**Flows typiques** :
1. **Ingestion** : Charger et valider les données
2. **Training** : Entraîner les modèles
3. **Monitoring** : Détecter le drift et générer des rapports

### Feast

**Rôle** : Feature Store centralisé

**Configuration** :
- Repository dans `services/feast_repo/repo/`
- Configuration dans `feature_store.yaml`
- Feature views dans `feature_views.py`
- Sources de données dans `data_sources.py`

**Modes d'utilisation** :
- **Offline** : Pour l'entraînement (historical features)
- **Online** : Pour les prédictions en temps réel

### MLflow

**Rôle** : Gestion du cycle de vie des modèles

**Configuration** :
- Image : `ghcr.io/mlflow/mlflow:v2.16.0`
- Port : `5000`
- Backend store : SQLite (ou PostgreSQL)
- Artifact store : `mlartifacts/`

**Fonctionnalités** :
- Tracking des expériences
- Registry de modèles
- Déploiement de modèles

### FastAPI

**Rôle** : API de prédiction en production

**Configuration** :
- Port : `8000`
- Hot reload : volume monté pour développement
- Métriques Prometheus : endpoint `/metrics`

**Endpoints typiques** :
- `GET /health` : Health check
- `GET /metrics` : Métriques Prometheus
- `POST /predict` : Prédiction

### Prometheus

**Rôle** : Collecte de métriques

**Configuration** :
- Image : `prom/prometheus:v2.55.1`
- Port : `9090`
- Configuration : `services/prometheus/prometheus.yml`

**Métriques collectées** :
- Nombre de requêtes (Counter)
- Latence des requêtes (Histogram)
- Erreurs (Counter)

### Grafana

**Rôle** : Visualisation des métriques

**Configuration** :
- Image : `grafana/grafana:11.2.0`
- Port : `3001` (mappé depuis 3000)
- Provisioning automatique dans `services/grafana/provisioning/`

**Dashboards** :
- RPS (Requêtes par seconde)
- Latence moyenne
- Taux d'erreur

### Evidently

**Rôle** : Détection de drift de données

**Configuration** :
- Utilisé dans les flows Prefect
- Génère des rapports HTML/JSON dans `reports/evidently/`

**Métriques** :
- Data drift (covariate drift)
- Target drift (concept drift)
- Data quality

---

## Bonnes pratiques

### 1. Gestion des versions

- Utiliser des tags Git pour marquer les versions importantes
- Documenter les changements dans les commits

### 2. Variables d'environnement

- Ne jamais commiter `.env`
- Utiliser des valeurs par défaut dans le code
- Documenter les variables nécessaires

### 3. Sécurité

- Utiliser des mots de passe forts pour PostgreSQL
- Ne pas exposer les services sensibles publiquement
- Utiliser des secrets management en production

### 4. Monitoring

- Configurer des alertes dans Grafana
- Surveiller les métriques de drift régulièrement
- Documenter les seuils d'alerte

### 5. Tests

- Tester les flows Prefect localement
- Tester l'API avec des données de test
- Valider les features Feast avant le déploiement

### 6. Documentation

- Documenter chaque flow Prefect
- Documenter les features Feast
- Maintenir un README à jour

---

## Commandes utiles

### Docker Compose

```bash
# Démarrer tous les services
docker compose up -d

# Arrêter tous les services
docker compose down

# Voir les logs
docker compose logs -f [service_name]

# Reconstruire un service
docker compose build [service_name]

# Redémarrer un service
docker compose restart [service_name]
```

### Prefect

```bash
# Exécuter un flow
docker compose exec prefect python /opt/prefect/flows/your_flow.py

# Voir les flows
docker compose exec prefect prefect flow ls
```

### Feast

```bash
# Appliquer les changements Feast
docker compose exec feast feast apply

# Matérialiser les features (online store)
docker compose exec feast feast materialize-incremental $(date -u +"%Y-%m-%dT%H:%M:%S")
```

### MLflow

```bash
# Lister les modèles
docker compose exec mlflow mlflow models list

# Charger un modèle
docker compose exec mlflow mlflow models serve -m "models:/your_model/Production"
```

---

## Dépannage

### Problèmes courants

1. **Port déjà utilisé** : Modifier les ports dans `docker-compose.yml`
2. **Connexion à PostgreSQL échoue** : Vérifier les variables d'environnement dans `.env`
3. **Feast ne trouve pas les features** : Vérifier que `feast apply` a été exécuté
4. **MLflow ne charge pas le modèle** : Vérifier que le modèle est enregistré et promu en Production
5. **Prometheus ne scrape pas l'API** : Vérifier que l'endpoint `/metrics` fonctionne

### Logs

```bash
# Logs de tous les services
docker compose logs

# Logs d'un service spécifique
docker compose logs api
docker compose logs prefect
docker compose logs postgres
```

---

## Ressources supplémentaires

- [Prefect Documentation](https://docs.prefect.io/)
- [Feast Documentation](https://docs.feast.dev/)
- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Evidently Documentation](https://docs.evidentlyai.com/)

---

## Conclusion

Cette architecture MLOps complète fournit :

✅ **Orchestration** avec Prefect  
✅ **Feature Store** avec Feast  
✅ **Model Registry** avec MLflow  
✅ **API de prédiction** avec FastAPI  
✅ **Monitoring** avec Prometheus et Grafana  
✅ **Drift Detection** avec Evidently  
✅ **Validation** avec Great Expectations  
✅ **Containerisation** avec Docker  

Cette structure est modulaire et peut être adaptée à différents projets ML en modifiant les configurations spécifiques à votre cas d'usage.

