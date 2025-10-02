# Guide de Recherche dans la Base de Données

Ce guide explique comment chercher et analyser les données des vélos et stations dans la base de données.

## Script de Recherche (`query_database.py`)

Le script `query_database.py` fournit des commandes pour interroger la base de données depuis la ligne de commande.

### Usage de Base

```bash
docker exec velivert_backend python query_database.py [commande] [arguments]
```

## Commandes Disponibles

### 1. Trouver les Vélos Suspects (Nécessitant Intervention)

```bash
docker exec velivert_backend python query_database.py suspect_bikes
```

**Détecte automatiquement:**
- Vélos désactivés
- Vélos avec batterie vide (0 km)
- Vélos avec autonomie faible (< 5 km)

**Exemple de résultat:**
```
=== Vélos Suspects Nécessitant Intervention (41) ===

[URGENT] be7797ca...
  Raisons: DÉSACTIVÉ, BATTERIE VIDE
  Station: chf7qn43casf...
  Position: 45.44637000, 4.36792000
```

### 2. Lister les Vélos Désactivés

```bash
docker exec velivert_backend python query_database.py disabled_bikes
```

Liste tous les vélos avec `is_disabled = true`.

### 3. Trouver les Vélos avec Batterie Faible

```bash
# Par défaut: < 5 km
docker exec velivert_backend python query_database.py low_battery

# Personnalisé: < 3 km
docker exec velivert_backend python query_database.py low_battery 3
```

### 4. Trouver les Vélos avec Batterie Vide

```bash
docker exec velivert_backend python query_database.py empty_battery
```

Liste les vélos avec `current_range_meters = 0` ou `NULL`.

### 5. Chercher un Vélo par ID

```bash
# Recherche partielle (accepte une partie de l'ID)
docker exec velivert_backend python query_database.py bike_by_id be7797

# Résultat complet avec tous les détails
docker exec velivert_backend python query_database.py bike_by_id be7797ca-ae5c-4de6-87b8-10e10c91b21f
```

**Exemple de résultat:**
```
=== Vélos trouvés (1) ===

ID: be7797ca-ae5c-4de6-87b8-10e10c91b21f
  Type: 1
  Station: chf7qn43casf4e19ghhk
  Position: 45.44637000, 4.36792000
  Autonomie: 0m
  Désactivé: True
  Réservé: False
  Dernière mise à jour: 2025-10-01 12:34:56
```

### 6. Lister les Vélos à une Station

```bash
# Recherche partielle (accepte une partie de l'ID station)
docker exec velivert_backend python query_database.py bikes_at_station chf7qn43

# Recherche complète
docker exec velivert_backend python query_database.py bikes_at_station chf7qn43casf4e19ghhk
```

**Exemple de résultat:**
```
=== Vélos à la station chf7qn43 (12) ===

Disponibles: 8
Désactivés: 3
Réservés: 1

  be7797ca... - DÉSACTIVÉ - 0.0km
  3648c069... - DISPONIBLE - 15.2km
  09166cb2... - DISPONIBLE - 18.5km
```

### 7. Voir le Statut de Toutes les Stations

```bash
docker exec velivert_backend python query_database.py station_status
```

**Affiche:**
- Stations vides (0 vélos)
- Stations pleines (>90% capacité)
- Stations avec peu de vélos (<3)

**Exemple de résultat:**
```
=== Statut des Stations (98) ===

Stations vides (0 vélos): 16
  - Campus Tréfilerie (chf7qok3casf...)
  - Fourneyron (chf7qrc3casf...)

Stations pleines (>90%): 7
  - Terrenoire Vial: 30/20 vélos
  - Piscine le Chambon: 12/10 vélos

Stations avec peu de vélos (<3): 32
  - Plotton: 2 vélos
  - Jean Jaurès: 2 vélos
```

### 8. Voir les Interventions Récentes

```bash
docker exec velivert_backend python query_database.py recent_interventions
```

Liste les 10 dernières interventions créées.

### 9. Voir l'Historique d'une Station

```bash
# Dernières 24 heures (par défaut)
docker exec velivert_backend python query_database.py station_history chf7qn43casf4e19ghhk

# Dernières 48 heures
docker exec velivert_backend python query_database.py station_history chf7qn43casf4e19ghhk 48
```

**Affiche les statistiques agrégées par heure:**
```
=== Historique Station: Campus Tréfilerie (dernières 24h) ===

2025-10-01 08:00
  Moyenne: 12.5 vélos
  Min: 8 vélos
  Max: 15 vélos
```

## Recherche Directe dans la Base de Données

### Via psql (ligne de commande PostgreSQL)

```bash
# Connexion à la base de données
docker exec -it velivert_db psql -U velivert -d velivert_db

# Dans psql:
velivert_db=#
```

### Exemples de Requêtes SQL

#### 1. Compter les vélos par statut

```sql
SELECT
    COUNT(*) FILTER (WHERE is_disabled = false AND is_reserved = false) AS disponibles,
    COUNT(*) FILTER (WHERE is_disabled = true) AS desactives,
    COUNT(*) FILTER (WHERE is_reserved = true) AS reserves,
    COUNT(*) AS total
FROM bikes;
```

#### 2. Trouver les vélos sans batterie

```sql
SELECT bike_id, current_station_id, current_range_meters, is_disabled
FROM bikes
WHERE current_range_meters = 0 OR current_range_meters IS NULL
ORDER BY is_disabled DESC;
```

#### 3. Stations avec le plus de vélos

```sql
SELECT
    s.name,
    s.capacity,
    COUNT(b.bike_id) AS bikes_count
FROM stations s
LEFT JOIN bikes b ON b.current_station_id = s.id
GROUP BY s.id, s.name, s.capacity
ORDER BY bikes_count DESC
LIMIT 10;
```

#### 4. Vélos par type de véhicule

```sql
SELECT
    vehicle_type_id,
    COUNT(*) AS count,
    COUNT(*) FILTER (WHERE is_disabled = false) AS actifs
FROM bikes
GROUP BY vehicle_type_id
ORDER BY count DESC;
```

#### 5. Évolution du nombre de vélos disponibles (dernières 24h)

```sql
SELECT
    time_bucket('1 hour', time) AS hour,
    AVG(num_bikes_available)::numeric(10,2) AS avg_bikes
FROM station_status_snapshots
WHERE time >= NOW() - INTERVAL '24 hours'
GROUP BY hour
ORDER BY hour;
```

#### 6. Stations qui ont eu des changements récents

```sql
SELECT
    s.name,
    ss.num_bikes_available,
    ss.num_docks_available,
    ss.time
FROM station_status_snapshots ss
JOIN stations s ON s.id = ss.station_id
WHERE ss.time >= NOW() - INTERVAL '1 hour'
ORDER BY ss.time DESC
LIMIT 20;
```

## Depuis l'Interface Web

### Page Interventions - Alertes Automatiques

La page `/interventions` détecte automatiquement les vélos suspects et affiche des alertes:

1. **Alertes Urgentes (Rouge)** - Batterie vide (0 km)
2. **Alertes Importantes (Orange)** - Vélos désactivés ou autonomie < 5 km
3. **Alertes Moyennes (Jaune)** - Autres problèmes

Cliquez sur "Créer Intervention" dans une alerte pour créer automatiquement une intervention pré-remplie.

### Page Vélos - Recherche et Filtres

Sur `/bikes`:
- **Recherche** - Tapez une partie de l'ID du vélo
- **Filtre par statut** - Tous / Disponibles / Désactivés
- **Statistiques en temps réel** - Cartes avec totaux

### Page Stations - Carte Interactive

Sur `/stations`:
- **Vue Carte** - Marqueurs colorés selon disponibilité
  - Vert: > 5 vélos
  - Jaune: 1-4 vélos
  - Orange: 0 vélos
  - Rouge: Station inactive
- **Vue Liste** - Tableau avec tous les détails
- **Filtres** - Par statut et recherche par nom

## API REST

Vous pouvez aussi interroger l'API directement avec curl ou Postman:

```bash
# Token d'authentification
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@velivert.com","password":"admin123"}' \
  | jq -r '.access_token')

# Liste tous les vélos
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/bikes/current

# Liste les vélos désactivés
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/bikes/disabled/list

# Statut actuel des stations
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/stations/current

# Interventions en attente
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/interventions/pending
```

## Conseils de Recherche

1. **Pour trouver un vélo spécifique** - Utilisez `bike_by_id` avec une partie de l'ID
2. **Pour voir quels vélos ont besoin d'attention** - Utilisez `suspect_bikes`
3. **Pour analyser une station** - Utilisez `bikes_at_station` puis `station_history`
4. **Pour planifier les interventions** - Utilisez `disabled_bikes` et `low_battery`
5. **Pour voir la vue d'ensemble** - Utilisez `station_status`

## Résumé des Données Actuelles

D'après la dernière vérification:
- **98 stations** au total
- **495 vélos** au total
- **41 vélos suspects** nécessitant intervention (désactivés ou batterie faible)
- **16 stations vides** (0 vélos)
- **32 stations avec peu de vélos** (<3 vélos)

Ces chiffres sont mis à jour en temps réel depuis l'API GBFS de Saint-Étienne Métropole.
