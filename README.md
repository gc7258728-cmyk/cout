# BuildOptima 360 V3 — Construction Intelligence

Application pédagogique **Génie civil N4** développée avec Streamlit. Architecture modulaire (métrés, simulations, CPM, Pareto, SQLite, rapports), jeux de démonstration **fictifs** et analyses de données importées.

## Installation locale

Python 3.11 ou 3.12 conseillé. Depuis le dossier qui contient `app.py` :

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Sur Windows, si `python` n'est pas reconnu, essayer `py -m pip install -r requirements.txt` et `py -m streamlit run app.py`.

## Démonstration rapide

1. Dans la barre latérale, cliquer sur **Créer le projet de démonstration**.
2. Ouvrir **Vue générale** et **Métrés & devis** pour vérifier le coût.
3. Ouvrir **Simulation Monte-Carlo**, lancer 10 000 tirages, observer la probabilité de dépassement et les quantiles.
4. Ouvrir **Planning CPM** pour afficher le Gantt, le chemin critique et les marges.
5. Ouvrir **Optimisation** pour la sensibilité des prix et les variantes déclarées admissibles.
6. Ouvrir **Statistiques & données** et importer un CSV ou XLSX réel : afficher d'abord les **données brutes**, la source, le nombre de lignes et les manquants.
7. Ouvrir **Rapports & sauvegardes** pour obtenir un PDF, Excel, CSV et sauvegarde JSON.

## Architecture

- `app.py` : interface responsive Streamlit, navigation, tableaux de bord, graphiques.
- `core/metres.py` : contrôle des entrées, coûts, volumes et masses géométriques, sensibilité.
- `core/probabilites.py` : Monte-Carlo vectorisé, facteurs triangulaires, corrélation de prix par copule gaussienne, quantiles et erreur MC.
- `core/planning.py` : calcul du chemin critique CPM sur graphe acyclique, prédécesseurs multiples, dates tôt/tard, marges.
- `core/optimisation.py` : front de Pareto sur variantes déclarées techniquement validées.
- `core/storage.py` : base SQLite persistante sur disque local, création, mise à jour, suppression.
- `core/reports.py` : rapport PDF paginé.
- `core/demo.py` : projet **fictif** pour la démonstration.
- `tests/test_core.py` : tests automatisés.

## Vérification

```bash
python -m unittest discover -s tests -v
python -m py_compile app.py core/*.py
```

5 tests unitaires passent dans l'environnement de création (calculs, Monte-Carlo, CPM, Pareto, SQLite, PDF). Le **rendu réel dans Streamlit et le déploiement cloud n'ont pas été testés** ici.

## Déploiement Streamlit Community Cloud

1. Créer un dépôt GitHub contenant **tout le contenu de ce dossier**, y compris le dossier `core/`, `requirements.txt` et `app.py` à la racine.
2. Aller sur Streamlit Community Cloud, sélectionner le dépôt et le fichier principal `app.py`.
3. Attendre l'installation des dépendances, puis vérifier les logs et toutes les pages.
4. **Important :** sur Streamlit Community Cloud, le stockage SQLite local est éphémère et peut être perdu au redémarrage, à la mise en veille ou au redéploiement. Utiliser régulièrement **Exporter tous les projets JSON**. Pour une application publique multi-utilisateur, remplacer SQLite local par une base distante et ajouter une authentification.

## Méthodes et limites

- Coût : `C = somme(Q_i * P_i)` ; unités et prix unitaires saisis manuellement.
- Monte-Carlo : variations triangulaires symétriques de quantités/prix dans les bornes ± pourcentages saisis. Corrélation des chocs de prix via une copule gaussienne (paramètre choisi, non estimé). Aucune corrélation entre quantités.
- Dépassement : fraction des coûts simulés strictement supérieurs au budget. Erreur MC : `sqrt(p(1-p)/N)` ; elle ne couvre pas l'incertitude du modèle.
- CPM : tâches avec plusieurs prédécesseurs ; jours calendaires, pas de ressources, congés ou contraintes de capacité.
- Pareto : minimisation coût et durée **uniquement parmi les variantes que l'utilisateur marque validées**. Aucun contrôle normatif automatique.
- Géométrie : acier à 7850 kg/m³, volumes et surfaces théoriques ; aucune validation de résistance.
- Les prix et données de démonstration sont **inventés**. Aucune prétention à des tarifs de marché camerounais actuels.
- Le module d'import analyse les données brutes d'un CSV/XLSX fourni, sans apprentissage prédictif ni récupération automatique de données externes. L'application n'est pas un devis certifié ni un logiciel de calcul de structures.

## Confidentialité et sécurité

L'application ne possède pas de gestion des comptes ou des autorisations. Ne pas déployer avec des données sensibles sur une instance publique partagée. Les sauvegardes JSON contiennent les projets en clair.
