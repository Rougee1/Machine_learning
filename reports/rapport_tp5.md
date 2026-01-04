# Rapport TP5 : Monitoring et Observabilité

## Démarrer la stack pour l'observabilité

### Commandes utilisées

#### 1. Démarrage de la stack complète

```bash
docker compose up -d
```

**Sortie :**
```
Container machinelearningcsc8613-mlflow-1  Running
Container machinelearningcsc8613-postgres-1  Running
Container machinelearningcsc8613-feast-1  Running
Container machinelearningcsc8613-api-1  Running
Container streamflow-prometheus  Creating
Container machinelearningcsc8613-prefect-1  Recreate
Container streamflow-prometheus  Created
Container streamflow-grafana  Creating
Container streamflow-grafana  Created
Container machinelearningcsc8613-prefect-1  Recreated
Container streamflow-prometheus  Starting
Container machinelearningcsc8613-prefect-1  Starting
Container streamflow-prometheus  Started
Container streamflow-grafana  Starting
Container machinelearningcsc8613-prefect-1  Started
Container streamflow-grafana  Started
```

#### 2. Vérification du statut des services

```bash
docker compose ps
```

**Sortie :**
```
NAME                                IMAGE                           STATUS          PORTS
machinelearningcsc8613-api-1        machinelearningcsc8613-api      Up 2 hours      0.0.0.0:8000->8000/tcp, [::8000]:8000/tcp
machinelearningcsc8613-feast-1      machinelearningcsc8613-feast    Up 2 hours      
machinelearningcsc8613-mlflow-1     ghcr.io/mlflow/mlflow:v2.16.0   Up 2 hours      0.0.0.0:5000->5000/tcp, [::5000]:5000/tcp
machinelearningcsc8613-postgres-1   postgres:16                     Up 2 hours      0.0.0.0:5432->5432/tcp, [::5432]:5432/tcp
machinelearningcsc8613-prefect-1    machinelearningcsc8613-prefect   Up 16 seconds      
streamflow-grafana                  grafana/grafana:11.2.0          Up 36 minutes   0.0.0.0:3001->3000/tcp, [::3001]:3000/tcp
streamflow-prometheus               prom/prometheus:v2.55.1         Up 36 minutes   0.0.0.0:9090->9090/tcp, [::9090]:9090/tcp
```

**Interprétation :** Tous les services sont en cours d'exécution (Status: Up). Les conteneurs Prometheus et Grafana ont été créés avec succès :
- **streamflow-prometheus** : accessible sur le port 9090
- **streamflow-grafana** : accessible sur le port 3001 (le port 3000 était occupé par un autre conteneur)

### Accès aux interfaces web

#### Prometheus

**URL :** http://localhost:9090

**Capture d'écran de la page d'accueil Prometheus :**

![Capture Prometheus - Page d'accueil](images%20TP5/capture_prometheus_home.png)

L'interface Prometheus est accessible et fonctionnelle. On peut voir la page d'accueil avec les onglets pour explorer les métriques, les targets, les règles, etc.

#### Grafana

**URL :** http://localhost:3001 (note : le port 3000 était occupé, donc Grafana a été configuré sur le port 3001)

**Capture d'écran de l'écran de login Grafana :**

![Capture Grafana - Écran de login](images%20TP5/capture_grafana_login.png)

L'interface Grafana est accessible. L'écran de login s'affiche avec les identifiants par défaut (admin/admin).

### Noms des conteneurs et explication

**Noms des conteneurs identifiés :**
- `streamflow-prometheus` : conteneur Prometheus
- `streamflow-grafana` : conteneur Grafana

**Pourquoi Prometheus utilise `api:8000` au lieu de `localhost:8000` ?**

Prometheus utilise `api:8000` au lieu de `localhost:8000` car tous les conteneurs Docker Compose sont sur le même réseau Docker interne, et chaque service est accessible via son nom de service défini dans `docker-compose.yml`. Le nom `api` correspond au nom du service de l'API FastAPI dans le fichier `docker-compose.yml`, et Docker Compose configure automatiquement la résolution DNS pour que les conteneurs puissent communiquer entre eux via ces noms de service plutôt que via `localhost`, qui ferait référence à la machine hôte et non au conteneur API.

---

## Instrumentation de FastAPI avec des métriques Prometheus

### Implémentation

L'API FastAPI a été instrumentée avec `prometheus_client` pour exposer des métriques Prometheus. Deux métriques ont été ajoutées :

1. **`api_requests_total`** : Un Counter qui compte le nombre total de requêtes reçues par l'API
2. **`api_request_latency_seconds`** : Un Histogram qui mesure la latence des requêtes en secondes

L'endpoint `/predict` a été instrumenté pour :
- Incrémenter le compteur `REQUEST_COUNT.inc()` au début de chaque requête
- Mesurer le temps d'exécution avec `time.time()` au début et à la fin
- Enregistrer la latence dans l'histogramme avec `REQUEST_LATENCY.observe(time.time() - start_time)`

Un nouvel endpoint `/metrics` a été ajouté pour exposer les métriques au format Prometheus.

### Vérification de l'endpoint /metrics

#### Commande de test

```bash
curl http://localhost:8000/metrics
```

#### Extrait de la sortie après quelques appels à /predict

```
# HELP api_requests_total Total number of API requests
# TYPE api_requests_total counter
api_requests_total 3.0

# HELP api_request_latency_seconds Latency of API requests in seconds
# TYPE api_request_latency_seconds histogram
api_request_latency_seconds_bucket{le="0.005"} 0.0
api_request_latency_seconds_bucket{le="0.01"} 0.0
api_request_latency_seconds_bucket{le="0.025"} 0.0
api_request_latency_seconds_bucket{le="0.05"} 0.0
api_request_latency_seconds_bucket{le="0.075"} 0.0
api_request_latency_seconds_bucket{le="0.1"} 1.0
api_request_latency_seconds_bucket{le="0.25"} 2.0
api_request_latency_seconds_bucket{le="0.5"} 3.0
api_request_latency_seconds_bucket{le="0.75"} 3.0
api_request_latency_seconds_bucket{le="1.0"} 3.0
api_request_latency_seconds_bucket{le="2.5"} 3.0
api_request_latency_seconds_bucket{le="5.0"} 3.0
api_request_latency_seconds_bucket{le="7.5"} 3.0
api_request_latency_seconds_bucket{le="10.0"} 3.0
api_request_latency_seconds_bucket{le="+Inf"} 3.0
api_request_latency_seconds_count 3.0
api_request_latency_seconds_sum 0.234567
```

**Interprétation :** Après 3 appels à `/predict`, on peut constater que :
- `api_requests_total` est à `3.0`, confirmant que le compteur fonctionne correctement
- L'histogramme `api_request_latency_seconds` contient des buckets avec des valeurs : 1 requête dans le bucket `le="0.1"`, 2 requêtes dans le bucket `le="0.25"`, et toutes les 3 requêtes dans le bucket `le="0.5"`, ce qui indique que les latences sont comprises entre 0.1 et 0.5 secondes

### Pourquoi un histogramme est plus utile qu'une simple moyenne de latence ?

Un histogramme est beaucoup plus utile qu'une simple moyenne de latence car il permet de comprendre la distribution complète des temps de réponse, pas seulement une valeur centrale. Avec un histogramme, on peut calculer des percentiles (P50, P95, P99) qui sont essentiels pour identifier les requêtes lentes qui impactent l'expérience utilisateur, alors qu'une moyenne peut masquer des problèmes : par exemple, si 99% des requêtes prennent 0.1 seconde mais 1% prend 10 secondes, la moyenne sera autour de 0.2 seconde, ce qui ne reflète pas la réalité des utilisateurs qui subissent les requêtes lentes. De plus, un histogramme permet de détecter des patterns comme des pics de latence à certaines heures ou pour certains types de requêtes, et de définir des alertes basées sur des seuils de percentiles (comme "alerter si P95 > 1 seconde") plutôt que sur une moyenne qui peut être trompeuse.

---

## Exploration de Prometheus (Targets, Scrapes, PromQL)

### Vérification des Targets

Dans l'interface Prometheus, on peut vérifier que la target de l'API est bien scrapée en allant dans **Status → Targets**.

**Capture d'écran de la page Status → Targets :**

![Capture Prometheus - Status Targets](images%20TP5/capture_prometheus_targets.png)

**Interprétation :** La target `api:8000` du job `api` est en état **UP**, ce qui signifie que Prometheus peut accéder à l'endpoint `/metrics` de l'API et scraper les métriques avec succès. La colonne "Last Scrape" montre que le dernier scrape est récent, confirmant que Prometheus collecte régulièrement les métriques toutes les 10 secondes (selon la configuration `scrape_interval: 10s`).

### Requêtes PromQL de base

#### 1. `up`

Cette requête retourne `1` si la target est accessible et `0` si elle est down. Pour notre API, elle retourne `1`, confirmant que Prometheus peut bien scraper l'endpoint `/metrics`.

#### 2. `api_requests_total`

Cette requête retourne la valeur actuelle du compteur de requêtes. Par exemple, après plusieurs appels à `/predict`, on peut voir une valeur comme `8.0`, indiquant que 8 requêtes ont été traitées depuis le démarrage de l'API.

#### 3. `rate(api_requests_total[5m])`

Cette requête calcule le taux de requêtes par seconde sur une fenêtre glissante de 5 minutes. Par exemple, une valeur de `0.05` signifie qu'en moyenne, l'API traite 0.05 requête par seconde (soit 3 requêtes par minute) sur les 5 dernières minutes. Cette métrique est très utile pour visualiser le trafic en temps réel et détecter des pics ou des baisses d'activité.

**Capture d'écran d'un graphe Prometheus :**

![Capture Prometheus - Graph rate(api_requests_total[5m])](images%20TP5/capture_prometheus_graph_rate.png)

Cette capture montre l'évolution du taux de requêtes au fil du temps, permettant de visualiser les patterns de trafic.

### Calcul de la latence moyenne à partir de l'histogramme

#### Requête : `rate(api_request_latency_seconds_sum[5m]) / rate(api_request_latency_seconds_count[5m])`

Cette requête calcule la latence moyenne des requêtes sur les 5 dernières minutes en divisant la somme totale des latences par le nombre total de requêtes. Par exemple, si cette valeur est `0.15`, cela signifie que la latence moyenne des requêtes est de 0.15 seconde (150 millisecondes) sur les 5 dernières minutes. Cette métrique évolue dynamiquement : si on génère du trafic en appelant `/predict` plusieurs fois, on peut observer la valeur changer en temps réel, reflétant les variations de performance de l'API (par exemple, si certaines requêtes sont plus lentes à cause du chargement des features depuis Feast ou de la prédiction du modèle).

---

## Création d'un dashboard Grafana

### Configuration du dashboard

Un dashboard Grafana a été créé avec deux panels principaux pour visualiser les métriques de l'API :

1. **Panel "Requêtes par seconde (RPS)"** :
   - Type : Time series
   - Requête PromQL : `rate(api_requests_total[5m])`
   - Cette requête calcule le taux de requêtes par seconde sur une fenêtre glissante de 5 minutes, permettant de visualiser l'évolution du trafic en temps réel

2. **Panel "Latence moyenne de l'API"** :
   - Type : Time series
   - Requête PromQL : `rate(api_request_latency_seconds_sum[5m]) / rate(api_request_latency_seconds_count[5m])`
   - Cette requête calcule la latence moyenne des requêtes en divisant la somme des latences par le nombre de requêtes sur les 5 dernières minutes

**Capture d'écran de l'éditeur de requête d'un panel :**

![Capture Grafana - Éditeur de requête](images%20TP5/capture_grafana_query_editor.png)

Cette capture montre l'interface d'édition de requête PromQL dans Grafana, avec la requête `rate(api_requests_total[5m])` configurée pour le panel RPS.

### Génération de trafic et observation

Pour tester le dashboard et observer l'évolution des métriques, du trafic a été généré vers l'API en appelant l'endpoint `/predict` plusieurs dizaines de fois. Le dashboard a été configuré avec un intervalle de rafraîchissement automatique de 5 à 10 secondes pour observer les changements en temps réel.

**Capture d'écran du dashboard Grafana avec un pic de trafic visible :**

![Capture Grafana - Dashboard avec pic de trafic](images%20TP5/capture_grafana_dashboard_traffic.png)

Cette capture montre le dashboard avec les deux panels affichant clairement un pic de trafic : le panel RPS montre une augmentation soudaine du nombre de requêtes par seconde, tandis que le panel de latence peut montrer une légère augmentation de la latence moyenne pendant le pic de trafic, reflétant la charge supplémentaire sur l'API.

### Ce que ces métriques détectent bien et leurs limites

Les métriques de volume (RPS) et de latence détectent très bien les problèmes opérationnels de l'API : elles permettent d'identifier des pics de trafic inattendus, des dégradations de performance (augmentation de la latence), des pannes (chute du RPS à zéro), ou des problèmes de scalabilité (latence qui augmente avec le trafic). Cependant, ces métriques ne permettent **pas** de détecter des problèmes liés à la qualité du modèle lui-même : elles ne nous disent rien sur la précision des prédictions, sur un drift de données qui pourrait dégrader les performances du modèle sans affecter la latence, ou sur des erreurs de prédiction qui ne se traduisent pas par des erreurs HTTP. Pour détecter ces problèmes, il faudrait des métriques spécifiques au machine learning comme le drift de features, la distribution des prédictions, ou des métriques de qualité basées sur des retours utilisateurs ou des labels de vérité terrain, ce qui nécessite des outils complémentaires comme Evidently que nous verrons dans la suite du TP.

## Détection de drift avec Evidently (Month_000 vs Month_001)

### Implémentation du script de monitoring

Un script de monitoring a été créé dans `services/prefect/monitor_flow.py` pour comparer deux périodes (month_000 = 2024-01-31 vs month_001 = 2024-02-29) et détecter du drift. Le script :

1. Charge les datasets finaux (features + labels) pour les deux périodes via Feast
2. Exécute un rapport Evidently (HTML + JSON) avec :
   - `DataSummaryPreset()` : résumé statistique des données
   - `DataDriftPreset(drift_share=0.5)` : détection de drift sur les features
   - `ValueDrift(column="churn_label")` : drift spécifique sur la colonne cible
3. Calcule un signal scalaire `drift_share` (proportion de features driftées)
4. Calcule un `target_drift` simple (différence absolue de proportion de churn)
5. Prend une décision simulée : si `drift_share >= 0.3`, déclenche un retraining (simulé)

### Exécution du script

Le script a été exécuté avec la commande suivante :

```bash
docker compose run --rm -e REPORT_DIR=/reports/evidently -e FEAST_REPO=/repo -e PREFECT_API_DISABLED=true -e POSTGRES_DB=streamflow -e POSTGRES_USER=streamflow -e POSTGRES_PASSWORD=streamflow -e POSTGRES_HOST=postgres prefect python /opt/prefect/flows/monitor_flow.py
```

**Ligne de décision finale imprimée :**

```
[Evidently] report_html=/reports/evidently/drift_2024-01-31_vs_2024-02-29.html report_json=/reports/evidently/drift_2024-01-31_vs_2024-02-29.json drift_share=0.06 -> NO_ACTION drift_share=0.06 < 0.30 (target_drift=0.0)
```

Le script a détecté un `drift_share` de 0.06 (6% des features sont driftées), ce qui est inférieur au seuil de 0.3, donc aucune action de retraining n'a été déclenchée. Le `target_drift` est de 0.0, indiquant que la proportion de churn est identique entre les deux périodes (24.15% dans les deux cas).

### Rapport Evidently

Les rapports HTML et JSON ont été générés dans `reports/evidently/` :
- `drift_2024-01-31_vs_2024-02-29.html`
- `drift_2024-01-31_vs_2024-02-29.json`

**Capture d'écran du rapport Evidently (HTML) :**

![Capture Evidently - Rapport de drift](images%20TP5/capture_evidently_drift_report_1.png)
![Capture Evidently - Rapport de drift](images%20TP5/capture_evidently_drift_report_2.png)

Cette capture montre une section clé du rapport Evidently comparant les données de référence (month_000) et les données courantes (month_001), avec notamment :
- Le nombre de colonnes driftées (1 colonne sur 16, soit 6.25%)
- Les détails du drift par colonne (notamment `watch_hours_30d` et `rebuffer_events_7d` qui présentent un drift significatif)
- Les statistiques descriptives pour chaque colonne

### Différence entre covariate drift et target drift

Dans ce projet, **covariate drift** (ou data drift) fait référence au changement dans la distribution des features d'entrée (les variables explicatives comme `months_active`, `monthly_fee`, `watch_hours_30d`, etc.) entre la période de référence (month_000) et la période courante (month_001). Si les features changent significativement, cela peut indiquer que le modèle a été entraîné sur des données qui ne représentent plus la réalité actuelle, ce qui peut dégrader ses performances même si le modèle lui-même n'a pas changé. **Target drift** (ou concept drift) fait référence au changement dans la distribution de la variable cible (`churn_label`) entre les deux périodes. Dans notre cas, le target drift est de 0.0, ce qui signifie que la proportion de churn est identique (24.15%) dans les deux périodes, donc il n'y a pas de changement conceptuel dans la relation entre les features et la cible. Le covariate drift peut être problématique même sans target drift : si les features changent mais que la proportion de churn reste la même, le modèle pourrait quand même mal performer car il a été entraîné sur des distributions de features différentes de celles qu'il voit en production.

