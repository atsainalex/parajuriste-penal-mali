# Parajuriste Pénal Mali 🇲🇱⚖️

Application web d'assistance juridique pour le droit pénal malien, basée sur le Code pénal 2024, le Code de procédure pénale 2024 et la Constitution 2023.

## 📋 Architecture

- **Frontend** : HTML/CSS/JavaScript (interface de chat moderne)
- **Backend** : FastAPI (Python) avec base de connaissance FAISS et intégration OpenAI
- **Base de données** : FAISS (recherche vectorielle)

## 🚀 Déploiement

### 1️⃣ Déployer le Backend sur Render

1. Créez un compte sur [render.com](https://render.com) (gratuit)
2. Cliquez sur **"New +"** → **"Web Service"**
3. Connectez votre compte GitHub et sélectionnez ce dépôt
4. Configurez le service :
   - **Name** : `parajuriste-backend`
   - **Region** : Choisissez la région la plus proche
   - **Branch** : `master`
   - **Root Directory** : `backend`
   - **Runtime** : `Python 3`
   - **Build Command** : `pip install -r requirements.txt`
   - **Start Command** : `uvicorn app:app --host 0.0.0.0 --port $PORT`
5. Dans **Environment Variables**, ajoutez :
   - **Key** : `OPENAI_API_KEY`
   - **Value** : Votre clé API OpenAI
6. Cliquez sur **"Create Web Service"**

Render va déployer votre backend et vous donnera une URL (ex: `https://parajuriste-backend.onrender.com`)

### 2️⃣ Configurer le Frontend

1. Une fois le backend déployé, copiez l'URL fournie par Render
2. Ouvrez le fichier `frontend/script.js`
3. Remplacez `YOUR_RENDER_URL.onrender.com` par votre URL Render (ligne 5)
   ```javascript
   const API_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
       ? "http://127.0.0.1:8000/chat"
       : "https://parajuriste-backend.onrender.com/chat"; // Votre URL ici
   ```
4. Committez et poussez les changements :
   ```bash
   git add frontend/script.js
   git commit -m "Update backend URL"
   git push origin master
   ```

### 3️⃣ Déployer le Frontend sur Vercel

1. Créez un compte sur [vercel.com](https://vercel.com) (gratuit)
2. Cliquez sur **"Add New..."** → **"Project"**
3. Importez votre dépôt GitHub : `parajuriste-penal-mali`
4. Configurez le projet :
   - **Framework Preset** : Other
   - **Root Directory** : `frontend`
   - **Build Command** : (laissez vide)
   - **Output Directory** : (laissez vide ou `.`)
5. Cliquez sur **"Deploy"**

Vercel va déployer votre frontend et vous donnera une URL (ex: `https://parajuriste-penal-mali.vercel.app`)

## 🎯 Accès à l'application

Une fois les deux déploiements terminés, votre application sera accessible via l'URL Vercel !

## 🔧 Développement local

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

### Frontend
Ouvrez simplement `frontend/index.html` dans votre navigateur.

## 📚 Base de connaissance

La base de connaissance inclut :
- Code pénal malien (2024)
- Code de procédure pénale malien (2024)
- Constitution du Mali (2023)
- Guides citoyens
- Numéros d'urgence Mali

## ⚠️ Avertissement

Cette application est un outil d'assistance et ne remplace pas un avocat professionnel. Pour les démarches devant le tribunal, consultez un avocat qualifié.

## 📄 Licence

Ce projet est destiné à un usage éducatif et d'assistance juridique au Mali.
