# Contexte

Dans le cadre du projet StreamFlow, nous disposons déjà d'un pipeline d'ingestion de données qui a permis de charger et valider les données issues des fichiers CSV pour deux périodes (month_000 et month_001), créant ainsi des snapshots mensuels dans PostgreSQL. Ces données incluent les tables utilisateurs, d'usage (usage_agg_30d), d'abonnements (subscriptions), de paiements (payments_agg_90d) et de support (support_agg_90d), toutes validées et figées dans le temps grâce aux snapshots créés lors du TP2. L'objectif du TP3 est de brancher ces données au Feature Store Feast, qui permettra de centraliser et gérer les features utilisées pour l'entraînement et la prédiction du modèle de churn. Nous apprendrons à récupérer des features en mode offline (pour l'entraînement) et en mode online (pour les prédictions en temps réel), puis à exposer un endpoint API simple qui utilise ces features pour servir des prédictions, constituant ainsi la base de l'infrastructure de production pour le modèle de machine learning.

# Mise en place de Feast

Pour démarrer les services, j'utilise la commande suivante :

```bash
docker compose up -d
```

Le conteneur `feast` contient le Feature Store Feast et sa configuration se trouve dans `/repo/feature_store.yaml` (correspondant au montage du dossier `./services/feast_repo/repo`). Ce conteneur permet d'exécuter les commandes Feast pour gérer le Feature Store : nous l'utiliserons via `docker compose exec feast feast apply` pour appliquer les définitions de features et `docker compose exec feast feast materialize` pour matérialiser les features dans le online store.

# Définition du Feature Store

Dans Feast, une Entity représente une entité métier pour laquelle on définit des features. C'est l'objet principal autour duquel sont organisées les features (par exemple, un utilisateur, une transaction, un produit). L'Entity définit les clés de jointure (join_keys) qui permettent de relier différentes sources de données et features à cette entité. Dans le contexte de StreamFlow, user_id est un excellent choix de clé de jointure car c'est l'identifiant unique qui permet de relier toutes les données d'un même utilisateur : ses informations démographiques (users), son abonnement (subscriptions), son utilisation (usage_agg_30d), ses paiements (payments_agg_90d) et son historique de support (support_agg_90d). Cette clé commune traverse toutes nos tables et permet de construire un profil complet de chaque utilisateur pour la prédiction du churn.

Les DataSources PostgreSQL sont configurées pour lire les tables de snapshots. Par exemple, la table `usage_agg_30d_snapshots` contient les colonnes de features suivantes : `watch_hours_30d`, `avg_session_mins_7d`, `unique_devices_30d`, `skips_7d`, et `rebuffer_events_7d`.

La commande `feast apply` permet de valider et enregistrer les définitions du Feature Store (entities, data sources, feature views) dans le registry. Elle vérifie la cohérence des schémas et crée les structures nécessaires dans le online store si elles n'existent pas déjà. C'est l'étape nécessaire avant de pouvoir utiliser le Feature Store pour récupérer des features.

# Récupération offline & online

Pour créer le dataset d'entraînement, j'utilise la commande suivante :

```bash
docker compose exec prefect python build_training_dataset.py
```

Cette commande exécute le script qui construit un entity_df à partir des snapshots, récupère les features via Feast, et joint les labels pour créer le fichier `training_df.csv`.

Les 5 premières lignes du fichier généré (7043 lignes au total) :

```
user_id,event_timestamp,months_active,monthly_fee,paperless_billing,watch_hours_30d,avg_session_mins_7d,failed_payments_90d,churn_label
5698-BQJOH,2024-01-31,9,94.4,False,31.2634920174866,29.141044640845102,0,False
5122-CYFXA,2024-01-31,3,75.3,True,30.3140201359775,29.141044640845102,0,False
8627-ZYGSZ,2024-01-31,47,78.9,True,36.328819360502,29.141044640845102,0,False
3410-YOQBQ,2024-01-31,31,79.2,False,37.6061100372707,29.141044640845102,1,False
```

**Temporal correctness (point-in-time correctness) :**

Feast garantit la temporal correctness lors de la récupération offline grâce au champ `timestamp_field = "as_of"` défini dans chaque DataSource, qui indique à Feast quelle colonne utiliser comme référence temporelle dans les snapshots. L'entity_df contient à la fois `user_id` et `event_timestamp` (dérivée de `as_of`), ce qui permet à Feast de récupérer uniquement les features qui étaient disponibles à cette date précise (2024-01-31). Ainsi, lors du join entre entity_df et les snapshots, Feast s'assure que seules les données figées à cette date sont utilisées, évitant ainsi tout risque de data leakage en utilisant des informations du futur.

**Récupération online :**

Pour tester la récupération de features en ligne, j'ai exécuté le script `debug_online_features.py` qui utilise `get_online_features`. Voici le dictionnaire retourné pour l'utilisateur `7590-VHVEG` :

```python
{'user_id': ['7590-VHVEG'], 'months_active': [1], 'paperless_billing': [True], 'monthly_fee': [29.850000381469727]}
```

Si on interroge un `user_id` qui n'a pas de features matérialisées (par exemple un utilisateur inexistant ou qui se trouve en dehors de la fenêtre de matérialisation), Feast retournera des valeurs `None` ou des valeurs par défaut pour les features demandées, ce qui permet à l'API de gérer gracieusement ce cas sans lever d'erreur.

**Test de l'endpoint API :**

Après avoir démarré le service API avec `docker compose up -d api`, j'ai testé l'endpoint `/features/{user_id}` pour l'utilisateur `7590-VHVEG`. Voici la réponse JSON obtenue :

```json
{
  "user_id": "7590-VHVEG",
  "features": {
    "user_id": "7590-VHVEG",
    "monthly_fee": 29.850000381469727,
    "months_active": 1,
    "paperless_billing": true
  }
}
```

L'API récupère correctement les features depuis le online store Feast et les retourne dans le format attendu.

# Réflexion

**En quoi ce endpoint /features/{user_id}, basé sur Feast, nous aide-t-il à réduire le training-serving skew dans un système de ML en production ?**

L'endpoint `/features/{user_id}` basé sur Feast permet de réduire le training-serving skew car il utilise exactement les mêmes FeatureViews (définitions de features) que celles utilisées lors de la construction du dataset d'entraînement via `get_historical_features`. En centralisant la logique de transformation des features dans Feast, on garantit que les features récupérées en production sont calculées de la même manière qu'à l'entraînement, évitant ainsi les écarts qui pourraient survenir si le code de transformation était dupliqué entre les deux environnements. Cette cohérence entre offline (entraînement) et online (serving) assure que le modèle reçoit des features dans le même format et avec les mêmes valeurs, ce qui est essentiel pour maintenir les performances du modèle en production.

## Tag Git

Le dépôt a été tagué avec `tp3` à la fin de ce TP pour marquer l'état du projet après l'intégration du Feature Store Feast et de l'API. Cela permet de revenir facilement à cet état dans les TP suivants si nécessaire.

Commandes utilisées :
```bash
git tag -a tp3 -m "Fin du TP3 - Feature Store et API"
git push origin tp3
``` 