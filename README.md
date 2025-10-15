# Projet Miskatonic

## Résumé
Générateur de quizs en ligne.

## Collaborateurs
[![GitHub](https://img.shields.io/badge/GitHub-Nathalie%20Bédiée-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/natbediee/)  
[![GitHub](https://img.shields.io/badge/GitHub-Hugo%20Babin-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/hugobabin)

## Stack technique
[![Python](https://img.shields.io/badge/Python-3.12.3-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/) [![FastAPI](https://img.shields.io/badge/FastAPI-0.116.1-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)  
[![JavaScript](https://img.shields.io/badge/JavaScript-ES6-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript) [![Bulma](https://img.shields.io/badge/Bulma-Latest-00D1B2?style=for-the-badge&logo=bulma&logoColor=white)](https://bulma.io/)  
[![MongoDB](https://img.shields.io/badge/MongoDB-Latest-47A248?style=for-the-badge&logo=mongodb&logoColor=white)](https://www.mongodb.com/) [![SQLite](https://img.shields.io/badge/SQLite-Latest-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)

## Installation
- git clone https://github.com/hugobabin/miskatonic/ && cd miskatonic
- python3 -m venv .venv
- cd src-client && pip install -r requirements.txt

## Utilisation
### Lancer le backend
- docker compose up (depuis la racine du projet)
### Lancer le frontend
- source .venv/bin/activate (depuis la racine du projet)
- cd src-client (depuis la racine du projet)
- python3 app.py (depuis src-client)
### URLs importantes
- Accéder à l'API : localhost:8000/
- Accéder à Mongo Express (user: user, pwd: user) : localhost:8081/
- Accéder à Grafana : localhost:3000/
- Accéder au client (user: admin, pwd: admin123) : localhost:5000/


