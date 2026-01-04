# Rapport TP4 : Chaîne MLOps End-to-End avec MLflow

## Mise en route + rappel de contexte

### Commandes utilisées

#### 1. Démarrage de la stack Docker Compose

```bash
docker compose up -d
```

#### 2. Vérification du statut des conteneurs

```bash
docker compose ps
```

**Sortie :**
```
NAME                                IMAGE                            COMMAND                  SERVICE    CREATED          STATUS         PORTS                  
machinelearningcsc8613-api-1        machinelearningcsc8613-api       "uvicorn app:app --h…"   api        7 seconds ago    Up 5 seconds   0.0.0.0:8000->8000/tcp
machinelearningcsc8613-feast-1      machinelearningcsc8613-feast     "bash -lc 'tail -f /…"   feast      7 seconds ago    Up 6 seconds                          
machinelearningcsc8613-mlflow-1     ghcr.io/mlflow/mlflow:v2.16.0    "mlflow server --bac…"   mlflow     10 seconds ago   Up 6 seconds   0.0.0.0:5000->5000/tcp
machinelearningcsc8613-postgres-1   postgres:16                      "docker-entrypoint.s…"   postgres   10 seconds ago   Up 6 seconds   0.0.0.0:5432->5432/tcp
machinelearningcsc8613-prefect-1    machinelearningcsc8613-prefect   "/usr/bin/tini -g --…"   prefect    7 seconds ago    Up 6 seconds
```

#### 3. Vérification de l'accessibilité de MLflow UI (localhost:5000)

```powershell
Invoke-WebRequest -Uri http://localhost:5000 -UseBasicParsing | Select-Object StatusCode
```

**Sortie :**
```
StatusCode
----------
       200
```

**Preuve d'accessibilité :** MLflow UI est accessible sur http://localhost:5000 (Code HTTP 200, Content-Type: text/html; charset=utf-8)

#### 4. Vérification de l'endpoint API /health (localhost:8000)

```powershell
Invoke-WebRequest -Uri http://localhost:8000/health -UseBasicParsing | ConvertFrom-Json
```

**Sortie :**
```
status
------
ok
```

**Preuve d'accessibilité :** L'API répond correctement avec `{"status": "ok"}` (Code HTTP 200)

#### 5. Smoke check : récupération de features online via /features/{user_id}

```powershell
Invoke-WebRequest -Uri http://localhost:8000/features/7590-VHVEG -UseBasicParsing | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

**Sortie :**
```json
{
    "user_id":  "7590-VHVEG",
    "features":  {
                     "user_id":  "7590-VHVEG",
                     "monthly_fee":  29.850000381469727,
                     "months_active":  1,
                     "paperless_billing":  true
                 }
}
```

**Preuve d'accessibilité :** L'endpoint `/features/{user_id}` fonctionne correctement et récupère les features depuis Feast (Code HTTP 200)

#### 6. Vérification des logs MLflow

```bash
docker compose logs --tail=10 mlflow
```

**Sortie :**
```
mlflow-1  | INFO  [alembic.runtime.migration] Running upgrade 5b0e9adcef9c -> 4465047574b1, increase max dataset schema size
mlflow-1  | INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
mlflow-1  | INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
mlflow-1  | [2025-12-29 08:41:37 +0000] [27] [INFO] Starting gunicorn 23.0.0
mlflow-1  | [2025-12-29 08:41:37 +0000] [27] [INFO] Listening at: http://0.0.0.0:5000 (27)
mlflow-1  | [2025-12-29 08:41:37 +0000] [27] [INFO] Using worker: sync
mlflow-1  | [2025-12-29 08:41:37 +0000] [28] [INFO] Booting worker with pid: 28
mlflow-1  | [2025-12-29 08:41:37 +0000] [29] [INFO] Booting worker with pid: 29
mlflow-1  | [2025-12-29 08:41:37 +0000] [30] [INFO] Booting worker with pid: 30
mlflow-1  | [2025-12-29 08:41:37 +0000] [31] [INFO] Booting worker with pid: 31
```

**Preuve d'accessibilité :** MLflow server est démarré et écoute sur le port 5000 avec 4 workers

---

### Quels composants tournent et pourquoi

La stack Docker Compose exécute cinq services principaux qui forment une infrastructure MLOps complète. **PostgreSQL** (postgres) sert de base de données centralisée pour stocker les données brutes, les snapshots temporels créés lors du TP2, et les features matérialisées par Feast dans l'online store. **Prefect** (prefect) orchestre les pipelines de données et d'entraînement, permettant l'exécution automatisée et traçable des workflows d'ingestion et de préparation des données. **Feast** (feast) gère le Feature Store qui centralise la logique de transformation des features, garantissant la cohérence entre l'entraînement (offline) et la production (online), évitant ainsi le training-serving skew. **MLflow** (mlflow), ajouté dans ce TP, fournit le tracking des expériences d'entraînement et le Model Registry pour gérer le cycle de vie des modèles avec des stages (Staging, Production), permettant un déploiement contrôlé et traçable. Enfin, **l'API FastAPI** (api) expose les endpoints de prédiction en production, récupérant les features depuis Feast et servant les modèles enregistrés dans MLflow, constituant l'interface finale pour les prédictions en temps réel. Ensemble, ces composants forment une chaîne MLOps end-to-end, de la gestion des données jusqu'au serving en production, avec une traçabilité complète grâce à MLflow.

---

## Créer un script d'entraînement + tracking MLflow (baseline RandomForest)

### Résultats de l'entraînement

#### Informations sur le dataset et l'entraînement

- **AS_OF utilisé** : `2024-01-31` (correspond au snapshot `month_000`)
- **Nombre de lignes du dataset d'entraînement (après merge)** : **7043 lignes**
- **Colonnes catégorielles détectées (cat_cols)** : `['net_service']`
- **Métriques calculées (sur validation)** :
  - **AUC** (Area Under ROC Curve) : **0.6163**
  - **F1** (F1-Score) : **0.0687**
  - **ACC** (Accuracy) : **0.7535**
- **Temps d'entraînement** : **0.73 secondes**

**Sortie complète du script :**
```
[INFO] Dataset: 7043 rows after merge
[INFO] Categorical columns: ['net_service']
[INFO] Training time: 0.73 seconds
[OK] Trained baseline RF. AUC=0.6163 F1=0.0687 ACC=0.7535 (run_id=71f878e8af12419597321c4963c1dc8d)
```

### Reproductibilité : Pourquoi fixer AS_OF et random_state ?

Dans un pipeline MLOps orienté reproductibilité, fixer **AS_OF** et **random_state** est essentiel pour garantir la reproductibilité des résultats. **AS_OF** (fixé à `2024-01-31` dans notre cas) permet de s'assurer que tous les entraînements utilisent exactement les mêmes snapshots de données à un point temporel donné. Cela évite le data leakage en utilisant uniquement les données disponibles jusqu'à cette date, et garantit que si on réexécute l'entraînement plusieurs fois, on utilise toujours les mêmes données d'entraînement. **random_state** (fixé à `42` pour le RandomForest et pour `train_test_split`) garantit que le hasard introduit par l'algorithme (initialisation, split train/val) produit toujours les mêmes résultats. Sans ces valeurs fixes, chaque exécution produirait un modèle différent et des métriques différentes, rendant impossible la comparaison entre différents runs et la reproductibilité des expériences. Ces pratiques sont fondamentales pour un pipeline MLOps fiable et débuggable.

---

## Explorer l'interface MLflow et promouvoir un modèle

### Capture de l'UI MLflow montrant le run (métriques + artefacts)

La capture d'écran suivante montre l'interface MLflow avec les métriques, paramètres et artefacts enregistrés pour le run d'entraînement :

![Capture UI MLflow - Métriques et paramètres](images%20TP4/capture_UIMLFlow_metrique_parametres.png)

![Capture UI MLflow - Artifacts](images%20TP4/capture_UIMLFlow_Artifacts.png)

Ces captures montrent :
- **Métriques** : AUC (0.6163), F1 (0.0687), Accuracy (0.7535), train_time_seconds
- **Paramètres** : as_of (2024-01-31), model_type (RandomForest), n_estimators (300), random_state (42)
- **Artefacts** : `feature_schema.json` (décrivant les colonnes catégorielles et numériques) et le dossier `model/` contenant le modèle entraîné

### Capture du Model Registry avec le modèle en Production

La capture suivante montre le Model Registry avec le modèle `streamflow_churn` promu en Production :

![Capture Model Registry - Modèle en Production](images%20TP4/capture_modele_prod.png)

### Numéro de version promu

**Version promue en Production :** **Version 4** du modèle `streamflow_churn`

Le modèle a été promu en Production via l'interface MLflow en modifiant le Stage de "None" à "Production" dans le Model Registry. Cette promotion permet à l'API de charger automatiquement cette version spécifique lors du démarrage, garantissant que les prédictions en production utilisent le modèle validé et approuvé.

### Pourquoi la promotion via interface (stages) est préférable au déploiement manuel

La promotion via une interface avec des stages (None, Staging, Production) est préférable à un déploiement manuel basé sur des fichiers ou des chemins locaux pour plusieurs raisons fondamentales. Premièrement, elle garantit la traçabilité et l'auditabilité : chaque changement de stage est enregistré avec l'utilisateur responsable et l'horodatage, permettant de suivre qui a déployé quoi et quand. Deuxièmement, elle évite les erreurs humaines : pas besoin de copier des fichiers manuellement, de mettre à jour des chemins dans le code, ou de risquer d'utiliser une mauvaise version du modèle. Troisièmement, elle centralise la gestion du cycle de vie : toutes les versions du modèle sont accessibles depuis un seul endroit, et le passage de Staging à Production se fait en un clic, facilitant les rollbacks si nécessaire. Quatrièmement, elle assure la cohérence : l'API charge toujours le modèle via `models:/streamflow_churn/Production`, indépendamment du numéro de version sous-jacent, évitant les problèmes de synchronisation entre les environnements. Enfin, elle permet un workflow de validation contrôlé : les modèles peuvent être testés en Staging avant d'être promus en Production, réduisant les risques de déploiement de modèles non validés.

---

## Étendre l'API pour exposer /predict (serving minimal end-to-end)

### Requête réussie vers l'endpoint /predict

#### Commande PowerShell utilisée

```powershell
$body = @{user_id='7590-VHVEG'} | ConvertTo-Json
Invoke-RestMethod -Uri http://localhost:8000/predict -Method POST -Body $body -ContentType "application/json" | ConvertTo-Json -Depth 10
```

#### Réponse JSON obtenue

```json
{
    "user_id":  "7590-VHVEG",
    "prediction":  0,
    "features_used":  {
                          "monthly_fee":  29.850000381469727,
                          "paperless_billing":  true,
                          "plan_stream_tv":  false,
                          "net_service":  "DSL",
                          "plan_stream_movies":  false,
                          "months_active":  1,
                          "avg_session_mins_7d":  29.14104461669922,
                          "unique_devices_30d":  3,
                          "watch_hours_30d":  24.48365020751953,
                          "rebuffer_events_7d":  1,
                          "skips_7d":  4,
                          "failed_payments_90d":  1,
                          "ticket_avg_resolution_hrs_90d":  16.0,
                          "support_tickets_90d":  0
                      }
}
```

**Interprétation :** L'endpoint `/predict` fonctionne correctement. Pour l'utilisateur `7590-VHVEG`, le modèle prédit **0** (pas de churn) avec toutes les features récupérées depuis Feast et utilisées pour la prédiction.

### Pourquoi utiliser `models:/streamflow_churn/Production` plutôt qu'un fichier local ou un artifact de run ?

Utiliser `models:/streamflow_churn/Production` plutôt qu'un fichier local (`.pkl`) ou un artifact de run (`runs:/<run_id>/model`) est essentiel pour un serving en production fiable et maintenable. Premièrement, cela garantit la **découplage entre l'entraînement et le déploiement** : l'API charge toujours le modèle "Production" actuel, indépendamment de quel run l'a généré, évitant de devoir modifier le code de l'API à chaque nouvel entraînement. Deuxièmement, cela permet un **déploiement sans interruption** : lorsqu'un nouveau modèle est promu en Production via le Model Registry, l'API peut recharger automatiquement le nouveau modèle sans changement de code ni redéploiement de l'application. Troisièmement, cela assure la **traçabilité et la gouvernance** : chaque modèle en Production est lié à un run MLflow spécifique avec toutes ses métriques, paramètres et artefacts, permettant de comprendre exactement quel modèle est servi et pourquoi. Quatrièmement, cela évite les **problèmes de synchronisation** : pas besoin de copier manuellement des fichiers entre les environnements ou de gérer des chemins de fichiers qui peuvent être différents entre dev, staging et production. Enfin, cela facilite les **rollbacks** : si un modèle en Production pose problème, on peut simplement promouvoir une version précédente en Production via l'interface MLflow, sans toucher au code de l'API.

---

## Robustesse du serving : cas d'échec réalistes (sans monitoring)

### Exemple de requête réussie

#### Commande PowerShell

```powershell
$body = @{user_id='7590-VHVEG'} | ConvertTo-Json
Invoke-RestMethod -Uri http://localhost:8000/predict -Method POST -Body $body -ContentType "application/json" | ConvertTo-Json -Depth 10
```

#### Réponse JSON (succès)

```json
{
    "user_id":  "7590-VHVEG",
    "prediction":  0,
    "features_used":  {
                          "monthly_fee":  29.850000381469727,
                          "paperless_billing":  true,
                          "plan_stream_tv":  false,
                          "net_service":  "DSL",
                          "plan_stream_movies":  false,
                          "months_active":  1,
                          "avg_session_mins_7d":  29.14104461669922,
                          "unique_devices_30d":  3,
                          "watch_hours_30d":  24.48365020751953,
                          "rebuffer_events_7d":  1,
                          "skips_7d":  4,
                          "failed_payments_90d":  1,
                          "ticket_avg_resolution_hrs_90d":  16.0,
                          "support_tickets_90d":  0
                      }
}
```

**Interprétation :** La requête réussit car l'utilisateur `7590-VHVEG` existe dans l'online store Feast et toutes ses features sont disponibles. Le modèle retourne une prédiction de **0** (pas de churn) avec toutes les features utilisées.

### Exemple de requête échouée

#### Commande PowerShell

```powershell
$body = @{user_id='999999'} | ConvertTo-Json
Invoke-RestMethod -Uri http://localhost:8000/predict -Method POST -Body $body -ContentType "application/json" | ConvertTo-Json -Depth 10
```

#### Réponse JSON (erreur)

```json
{
    "error":  "Missing features for user_id=999999",
    "missing_features":  [
                             "monthly_fee",
                             "paperless_billing",
                             "plan_stream_tv",
                             "net_service",
                             "plan_stream_movies",
                             "months_active",
                             "avg_session_mins_7d",
                             "unique_devices_30d",
                             "watch_hours_30d",
                             "rebuffer_events_7d",
                             "skips_7d",
                             "failed_payments_90d",
                             "ticket_avg_resolution_hrs_90d",
                             "support_tickets_90d"
                         ]
}
```

**Interprétation :** La requête échoue car l'utilisateur `999999` n'existe pas dans l'online store Feast. L'API détecte que toutes les features sont manquantes et retourne une erreur explicite avec la liste complète des `missing_features`, permettant de diagnostiquer rapidement le problème.

### Ce qui peut mal tourner en serving et comment on le détecte tôt

En production, la majorité des pannes "modèle" sont en réalité des pannes "features", et il est crucial de les détecter tôt pour éviter de servir des prédictions incorrectes ou de faire planter l'API. Deux causes principales peuvent être identifiées. Premièrement, **l'entité absente** : lorsque le `user_id` demandé n'est pas présent dans l'online store Feast, toutes les features retournent des valeurs nulles ou manquantes. L'API détecte ce cas en vérifiant `X.isnull().any().any()` après la récupération des features, et retourne immédiatement une erreur explicite avec la liste des `missing_features`, évitant ainsi de passer des données incomplètes au modèle qui produirait une prédiction non fiable. Deuxièmement, **l'online store incomplet ou obsolète (stale)** : même si l'entité existe, certaines features peuvent être manquantes si la matérialisation Feast n'a pas été exécutée récemment ou si certaines features n'ont pas été calculées pour cet utilisateur. Ce cas se traduit également par des valeurs nulles partielles, détectées par la même vérification. Pour détecter ces problèmes tôt, l'API implémente des **garde-fous minimaux** : validation des features manquantes avant l'appel au modèle, messages d'erreur explicites indiquant quelles features sont absentes, et retour d'un code HTTP 200 avec un objet d'erreur structuré plutôt qu'une exception non gérée. Ces mécanismes permettent de diagnostiquer rapidement les problèmes de données sans nécessiter de monitoring complexe, et évitent de servir des prédictions basées sur des données incomplètes qui pourraient être trompeuses pour les utilisateurs finaux.

---

## Réflexion de synthèse (ingénierie MLOps)

### Ce que MLflow garantit dans cette pipeline

Au niveau de la **traçabilité des entraînements**, MLflow garantit qu'on peut toujours savoir exactement comment un modèle a été entraîné, avec quelles données et quels paramètres, ce qui est vraiment important quand on veut comprendre pourquoi un modèle performe bien ou mal et pouvoir reproduire les résultats plus tard. Concrètement, chaque fois qu'on lance `train_baseline.py`, MLflow enregistre automatiquement tous les paramètres qu'on a utilisés (comme le `AS_OF`, le nombre d'estimateurs du RandomForest, le `random_state`), toutes les métriques qu'on a calculées (AUC, F1, accuracy), et même le schéma des features qu'on a utilisé, ce qui permet de comparer différents runs et de voir l'évolution des performances au fil du temps sans avoir à tout noter manuellement dans un fichier Excel ou un document.

Au niveau de l'**identification des modèles servis**, MLflow garantit qu'on sait toujours quel modèle exact est utilisé en production grâce au Model Registry et aux stages, ce qui évite les situations où on ne sait plus quelle version du modèle tourne sur le serveur. Quand l'API charge le modèle avec `models:/streamflow_churn/Production`, elle récupère automatiquement la version qui a été promue en Production dans le Model Registry, et on peut toujours remonter au run MLflow original pour voir toutes les métriques et paramètres de ce modèle, ce qui est essentiel pour le debugging et pour répondre aux questions du type "quel modèle est actuellement en production et comment a-t-il été entraîné".

### Ce que signifie concrètement le stage Production pour l'API

Le stage Production signifie que quand l'API démarre, elle va automatiquement charger le modèle qui est marqué comme "Production" dans le Model Registry, sans avoir besoin de spécifier un numéro de version ou un chemin de fichier précis, ce qui simplifie beaucoup le déploiement. Concrètement, au démarrage de l'API, le code fait `mlflow.pyfunc.load_model("models:/streamflow_churn/Production")` et MLflow va chercher dans son registry quelle version du modèle `streamflow_churn` a le stage "Production", puis il charge cette version-là, ce qui permet de changer le modèle en production simplement en changeant le stage dans l'interface MLflow sans toucher au code de l'API.

Côté déploiement, cela permet de faire des mises à jour de modèles de manière très contrôlée et traçable, parce qu'on peut d'abord tester un nouveau modèle en le mettant en stage "Staging", vérifier qu'il fonctionne bien, puis le promouvoir en "Production" quand on est sûr, et si jamais il y a un problème, on peut facilement faire un rollback en remettant l'ancien modèle en Production. Par contre, cela empêche de servir accidentellement un modèle qui n'a pas été validé, parce que seuls les modèles explicitement promus en Production peuvent être chargés par l'API, ce qui évite les erreurs humaines comme charger un mauvais fichier ou oublier de mettre à jour un chemin dans le code.

### Points où la reproductibilité peut encore casser dans ce système

Même avec MLflow qui trace les paramètres et les métriques, il y a encore plusieurs endroits où la reproductibilité peut casser dans notre système. Premièrement, au niveau des **données** : même si on fixe le `AS_OF` à `2024-01-31`, si les données dans PostgreSQL changent (par exemple si on réexécute un pipeline d'ingestion qui modifie les données historiques), les features récupérées par Feast pourront être différentes, ce qui donnera un modèle différent même avec les mêmes paramètres, et MLflow ne peut pas vraiment garantir que les données sous-jacentes n'ont pas changé entre deux runs.

Deuxièmement, au niveau du **code et des dépendances** : si on modifie le script `train_baseline.py` ou si les versions des bibliothèques Python changent (par exemple scikit-learn passe de la version 1.7.2 à une version plus récente avec des changements d'implémentation), le modèle entraîné peut être différent même avec les mêmes paramètres et les mêmes données, et MLflow enregistre bien les paramètres du modèle mais pas forcément les versions exactes de toutes les dépendances ou le code source complet du script d'entraînement.

Troisièmement, au niveau de l'**environnement et de la configuration** : si l'environnement d'exécution change (par exemple on passe d'un conteneur Docker avec Python 3.11 à un autre avec Python 3.12, ou si les variables d'environnement comme `MLFLOW_TRACKING_URI` pointent vers un serveur MLflow différent), les résultats peuvent varier, et même si MLflow stocke les paramètres du modèle, il ne garantit pas que l'environnement d'exécution soit identique entre deux runs, ce qui peut causer des différences subtiles dans les calculs numériques ou dans le comportement des bibliothèques.
