# Rapport TP2

## 1.c

![Capture 1.C](./Images%20TP2/1.C.png)

## 2.a

![Capture 2.A](./Images%20TP2/2.A.png)

## 2.b

Un fichier .env dans un projet Docker sert à définir et centraliser les variables d'environnement (comme les ports, mots de passe ou noms de services) afin de configurer les conteneurs sans modifier le code et de faciliter le déploiement selon les environnements (développement, test, production).

## 2.c

![Capture 2.C](./Images%20TP2/2.C.png)

## 2.d

![Capture 2.D](./Images%20TP2/2.D.png)

**Commentaires sur les tables du schéma :**

- **users** : Contient les informations démographiques de base des utilisateurs (date d'inscription, genre, âge senior, situation familiale).
- **subscriptions** : Stocke les détails des abonnements (plans, contrat, tarifs, options) pour chaque utilisateur.
- **usage_agg_30d** : Agrège les statistiques d'utilisation de chaque utilisateur sur 30 jours (heures de visionnage, appareils, interruptions).
- **payments_agg_90d** : Enregistre le nombre de paiements échoués par utilisateur sur une période de 90 jours.
- **support_agg_90d** : Contient les statistiques de support client (nombre de tickets, temps de résolution) agrégées sur 90 jours par utilisateur.
- **labels** : Stocke l'étiquette de churn (désabonnement) pour chaque utilisateur, utilisée pour l'entraînement du modèle de machine learning.

## 3.A

Le conteneur Prefect orchestre le pipeline d'ingestion des données en coordonnant l'extraction des fichiers CSV, leur transformation et leur chargement dans PostgreSQL, tout en permettant le suivi et le monitoring des tâches via son interface web.

## 3.B

**Logique de la fonction upsert_csv :**

La fonction upsert_csv charge un fichier CSV dans une table PostgreSQL avec une stratégie d'upsert (insert ou mise à jour). Elle lit le CSV avec pandas, convertit les types (dates, booléens), puis crée une table temporaire pour charger les données. Ensuite, elle exécute une requête SQL INSERT ... ON CONFLICT DO UPDATE qui insère les nouvelles lignes ou met à jour les lignes existantes en cas de conflit sur la clé primaire, en utilisant la clause SET pour mettre à jour toutes les colonnes non-PK avec les nouvelles valeurs.

## 3.C

![Capture 3.C](./Images%20TP2/3.C.png)

**Combien de clients avons-nous après month_000 ?**

On a donc 7043 clients après le month_000.

## 4.A

**Rôle de validate_with_ge dans le pipeline :**

La fonction validate_with_ge est une étape de contrôle qualité dans le pipeline d'ingestion. Elle utilise Great Expectations pour valider la structure et la qualité des données après leur chargement dans PostgreSQL. Elle vérifie que chaque table contient les colonnes attendues, que les valeurs essentielles (comme les clés primaires) ne sont pas nulles, et que les valeurs numériques respectent des contraintes raisonnables (par exemple, des valeurs non négatives pour les agrégats). Si une validation échoue, la fonction lève une exception, ce qui interrompt le flow Prefect et empêche la propagation de données invalides dans les étapes suivantes du pipeline, agissant ainsi comme un garde-fou avant les snapshots et les traitements ultérieurs.

## 4.C

**Validation des données :**

Pour la table usage_agg_30d, j'ai ajouté des expectations avec des bornes minimales sur certaines colonnes numériques. Voici les lignes correspondantes :

```python
gdf.expect_column_values_to_be_between("watch_hours_30d", min_value=0)
gdf.expect_column_values_to_be_between("avg_session_mins_7d", min_value=0)
```

Ces deux colonnes sont contraintes à être supérieures ou égales à 0, car elles représentent respectivement le nombre d'heures de visionnage sur 30 jours et la durée moyenne des sessions sur 7 jours. Par définition, ces métriques ne peuvent pas être négatives.

Ces règles de validation protègent le modèle de machine learning en excluant les valeurs impossibles ou aberrantes, par exemple des erreurs d'export, des bugs dans le pipeline d'agrégation, ou des données corrompues. En détectant ces anomalies avant l'entraînement du modèle, on évite qu'il apprenne des patterns basés sur des données erronées, ce qui pourrait dégrader ses performances de prédiction du churn et sa capacité à généraliser sur de nouvelles données.

## 5.A

**Explication de snapshot_month :**

La fonction snapshot_month crée des snapshots temporels des données en copiant l'état des tables live vers des tables de snapshots, où le paramètre as_of représente la date de référence (par exemple "2024-01-31") qui permet d'identifier à quel moment précis ces données ont été figées, permettant ainsi de conserver un historique des états des données à différentes dates pour des analyses rétrospectives.

## 5.B

![Capture 5.B](./Images%20TP2/5.B.png)

Les deux snapshots (2024-01-31 et 2024-02-29) ont le même nombre de lignes : 7043. C'est normal car on a le même nombre de clients entre janvier et février. Les snapshots capturent l'état des données à chaque date, et comme aucun nouveau client n'a été ajouté entre ces deux mois ou qu'on a eu le même nombre de désabonnement que de nouvel abonnement, le nombre de lignes reste identique.

## Synthèse

### Schéma du pipeline complet

```
┌─────────────────────────────────────────────────────────────┐
│                    FICHIERS CSV                             │
│              (month_000, month_001)                         │
│         /data/seeds/month_000/*.csv                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  1. UPSERT DES DONNÉES (upsert_csv)                        │
│  ─────────────────────────────────────                      │
│  • Lecture CSV avec pandas                                 │
│  • Conversion des types (dates, booléens)                  │
│  • Insert/Update dans PostgreSQL                           │
│    (ON CONFLICT DO UPDATE)                                 │
│    - users, subscriptions, usage_agg_30d,                  │
│      payments_agg_90d, support_agg_90d, labels             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  2. VALIDATION (validate_with_ge)                          │
│  ────────────────────────────────────                       │
│  • Vérification structure (colonnes attendues)             │
│  • Vérification qualité (non-null, bornes)                 │
│  • Great Expectations                                       │
│    - users, subscriptions, usage_agg_30d                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  3. SNAPSHOTS TEMPORELS (snapshot_month)                   │
│  ──────────────────────────────────────                     │
│  • Copie des tables live vers *_snapshots                  │
│  • Ajout du champ as_of (date de référence)                │
│    - subscriptions_profile_snapshots                        │
│    - usage_agg_30d_snapshots                                │
│    - payments_agg_90d_snapshots                             │
│    - support_agg_90d_snapshots                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              PostgreSQL                                     │
│  ┌────────────────────┐  ┌──────────────────────┐          │
│  │  Tables Live       │  │  Tables Snapshots    │          │
│  │  (état actuel)     │  │  (historique)        │          │
│  │                    │  │  avec as_of          │          │
│  └────────────────────┘  └──────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### Pourquoi ne pas travailler directement sur les tables live ?

On ne travaille pas directement sur les tables live pour entraîner un modèle car ces tables sont constamment mises à jour par le pipeline d'ingestion. Si on utilisait les tables live, on risquerait d'avoir des données qui changent entre le moment où on prépare le dataset d'entraînement et le moment où on l'utilise, ce qui rendrait les résultats non reproductibles. De plus, les tables live peuvent contenir des informations "du futur" par rapport à la date de prédiction, ce qui créerait du data leakage.

### Pourquoi les snapshots sont importants ?

Les snapshots sont essentiels pour éviter le data leakage et garantir la reproductibilité temporelle. Ils permettent de figer l'état des données à une date précise (as_of), ce qui garantit que lors de l'entraînement du modèle, on n'utilise que les informations qui étaient disponibles à cette date. Cela évite d'utiliser des données qui auraient été créées après l'événement qu'on cherche à prédire (comme le churn). Les snapshots assurent également la reproductibilité : on peut refaire exactement les mêmes expériences en utilisant les mêmes snapshots, même si les tables live ont changé entre-temps.

### Réflexion personnelle

**Qu'est-ce que j'ai trouvé le plus difficile ?**

La partie la plus difficile a été la compréhension de la stratégie d'upsert avec la clause `ON CONFLICT DO UPDATE`, notamment la construction de la partie SET pour mettre à jour toutes les colonnes non-clé primaire. J'ai également eu des difficultés à comprendre comment Prefect se connecte à son serveur API et à configurer correctement les variables d'environnement dans Docker Compose.

**Quelles erreurs ai-je rencontrées et comment les ai-je corrigées ?**

J'ai rencontré plusieurs erreurs : d'abord des problèmes de syntaxe PowerShell (utilisation de `\` au lieu de backticks pour les continuations de ligne), puis des erreurs de connexion à l'API Prefect car j'essayais d'utiliser `docker compose exec` avec des variables d'environnement alors que cette commande ne les accepte pas. J'ai résolu ces problèmes en utilisant `docker compose run` ou `bash -c` avec les variables. J'ai aussi eu des problèmes avec les conversions de types dans pandas, notamment pour les colonnes booléennes, que j'ai résolus en ajoutant explicitement les conversions nécessaires.
