# 🤝 Contributing to Vélivert Analytics Platform

Merci de votre intérêt pour contribuer au projet Vélivert Analytics !

## 🚀 Comment contribuer

### 1. Fork & Clone
```bash
git clone https://github.com/votre-username/velivert-app.git
cd velivert-app
```

### 2. Créer une branche
```bash
git checkout -b feature/ma-nouvelle-fonctionnalite
```

### 3. Développer
- Suivez les conventions de code existantes
- Ajoutez des tests si applicable
- Documentez les nouvelles fonctionnalités

### 4. Commit
```bash
git add .
git commit -m "feat: ajouter fonctionnalité X"
```

**Convention de commit:**
- `feat:` Nouvelle fonctionnalité
- `fix:` Correction de bug
- `docs:` Documentation
- `refactor:` Refactoring
- `test:` Tests
- `chore:` Maintenance

### 5. Push & Pull Request
```bash
git push origin feature/ma-nouvelle-fonctionnalite
```

Créez ensuite une Pull Request sur GitHub avec une description détaillée.

## 📋 Guidelines

### Code Style

**Backend (Python):**
- PEP 8
- Type hints recommandés
- Docstrings pour les fonctions publiques

**Frontend (TypeScript):**
- ESLint configuration fournie
- Composants fonctionnels avec hooks
- Props typées avec TypeScript

### Tests

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

### Structure de commit idéale

```
feat: ajouter optimisation multi-techniciens

- Implémentation algorithme K-means
- Équilibrage charge en 2 phases
- Tests unitaires ajoutés
- Documentation mise à jour

Closes #123
```

## 🐛 Signaler un bug

Utilisez les GitHub Issues avec le template:

**Description:**
- Comportement attendu
- Comportement observé
- Étapes pour reproduire

**Environnement:**
- OS
- Version Docker
- Version navigateur

## 💡 Proposer une fonctionnalité

Créez une issue avec le label `enhancement`:

1. Décrivez le besoin
2. Proposez une solution
3. Alternatives envisagées
4. Impact estimé

## ⚖️ Licence

En contribuant, vous acceptez que vos contributions soient sous licence MIT.

## 📞 Contact

Pour toute question: [Créer une issue](https://github.com/votre-repo/velivert-app/issues)

---

**Merci de contribuer à améliorer la gestion des vélos partagés ! 🚲**
