# Rapport TP6 : CI/CD pour systèmes ML + réentraînement automatisé + promotion MLflow

## 1. Mise en place du rapport et vérifications de départ

### 1.1 Démarrage de la stack et vérification des services

#### Commandes utilisées

**1. Démarrage de la stack complète**

```bash
docker compose up -d
```

**Sortie :**

![Démarrage de la stack](images%20TP6/capture_docker_compose_up.png)

**2. Vérification du statut des services**

```bash
docker compose ps
```

**Sortie :**

![Statut des services](images%20TP6/capture_docker_compose_ps.png)

**3. Vérification des logs de l'API**

```bash
docker compose logs -f api
```

**Sortie :**

![Logs de l'API](images%20TP6/capture_api_restart_logs.png)

### 1.2 Vérification du modèle en Production dans MLflow

**Vérification MLflow UI :**

![Modèle en Production dans MLflow](images%20TP6/capture_mlflow_production_initial.png)

**Description :**
- URL MLflow : http://localhost:5000
- Modèle : streamflow_churn
- Stage : Production
- Version visible dans la capture d'écran

---

## 2. Ajouter une logique de décision testable (unit test)

### 2.1 Fonction `should_promote` dans `compare_utils.py`

La fonction `should_promote` a été créée dans `services/prefect/compare_utils.py`. Cette fonction pure permet de décider si un modèle candidat doit être promu en Production en comparant son AUC avec celui du modèle Production actuel.

**Pourquoi extraire une fonction pure pour les tests unitaires ?**

On extrait une fonction pure pour éviter de tester "directement Prefect + MLflow" dans des tests unitaires. Une fonction pure est facilement testable car elle :
- N'a pas d'effets de bord (pas d'appels réseau, pas de modifications d'état)
- Retourne toujours le même résultat pour les mêmes entrées
- Peut être testée rapidement sans dépendances externes (MLflow, Prefect, etc.)

### 2.2 Tests unitaires

Les tests unitaires ont été créés dans `tests/unit/test_compare_utils.py`.

**Exécution des tests :**

```bash
pytest -q
```

**Sortie attendue :**

![Tests unitaires réussis](images%20TP6/capture_pytest_success.png)

---

## 3. Créer le flow Prefect `train_and_compare_flow`

### 3.1 Description du flow

Le flow `train_and_compare_flow` a été créé dans `services/prefect/train_and_compare_flow.py`. Ce flow :
1. Construit un dataset d'entraînement pour un `as_of` donné (Feast + labels)
2. Entraîne un modèle candidat et logge `val_auc` dans MLflow
3. Évalue le modèle Production sur les mêmes données/split
4. Compare `val_auc` et promeut si amélioration >= delta

### 3.2 Exécution du flow

**Commande :**

```bash
docker compose exec prefect python train_and_compare_flow.py
```

**Logs du flow :**

![Exécution du flow train_and_compare](images%20TP6/capture_train_compare_flow.png)

### 3.3 Vérification dans MLflow

**Vérification MLflow UI après exécution :**

![Stage Production dans MLflow](images%20TP6/capture_mlflow_promotion.png)

**Résultat :**
- [x] Version candidate créée
- [ ] Promotion effectuée (selon résultat de la comparaison)
- La capture montre l'état du modèle après l'exécution du flow

**Pourquoi utiliser un delta ?**

On utilise un delta (par défaut 0.01) pour éviter de promouvoir un modèle qui n'apporte qu'une amélioration marginale. Cela permet de :
- Éviter les promotions inutiles pour des gains négligeables
- Réduire le risque de régression en production
- Assurer une amélioration significative avant de remplacer le modèle en production

---

## 4. Connecter drift → retraining automatique (monitor_flow.py)

### 4.1 Modifications apportées

Le fichier `services/prefect/monitor_flow.py` a été modifié pour :
- Importer `train_and_compare_flow`
- Utiliser un seuil de déclenchement de retrain à 0.02 (au lieu de 0.3)
- Appeler `train_and_compare_flow(as_of=as_of_cur)` quand `drift_share >= threshold`

### 4.2 Exécution du monitoring

**Commande :**

```bash
docker compose exec prefect python monitor_flow.py
```

**Logs :**

![Exécution du monitoring et réentraînement](images%20TP6/capture_monitor_retraining.png)

### 4.3 Rapport Evidently

**Rapport Evidently - Vue d'ensemble :**

![Rapport Evidently - Partie 1](images%20TP6/capture_evidently_report_1.png)

**Rapport Evidently - Détails du drift :**

![Rapport Evidently - Partie 2](images%20TP6/capture_evidently_report_2.png)

**Description :**
- Fichier : `reports/evidently/drift_2024-01-31_vs_2024-02-29.html`
- Drift share calculé : visible dans les captures
- Décision prise : Réentraînement déclenché si drift_share >= 0.02

---

## 5. Redémarrage API pour charger le nouveau modèle Production + test /predict

### 5.1 Redémarrage de l'API

**Commandes :**

```bash
docker compose restart api
docker compose logs -f api
```

**Sortie :**

![Logs de redémarrage de l'API](images%20TP6/capture_api_restart_logs.png)

**Pourquoi l'API doit être redémarrée ?**

L'API charge le modèle au démarrage depuis MLflow (URI `models:/streamflow_churn/Production`). Si une promotion a eu lieu, il faut redémarrer l'API pour qu'elle recharge la nouvelle version du modèle en Production. Sans redémarrage, l'API continuerait à utiliser l'ancienne version en cache.

### 5.2 Test de prédiction

**Récupération d'un user_id :**

```bash
head -n 2 data/seeds/month_000/users.csv
```

**Appel de prédiction :**

```bash
curl -s -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"[USER_ID_RÉCUPÉRÉ]"}' | jq
```

**Réponse JSON - Partie 1 :**

![Test de prédiction API - Partie 1](images%20TP6/capture_api_prediction_1.png)

**Réponse JSON - Partie 2 :**

![Test de prédiction API - Partie 2](images%20TP6/capture_api_prediction_2.png)

---

## 6. CI GitHub Actions (smoke + unit) avec Docker Compose

### 6.1 Configuration du workflow

Le workflow CI a été créé dans `.github/workflows/ci.yml`. Il comprend deux jobs :
1. **unit** : Exécute `pytest` sur les tests unitaires rapides
2. **integration** : Démarre la stack via `docker compose` et fait un healthcheck

### 6.2 Déclenchement de la CI

**Pour déclencher la CI :**
- Pousser sur GitHub (ou ouvrir une PR)

**GitHub Actions - CI réussie :**

![GitHub Actions CI](images%20TP6/capture_github_actions_ci.png)

**Pourquoi démarrer Docker Compose dans la CI ?**

On démarre Docker Compose dans la CI pour effectuer des tests d'intégration multi-services. Cela permet de :
- Vérifier que tous les services démarrent correctement ensemble
- Tester l'intégration entre les différents composants (API, PostgreSQL, MLflow, Feast)
- Détecter les problèmes de configuration ou de dépendances entre services
- S'assurer que l'API répond correctement après le démarrage

---

## 7. Synthèse finale : boucle complète drift → retrain → promotion → serving

### 7.1 Architecture du système

Le système complet fonctionne selon la boucle suivante :

1. **Détection de drift** : Le flow `monitor_month_flow` compare les données de référence (month_000) avec les données courantes (month_001) via Evidently
2. **Calcul du drift_share** : Evidently calcule la proportion de features qui ont dérivé
3. **Décision de réentraînement** : Si `drift_share >= threshold` (0.02), le réentraînement est déclenché
4. **Réentraînement et comparaison** : Le flow `train_and_compare_flow` :
   - Entraîne un nouveau modèle candidat
   - Évalue le modèle Production actuel
   - Compare les AUC et décide de promouvoir si `new_auc > prod_auc + delta`
5. **Promotion** : Si le modèle candidat est meilleur, il est promu en Production dans MLflow
6. **Redémarrage de l'API** : L'API doit être redémarrée pour charger le nouveau modèle
7. **Serving** : L'API sert désormais le nouveau modèle en Production

### 7.2 Rôle du seuil de drift (0.02)

Le seuil de 0.02 signifie que si au moins 2% des features ont dérivé, on déclenche un réentraînement. En pratique, ce seuil serait généralement plus élevé (0.2-0.5) pour éviter les réentraînements trop fréquents. Un seuil trop bas peut entraîner :
- Des réentraînements inutiles pour des variations normales
- Des coûts de calcul élevés
- Des risques de sur-ajustement aux variations temporaires

### 7.3 Comparaison et promotion dans `train_and_compare_flow`

Le flow compare les AUC de validation entre le modèle candidat et le modèle Production. La décision de promotion est prise par la fonction `should_promote` qui vérifie :
- Si `prod_auc` est NaN ou None → promotion automatique
- Si `new_auc > prod_auc + delta` → promotion

Le delta (0.01 par défaut) garantit une amélioration significative avant promotion.

### 7.4 Prefect vs GitHub Actions

**Prefect** s'occupe de :
- L'orchestration des workflows ML (ingestion, training, monitoring)
- La logique métier de réentraînement et de promotion
- L'exécution des flows de manière planifiée ou déclenchée

**GitHub Actions** s'occupe de :
- La vérification que le code s'intègre correctement (CI)
- L'exécution des tests unitaires rapides
- Les tests d'intégration avec Docker Compose
- La validation que les services démarrent et fonctionnent ensemble

### 7.5 Limites et améliorations

**Pourquoi la CI ne doit pas entraîner le modèle complet ?**

La CI ne doit pas entraîner le modèle complet car :
- C'est trop lent (peut prendre plusieurs minutes/heures)
- C'est non déterministe (les résultats peuvent varier légèrement)
- C'est coûteux en ressources (CPU/mémoire)
- La CI doit être rapide pour donner un feedback rapide aux développeurs

**Quels tests manquent ?**

- Tests d'intégration end-to-end (ingestion → training → serving)
- Tests de performance (latence, throughput)
- Tests de charge
- Tests de régression sur les métriques
- Tests de validation des données d'entrée
- Tests de rollback en cas de problème

**Pourquoi l'approbation humaine / gouvernance est souvent nécessaire en vrai ?**

L'approbation humaine est nécessaire car :
- Les métriques automatiques ne capturent pas tous les aspects (bias, équité, interprétabilité)
- Il faut valider que le modèle respecte les contraintes réglementaires
- Il faut s'assurer que les changements sont alignés avec la stratégie métier
- Il faut documenter les décisions pour l'audit et la traçabilité
- Il faut gérer les cas edge (modèles équivalents, régressions sur certaines métriques secondaires)

---

## Conclusion

Ce TP a permis de mettre en place un système complet de CI/CD pour systèmes ML avec :
- Réentraînement automatisé déclenché par la détection de drift
- Comparaison automatique des modèles et promotion conditionnelle
- Tests unitaires et d'intégration via GitHub Actions
- Une boucle complète de monitoring → retrain → promotion → serving

Le système est maintenant capable de détecter automatiquement les dérives de données, de réentraîner les modèles, et de les promouvoir en production si ils apportent une amélioration significative.
