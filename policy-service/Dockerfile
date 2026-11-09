# Image Python légère officielle
FROM python:3.11-slim

# Empêcher Python de générer des fichiers .pyc et activer les logs en temps réel
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Répertoire de travail dans le conteneur
WORKDIR /app

# Copier et installer les dépendances en premier (pour profiter du cache Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du code du microservice
COPY . .

# Exposer le port du microservice
EXPOSE 8080

# Commande de démarrage du serveur FastAPI avec Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

