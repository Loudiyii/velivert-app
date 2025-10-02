"""Multi-technician route optimization using K-means clustering."""

import structlog
from typing import List, Dict, Any, Tuple
from sklearn.cluster import KMeans
import numpy as np
from app.services.route_optimizer import RouteOptimizerService

logger = structlog.get_logger()


class MultiTechnicianOptimizer:
    """
    Service pour optimiser les trajets de plusieurs techniciens.

    Utilise K-means clustering pour répartir intelligemment les vélos
    entre techniciens basé sur la proximité géographique.
    """

    def __init__(self):
        self.route_optimizer = RouteOptimizerService()

    def assign_technicians(
        self,
        interventions: List[Dict[str, Any]],
        num_technicians: int,
        technician_names: List[str] = None,
        start_location: Tuple[float, float] = (45.439695, 4.387178)  # Centre Saint-Étienne
    ) -> Dict[str, Any]:
        """
        Répartit les interventions entre techniciens et calcule les trajets optimaux.

        Algorithme:
        1. K-means clustering initial sur positions GPS (lat, lon)
        2. Rééquilibrage des interventions pour charge équitable
        3. Distribution équitable des interventions urgentes
        4. Calcule trajet optimal pour chaque technicien

        Args:
            interventions: Liste des interventions/vélos à collecter
            num_technicians: Nombre de techniciens disponibles
            technician_names: Noms des techniciens (optionnel)
            start_location: Point de départ central

        Returns:
            Dict avec assignations par technicien et métriques
        """

        if not interventions:
            return {
                "technician_assignments": [],
                "total_technicians": num_technicians,
                "total_interventions": 0,
                "optimization_algorithm": "Balanced K-means + Load Balancing"
            }

        # Limiter le nombre de clusters au nombre d'interventions
        actual_num_technicians = min(num_technicians, len(interventions))

        logger.info(
            "multi_technician_optimization_start",
            num_interventions=len(interventions),
            num_technicians=actual_num_technicians
        )

        # Noms par défaut si non fournis
        if not technician_names or len(technician_names) < actual_num_technicians:
            technician_names = [f"Technicien {i+1}" for i in range(actual_num_technicians)]

        # Extraire coordonnées GPS pour clustering
        coordinates = np.array([
            [interv['lat'], interv['lon']] for interv in interventions
        ])

        # K-means clustering initial
        kmeans = KMeans(
            n_clusters=actual_num_technicians,
            random_state=42,
            n_init=10
        )
        cluster_labels = kmeans.fit_predict(coordinates)
        cluster_centers = kmeans.cluster_centers_

        # Grouper interventions par cluster initial
        clusters = {i: [] for i in range(actual_num_technicians)}
        for idx, label in enumerate(cluster_labels):
            clusters[label].append(interventions[idx])

        # ÉTAPE 1 : RÉÉQUILIBRAGE du NOMBRE d'interventions (strict)
        clusters = self._balance_intervention_count(clusters, actual_num_technicians, cluster_centers)

        # ÉTAPE 2 : RÉÉQUILIBRAGE du TEMPS de travail (affinage)
        clusters = self._rebalance_workload(clusters, actual_num_technicians, cluster_centers)

        # Calculer distance de chaque centre de cluster au point de départ
        cluster_distances = []
        for i, center in enumerate(cluster_centers):
            distance = self.route_optimizer._calculate_distance(
                start_location,
                (center[0], center[1])
            )
            # Score basé sur distance ET nombre d'interventions urgentes
            urgent_count = sum(
                1 for interv in clusters[i]
                if interv.get('priority') == 'urgent'
            )
            # Plus d'urgents = score plus élevé (priorité)
            priority_score = urgent_count * 100
            cluster_distances.append({
                'cluster_id': i,
                'distance': distance,
                'urgent_count': urgent_count,
                'total_count': len(clusters[i]),
                'priority_score': priority_score - distance  # Urgent prioritaire, proche aussi
            })

        # Trier par score de priorité (urgents + proximité)
        cluster_distances.sort(key=lambda x: x['priority_score'], reverse=True)

        # Assigner techniciens aux clusters par ordre de priorité
        technician_assignments = []

        for idx, cluster_info in enumerate(cluster_distances):
            cluster_id = cluster_info['cluster_id']
            cluster_interventions = clusters[cluster_id]

            if not cluster_interventions:
                continue

            # Trouver le point de départ optimal pour ce cluster
            # Utiliser le centre du cluster ou la station la plus proche du départ global
            cluster_start = self._find_optimal_start(
                cluster_interventions,
                start_location
            )

            # Calculer trajet optimal pour ce technicien
            route = self.route_optimizer.optimize_route(
                interventions=cluster_interventions,
                start_location=cluster_start,
                prioritize_urgent=True
            )

            assignment = {
                "technician_id": idx,
                "technician_name": technician_names[idx],
                "cluster_id": cluster_id,
                "num_interventions": len(cluster_interventions),
                "urgent_count": cluster_info['urgent_count'],
                "route": route,
                "start_location": {
                    "lat": cluster_start[0],
                    "lon": cluster_start[1],
                    "name": f"Zone {idx + 1}"
                },
                "estimated_duration_minutes": route['estimated_duration_minutes'],
                "total_distance_km": round(route['total_distance_meters'] / 1000, 2),
                "priority_score": cluster_info['priority_score']
            }

            technician_assignments.append(assignment)

        # Statistiques globales
        total_distance = sum(a['total_distance_km'] for a in technician_assignments)
        total_duration = max(
            (a['estimated_duration_minutes'] for a in technician_assignments),
            default=0
        )

        result = {
            "technician_assignments": technician_assignments,
            "total_technicians": actual_num_technicians,
            "total_interventions": len(interventions),
            "total_distance_km": round(total_distance, 2),
            "max_duration_minutes": total_duration,  # Temps du technicien le plus lent
            "optimization_algorithm": "Balanced K-means + Load Balancing + Nearest Neighbor",
            "summary": {
                "most_loaded_technician": max(
                    technician_assignments,
                    key=lambda x: x['num_interventions']
                )['technician_name'] if technician_assignments else None,
                "avg_interventions_per_tech": round(
                    len(interventions) / actual_num_technicians, 1
                ) if actual_num_technicians > 0 else 0,
                "load_balance_score": self._calculate_load_balance(technician_assignments)
            }
        }

        logger.info(
            "multi_technician_optimization_complete",
            num_technicians=actual_num_technicians,
            total_distance=total_distance,
            max_duration=total_duration
        )

        return result

    def _find_optimal_start(
        self,
        interventions: List[Dict[str, Any]],
        global_start: Tuple[float, float]
    ) -> Tuple[float, float]:
        """
        Trouve le point de départ optimal pour un groupe d'interventions.

        Choisit l'intervention la plus proche du point de départ global.
        """
        if not interventions:
            return global_start

        closest = min(
            interventions,
            key=lambda i: self.route_optimizer._calculate_distance(
                global_start,
                (i['lat'], i['lon'])
            )
        )

        return (closest['lat'], closest['lon'])

    def _balance_intervention_count(
        self,
        clusters: Dict[int, List[Dict[str, Any]]],
        num_technicians: int,
        cluster_centers: np.ndarray
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        Équilibre strictement le NOMBRE d'interventions entre techniciens.

        Chaque technicien doit avoir environ N/T interventions (±1).
        Transfère les excédents vers les techniciens sous-chargés.

        Args:
            clusters: Clusters K-means initiaux (déséquilibrés)
            num_technicians: Nombre de techniciens
            cluster_centers: Centres des clusters

        Returns:
            Clusters équilibrés par nombre
        """
        total_interventions = sum(len(cluster) for cluster in clusters.values())
        target_count = total_interventions // num_technicians
        max_count = target_count + 1  # Tolérance de +1

        logger.info(
            "count_balancing_start",
            total_interventions=total_interventions,
            target_count=target_count,
            num_technicians=num_technicians
        )

        balanced_clusters = {i: list(clusters[i]) for i in range(num_technicians)}

        # Boucle jusqu'à équilibrage strict
        for iteration in range(50):  # Max 50 transferts
            counts = [len(balanced_clusters[i]) for i in range(num_technicians)]

            # Trouver surchargé et sous-chargé
            max_tech = counts.index(max(counts))
            min_tech = counts.index(min(counts))

            # Si équilibré (différence ≤ 1), arrêter
            if max(counts) - min(counts) <= 1:
                logger.info("count_balancing_converged", iterations=iteration, final_counts=counts)
                break

            # Transférer 1 intervention du surchargé au sous-chargé
            if balanced_clusters[max_tech]:
                # Choisir l'intervention la plus proche du centre du technicien sous-chargé
                best_transfer = None
                min_distance = float('inf')

                for interv in balanced_clusters[max_tech]:
                    interv_coord = np.array([interv['lat'], interv['lon']])
                    distance = np.linalg.norm(interv_coord - cluster_centers[min_tech])

                    if distance < min_distance:
                        min_distance = distance
                        best_transfer = interv

                if best_transfer:
                    balanced_clusters[max_tech].remove(best_transfer)
                    balanced_clusters[min_tech].append(best_transfer)
                    logger.info(
                        f"count_transfer_iteration_{iteration}",
                        from_tech=max_tech,
                        to_tech=min_tech,
                        from_count=counts[max_tech],
                        to_count=counts[min_tech]
                    )

        final_counts = [len(balanced_clusters[i]) for i in range(num_technicians)]
        logger.info(
            "count_balancing_complete",
            final_counts=final_counts,
            min=min(final_counts),
            max=max(final_counts),
            diff=max(final_counts) - min(final_counts)
        )

        return balanced_clusters

    def _rebalance_workload(
        self,
        clusters: Dict[int, List[Dict[str, Any]]],
        num_technicians: int,
        cluster_centers: np.ndarray
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        Rééquilibre les interventions pour équilibrer le TEMPS DE TRAVAIL.

        Stratégie:
        1. Assigne initialement selon K-means
        2. Calcule le trajet optimal et le temps pour chaque technicien
        3. Transfère des interventions des surchargés vers sous-chargés
        4. Répète jusqu'à équilibrage du temps de travail

        Args:
            clusters: Dict des clusters actuels
            num_technicians: Nombre de techniciens
            cluster_centers: Centres des clusters K-means

        Returns:
            Clusters rééquilibrés par temps de travail
        """
        # Initialiser les assignations
        balanced_clusters = {i: list(clusters[i]) for i in range(num_technicians)}

        logger.info("time_based_workload_balancing_start")

        # Itérations pour équilibrer le temps
        max_iterations = 15
        tolerance_minutes = 20  # Tolérance de ±20 minutes
        previous_time_diff = float('inf')
        no_improvement_count = 0

        for iteration in range(max_iterations):
            # Calculer les trajets et temps pour chaque technicien
            tech_times = []
            tech_routes = []

            for tech_id in range(num_technicians):
                if not balanced_clusters[tech_id]:
                    tech_times.append(0)
                    tech_routes.append(None)
                    continue

                # Calculer trajet optimal pour ce technicien
                try:
                    route = self.route_optimizer.optimize_route(
                        interventions=balanced_clusters[tech_id],
                        start_location=(cluster_centers[tech_id][0], cluster_centers[tech_id][1]),
                        prioritize_urgent=True
                    )
                    tech_times.append(route['estimated_duration_minutes'])
                    tech_routes.append(route)
                except Exception as e:
                    logger.error(f"Route optimization failed for tech {tech_id}: {e}")
                    tech_times.append(0)
                    tech_routes.append(None)

            # Vérifier l'équilibrage
            max_time = max(tech_times)
            min_time = min(t for t in tech_times if t > 0) if any(t > 0 for t in tech_times) else 0
            time_diff = max_time - min_time

            logger.info(
                f"iteration_{iteration}",
                tech_times=tech_times,
                max_time=max_time,
                min_time=min_time,
                time_diff=time_diff
            )

            # Si équilibré, arrêter
            if time_diff <= tolerance_minutes:
                logger.info("time_balancing_converged", iterations=iteration+1)
                break

            # Détecter si on n'améliore plus (oscillation ou blocage)
            if time_diff >= previous_time_diff:
                no_improvement_count += 1
                if no_improvement_count >= 3:
                    logger.info("time_balancing_stuck", iterations=iteration+1, reason="no_improvement")
                    break
            else:
                no_improvement_count = 0

            previous_time_diff = time_diff

            # Identifier technicien surchargé et sous-chargé
            overloaded_tech = tech_times.index(max_time)
            underloaded_tech = tech_times.index(min_time)

            # Trouver l'intervention à transférer (la plus éloignée du centre du cluster surchargé)
            if not balanced_clusters[overloaded_tech]:
                break

            overloaded_center = cluster_centers[overloaded_tech]
            underloaded_center = cluster_centers[underloaded_tech]

            # Trouver l'intervention du technicien surchargé qui est la plus proche du technicien sous-chargé
            best_transfer = None
            best_score = float('inf')

            # Première passe : préférer les interventions non-urgentes
            for interv in balanced_clusters[overloaded_tech]:
                interv_coord = np.array([interv['lat'], interv['lon']])

                # Distance à son cluster actuel vs nouveau cluster
                dist_from_overloaded = np.linalg.norm(interv_coord - overloaded_center)
                dist_to_underloaded = np.linalg.norm(interv_coord - underloaded_center)

                # Score = préfère transférer ce qui rapproche du sous-chargé
                # Pénaliser les urgents (mais les autoriser quand même)
                urgency_penalty = 1000 if interv.get('priority') == 'urgent' else 0
                score = dist_to_underloaded - dist_from_overloaded + urgency_penalty

                if score < best_score:
                    best_score = score
                    best_transfer = interv

            # Si aucun candidat trouvé, prendre le premier disponible
            if best_transfer is None and balanced_clusters[overloaded_tech]:
                best_transfer = balanced_clusters[overloaded_tech][0]

            # Effectuer le transfert
            if best_transfer:
                balanced_clusters[overloaded_tech].remove(best_transfer)
                balanced_clusters[underloaded_tech].append(best_transfer)
                logger.info(
                    f"transferred_intervention",
                    from_tech=overloaded_tech,
                    to_tech=underloaded_tech,
                    bike_id=best_transfer.get('bike_id', 'N/A')
                )
            else:
                # Pas de transfert possible, arrêter
                break

        # Logs finaux
        final_loads = [len(balanced_clusters[i]) for i in range(num_technicians)]
        final_times = tech_times
        logger.info(
            "time_based_balancing_complete",
            loads=final_loads,
            times_minutes=final_times,
            max_time=max(final_times),
            min_time=min(t for t in final_times if t > 0) if any(t > 0 for t in final_times) else 0
        )

        return balanced_clusters

    def _calculate_load_balance(
        self,
        assignments: List[Dict[str, Any]]
    ) -> float:
        """
        Calcule un score d'équilibrage de charge (0-100).

        100 = parfaitement équilibré
        0 = très déséquilibré
        """
        if not assignments or len(assignments) < 2:
            return 100.0

        counts = [a['num_interventions'] for a in assignments]
        avg_count = np.mean(counts)

        if avg_count == 0:
            return 100.0

        # Coefficient de variation (écart-type / moyenne)
        cv = np.std(counts) / avg_count

        # Convertir en score 0-100 (moins de variation = meilleur score)
        score = max(0, 100 - (cv * 100))

        return round(score, 1)
