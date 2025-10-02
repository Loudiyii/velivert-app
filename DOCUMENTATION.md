# 📘 Documentation Vélivert Analytics Platform

## 🎯 Vue d'ensemble

**Vélivert Analytics** est une plateforme d'analyse et de gestion en temps réel du système de vélos en libre-service de Saint-Étienne Métropole. L'application combine collecte de données GBFS, tracking de mouvements, optimisation de trajets et visualisations cartographiques interactives.

### Technologies utilisées

**Backend:**
- Python 3.11 / FastAPI
- PostgreSQL + TimescaleDB (time-series)
- SQLAlchemy (ORM async)
- Redis (cache)
- Celery (tâches asynchrones)
- Structlog (logging structuré)
- JWT Authentication

**Frontend:**
- React 18 + TypeScript
- Vite (build tool)
- React Router v6
- Leaflet / React-Leaflet (cartographie)
- Axios (HTTP client)
- Tailwind CSS

**Infrastructure:**
- Docker / Docker Compose
- Nginx (reverse proxy - optionnel)
- PgAdmin (administration DB)

---

## 🏗️ Architecture

```
velivert-app/
├── backend/
│   ├── app/
│   │   ├── api/endpoints/        # Routes API
│   │   ├── models/               # Modèles SQLAlchemy
│   │   ├── repositories/         # Couche d'accès données
│   │   ├── services/             # Logique métier
│   │   ├── schemas/              # Pydantic schemas
│   │   └── core/                 # Config, auth, database
│   ├── alembic/                  # Migrations DB
│   ├── force_refresh_data.py     # Script refresh manuel
│   └── auto_refresh_daemon.py    # Daemon refresh 5min
├── frontend/
│   ├── src/
│   │   ├── pages/                # Pages principales
│   │   ├── components/           # Composants réutilisables
│   │   ├── hooks/                # Custom hooks
│   │   ├── services/             # API clients
│   │   └── types/                # TypeScript types
│   └── public/
└── docker-compose.yml
```

---

## 🚀 Fonctionnalités implémentées

### ✅ 1. Authentification & Sécurité
- **Système JWT** avec tokens access/refresh
- Endpoints protégés par middleware
- Hash bcrypt pour mots de passe
- Rate limiting (à améliorer)

### ✅ 2. Collecte de données GBFS
- **API GBFS Saint-Étienne** intégrée
- Endpoints:
  - `station_information.json`
  - `station_status.json`
  - `free_bike_status.json`
- **Refresh automatique** toutes les 5 minutes (daemon Python)
- Stockage historique avec timestamps (TimescaleDB)

### ✅ 3. Dashboard
- **Statistiques en temps réel:**
  - Total vélos, vélos disponibles, vélos en circulation
  - Stations actives, taux d'activité
  - Indicateur de fraîcheur des données
- **Polling automatique** toutes les 4 minutes
- État de connexion WebSocket
- Liens rapides vers autres pages

### ✅ 4. Stations & Cartographie
- **Carte interactive Leaflet** avec toutes les stations
- Marqueurs colorés par état (actif/inactif)
- Popups détaillés:
  - Nom station, capacité
  - Vélos disponibles/désactivés
  - Emplacements libres
  - État location/retour
- Filtres par disponibilité

### ✅ 5. Gestion des vélos
- **Liste paginée** de tous les vélos
- Filtres: état (actif/désactivé), batterie, station
- Informations détaillées:
  - Position GPS, autonomie
  - Type de véhicule
  - Dernière mise à jour
- Vue carte des vélos en circulation

### ✅ 6. Flux de vélos (Bike Flows)
- **Analyse des mouvements** entre stations
- **Carte avec liaisons colorées** montrant:
  - Pickups (bleu)
  - Dropoffs (vert)
  - Relocations (violet)
  - En transit (orange)
- **Notifications toast** en temps réel pour nouveaux mouvements
- Toggle affichage/masquage des lignes
- Stations "hubs" identifiées (haute activité)
- **Statistiques:**
  - Total mouvements, pickups, dropoffs, relocations
  - Distance parcourue
  - Vélos uniques
- **Tracking historique:**
  - Table `bike_movements` avec détection automatique
  - Système de snapshots pour analyse time-series

### ✅ 7. Optimisation de trajets (Route Optimization)
- **3 types de trajets:**
  1. Collecte vélos désactivés
  2. Batteries faibles
  3. Interventions en attente
- **Algorithme du plus proche voisin** (Nearest Neighbor)
- **Fonctionnalités:**
  - Sélection station de départ (auto-sélection station optimale)
  - Calcul distance totale, durée estimée (5 min/vélo)
  - **Instructions détaillées étape par étape:**
    - "Récupérez le vélo X à la station Y, puis..."
    - Priorités (urgent/high/medium/low)
    - Texte de finalisation avec totaux
  - Carte avec marqueurs numérotés et polyline
  - Légende des priorités

### ✅ 8. Interventions de maintenance
- CRUD complet pour interventions
- Types: réparation, entretien, batterie, relocalisation
- Statuts: pending, in_progress, completed, cancelled
- Priorités visuelles
- Export Excel (à finaliser)

### ✅ 9. Analytics & Rapports
- **Graphiques de disponibilité** (Chart.js)
- Analyse temporelle des flux
- Patterns de demande par station
- Heures de pointe identifiées

---

## 📊 Base de données

### Tables principales

**Stations** (`stations`)
- ID, nom, coordonnées GPS
- Capacité, région
- Méthodes de location
- Is_virtual_station

**Station Status Snapshots** (`station_status_snapshots`)
- Hypertable TimescaleDB (optimisé time-series)
- État à chaque refresh (5min)
- Vélos disponibles/désactivés
- Docks disponibles/désactivés

**Bikes** (`bikes`)
- bike_id (unique)
- Position GPS courante
- Autonomie batterie (meters)
- État (is_disabled, is_reserved)
- Station actuelle (FK)
- Type de véhicule

**Bike Snapshots** (`bike_snapshots`)
- Hypertable TimescaleDB
- Historique positions vélos
- Tracking pour détection mouvements

**Bike Movements** (`bike_movements`)
- Mouvements détectés automatiquement
- From/To stations
- Type mouvement (pickup/dropoff/relocation/in_transit)
- Distance calculée
- Timestamp détection

**Maintenance Interventions** (`maintenance_interventions`)
- ID, bike_id, user_id
- Type, description, priorité
- Status, assigned_technician
- Scheduled_date, completed_date

**Users** (`users`)
- Authentification JWT
- Email, hashed_password
- Role (admin/technician/viewer)
- Is_active

---

## 🔄 Système de refresh des données

### Stratégie actuelle: Daemon Python
```python
# auto_refresh_daemon.py
# Tourne en background dans le container backend
# Refresh toutes les 5 minutes
```

**Processus:**
1. Fetch GBFS API (station_info, station_status, free_bikes)
2. Upsert stations dans DB
3. Création snapshots status stations
4. Upsert vélos
5. **Tracking mouvements** automatique:
   - Compare position actuelle vs dernier snapshot
   - Détecte changement station → crée `bike_movement`
   - Calcule distance avec haversine
   - Classe type mouvement

**Alternative Celery** (à réparer):
- Celery worker + beat pour tâches planifiées
- Actuellement non fonctionnel (manque asyncpg)

---

## 🌐 API Endpoints

### Authentication
- `POST /api/auth/register` - Créer compte
- `POST /api/auth/login` - Se connecter (retourne JWT)
- `POST /api/auth/refresh` - Rafraîchir token
- `GET /api/auth/me` - Info utilisateur courant

### Stations
- `GET /api/stations` - Liste toutes les stations
- `GET /api/stations/{id}` - Détails station
- `GET /api/stations/current` - Statuts actuels

### Bikes
- `GET /api/bikes` - Liste vélos (paginée)
- `GET /api/bikes/{id}` - Détails vélo
- `GET /api/bikes/current` - Statuts actuels
- `GET /api/bikes/in-circulation` - Vélos hors stations

### Bike Flows
- `GET /api/bike-flows/flows/station-movements` - Flux entre stations
- `GET /api/bike-flows/flows/current-circulation` - Circulation actuelle
- `GET /api/bike-flows/movements/history` - Historique mouvements
- `GET /api/bike-flows/flows/station-demand` - Patterns demande

### Route Optimization
- `GET /api/route-optimization/stations-with-disabled-bikes` - Stations avec vélos HS
- `GET /api/route-optimization/optimize/detailed-route` - Calcul trajet optimisé
- `GET /api/route-optimization/optimize/disabled-bikes` - Route vélos désactivés
- `GET /api/route-optimization/optimize/low-battery-bikes` - Route batteries faibles
- `GET /api/route-optimization/optimize/pending-interventions` - Route interventions

### Interventions
- `GET /api/interventions/` - Liste interventions
- `POST /api/interventions/` - Créer intervention
- `GET /api/interventions/{id}` - Détails
- `PUT /api/interventions/{id}` - Modifier
- `DELETE /api/interventions/{id}` - Supprimer
- `PATCH /api/interventions/{id}/status` - Changer statut

### WebSocket
- `WS /ws/realtime` - Flux temps réel (stations/bikes)

---

## 🎨 Interface utilisateur

### Pages principales

1. **Dashboard** (`/`)
   - Vue d'ensemble des KPIs
   - Indicateur fraîcheur données
   - Navigation rapide

2. **Stations** (`/stations`)
   - Carte interactive complète
   - Liste détaillée
   - Filtres multiples

3. **Vélos** (`/bikes`)
   - Table paginée
   - Filtres état/batterie
   - Carte vélos en circulation

4. **Flux de Vélos** (`/bike-flows`)
   - Carte avec lignes de mouvement
   - Notifications toast temps réel
   - Statistiques mouvements
   - Top stations actives

5. **Interventions** (`/interventions`)
   - Liste interventions
   - CRUD complet
   - 3 onglets: Optimisation routes, Planification, Historique

6. **Analytics** (`/analytics`)
   - Graphiques interactifs
   - Analyse temporelle
   - Exportation données

### Composants réutilisables

- `RefreshIndicator` - Indicateur refresh en cours
- `DataRefreshStatus` - Affichage fraîcheur données
- `BikeMovementToast` - Notifications mouvements temps réel
- `RealtimeMap` - Carte Leaflet configurable
- `DetailedRouteOptimizer` - Optimisation trajets

### Hooks personnalisés

- `useWebSocket(url)` - Connexion WebSocket temps réel
- `useDataPolling(options)` - Polling API configurable (3-5min)

---

## 🚧 Ce qui manque pour la PRODUCTION

### 🔴 Critiques (bloquants)

1. **Sécurité**
   - ❌ HTTPS obligatoire (actuellement HTTP)
   - ❌ CORS configuré mais à restreindre en prod
   - ❌ Secrets dans variables d'environnement (pas hardcodés)
   - ❌ Rate limiting API agressif
   - ❌ Input validation côté backend (injection SQL)
   - ❌ CSP headers (Content Security Policy)

2. **Tests**
   - ❌ Tests unitaires backend (pytest)
   - ❌ Tests d'intégration API
   - ❌ Tests E2E frontend (Playwright/Cypress)
   - ❌ Coverage < 80%

3. **Monitoring & Observabilité**
   - ❌ Logs centralisés (ELK stack / Datadog)
   - ❌ Métriques APM (temps réponse API)
   - ❌ Health checks robustes
   - ❌ Alerting (vélos HS, API down)

4. **Performance**
   - ❌ Cache Redis non utilisé
   - ❌ Pagination côté backend (actuellement tout chargé)
   - ❌ Index DB manquants (lat/lon pour geo-queries)
   - ❌ CDN pour assets frontend

5. **Scalabilité**
   - ❌ Load balancer (plusieurs instances backend)
   - ❌ DB read replicas
   - ❌ Queue Redis pour jobs lourds
   - ❌ Compression responses HTTP (gzip)

### 🟠 Importantes (à faire rapidement)

6. **Documentation**
   - ⚠️ OpenAPI/Swagger auto-généré (FastAPI le fait déjà)
   - ❌ README détaillé pour déploiement
   - ❌ Guide utilisateur
   - ❌ Changelog versioning

7. **CI/CD**
   - ❌ Pipeline GitHub Actions / GitLab CI
   - ❌ Tests automatiques sur PR
   - ❌ Build Docker automatique
   - ❌ Déploiement automatique staging/prod

8. **Backup & Disaster Recovery**
   - ❌ Backup automatique DB (daily)
   - ❌ Procédure restore documentée
   - ❌ Plan de reprise d'activité

9. **UX/UI**
   - ❌ Messages d'erreur utilisateur friendly
   - ❌ Loading states partout
   - ❌ Mode offline (Service Worker)
   - ❌ PWA (installable mobile)
   - ❌ Responsive mobile (partiellement fait)

10. **Features manquantes**
    - ❌ Export Excel fonctionnel (interventions)
    - ❌ Notifications email (interventions urgentes)
    - ❌ Rôles & permissions granulaires
    - ❌ Historique actions utilisateurs (audit log)
    - ❌ Prédictions ML (demande future stations)

### 🟢 Nice-to-have (améliorations)

11. **Analytics avancés**
    - Prédiction flux futurs (ML)
    - Recommandations relocalisation proactive
    - Détection anomalies (vélo immobile longtemps)
    - Heatmaps utilisation

12. **Intégration**
    - Webhook vers système maintenance externe
    - API publique pour partenaires
    - Integration Google Maps / Waze

13. **Optimisation trajets avancée**
    - Algorithme OR-Tools VRP (Vehicle Routing Problem)
    - Prise en compte trafic temps réel
    - Multi-véhicules (plusieurs techniciens)
    - Contraintes horaires (fenêtres temps)

---

## 🎯 Recommandations pour l'entretien

### Points forts à présenter

1. **Architecture moderne Software 3.0**
   - Développé avec assistance IA (Claude Code)
   - Stack moderne async (FastAPI, React 18)
   - Patterns industry-standard (Repository, Service layer)

2. **Fonctionnalités temps réel**
   - WebSocket, polling intelligent (3-5min)
   - Tracking mouvements automatique
   - Notifications toast instantanées

3. **Optimisation & Algorithmes**
   - Nearest Neighbor pour trajets
   - Calcul haversine distances
   - Auto-sélection station optimale

4. **Data Engineering**
   - TimescaleDB pour time-series
   - Hypertables optimisées
   - Système de snapshots historiques

5. **UX soignée**
   - Cartes interactives Leaflet
   - Visualisations colorées intuitive
   - Instructions textuelles détaillées

### Points d'amélioration à mentionner

**Montrer que vous comprenez les enjeux production:**

- "L'application est fonctionnelle mais nécessite plusieurs améliorations pour la production"
- "J'ai identifié 5 axes critiques: sécurité, tests, monitoring, performance, scalabilité"
- "Voici mon plan sur 3 mois pour passer en production..."

**Exemple de roadmap:**

**Mois 1 - Fondations:**
- Mise en place CI/CD
- Tests unitaires backend (80% coverage)
- HTTPS + secrets management
- Monitoring basique (logs, health checks)

**Mois 2 - Robustesse:**
- Tests E2E frontend
- Rate limiting & input validation
- Cache Redis actif
- Backup automatique DB

**Mois 3 - Scale:**
- Load balancer + multi-instances
- CDN + compression
- Alerting automatique
- Documentation complète

### Questions à poser au recruteur

1. "Quels sont vos attentes en termes de couverture de tests pour une app production?"
2. "Utilisez-vous des outils de monitoring spécifiques (Datadog, New Relic)?"
3. "Comment gérez-vous le déploiement des applications IA (A/B testing, gradual rollout)?"
4. "Quelle est votre approche pour la sécurité des APIs exposées?"

---

## 📦 Installation & Déploiement

### Prérequis
- Docker 20+ & Docker Compose
- Git
- (Optionnel) Node 18+ pour dev frontend local

### Démarrage rapide

```bash
# Cloner le repo
git clone <repo-url>
cd velivert-app

# Lancer les services
docker-compose up -d

# Vérifier les services
docker ps

# Créer un utilisateur admin
docker exec -it velivert_backend python -c "
from app.core.security import get_password_hash
print(get_password_hash('admin123'))
"

# Insérer en DB manuellement via PgAdmin (localhost:5050)
```

### URLs
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- PgAdmin: http://localhost:5050

### Variables d'environnement

Créer `.env` à la racine:
```env
# Database
DATABASE_URL=postgresql+asyncpg://velivert:velivert123@postgres:5432/velivert
POSTGRES_USER=velivert
POSTGRES_PASSWORD=velivert123
POSTGRES_DB=velivert

# Redis
REDIS_URL=redis://redis:6379/0

# JWT
SECRET_KEY=<générer clé sécurisée>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# GBFS API
GBFS_BASE_URL=https://transport.data.gouv.fr/gbfs/saint-etienne-metropole

# Frontend
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

---

## 📈 Métriques & Performance

### Actuelles (développement)
- ⏱️ Temps réponse API: ~50-200ms
- 📊 Refresh données: 5 minutes
- 🔄 Polling frontend: 3-5 minutes
- 💾 Taille DB: ~50MB (1 semaine données)
- 🚀 Chargement initial: ~2s

### Cibles production
- ⏱️ Temps réponse: <100ms (P95)
- 📊 Refresh données: 2 minutes
- 💾 Retention données: 1 an
- 🎯 Uptime: 99.5%
- 🔐 Latence WebSocket: <50ms

---

## 🤝 Contribution & Maintenance

### Structure commits
```
feat: add bike movement notifications
fix: correct route optimization duration (30min → 5min)
refactor: extract polling logic to custom hook
docs: update API endpoints documentation
test: add unit tests for route optimizer service
```

### Workflow Git
1. Branch feature depuis `develop`
2. Commits atomiques
3. Tests passent
4. Pull request avec description
5. Code review
6. Merge dans `develop`
7. Deploy staging automatique
8. Tests validation
9. Merge `develop` → `main`
10. Deploy production

---

## 📞 Support & Contact

**Développé par:** [Votre Nom]
**Date:** Octobre 2025
**Version:** 0.9.0 (pre-production)
**Licence:** MIT

---

## 🏆 Conclusion

Cette application démontre la capacité à:
- ✅ Architecturer une solution full-stack moderne
- ✅ Intégrer des APIs tierces (GBFS)
- ✅ Implémenter du temps réel (WebSocket, polling)
- ✅ Optimiser des algorithmes (trajets)
- ✅ Visualiser des données géospatiales
- ✅ Penser scalabilité et production-readiness

**Prochaines étapes critiques:**
1. Sécuriser (HTTPS, secrets, validation)
2. Tester (80%+ coverage)
3. Monitorer (logs, métriques, alertes)
4. Scaler (load balancer, cache, CDN)
5. Documenter (guides utilisateur, API)

**Cette app est un excellent point de départ pour un projet production-ready. Avec 2-3 mois de travail supplémentaire sur les axes critiques, elle sera prête pour un déploiement à grande échelle.**
