import os
import requests
from urllib.parse import urlparse
from flask import Flask, request, Response

app = Flask(__name__)

# Récupération des identifiants du proxy depuis les variables d'environnement Render
# ⚠️ TRÈS IMPORTANT : Ces variables d'environnement DOIVENT être définies dans Render
PROXY_USER = os.environ.get('PROXY_USER', 'mon_utilisateur')
PROXY_PASS = os.environ.get('PROXY_PASS', 'mon_mot_de_passe_securise')

def verifier_authentification():
    auth = request.authorization
    if not auth or auth.username != PROXY_USER or auth.password != PROXY_PASS:
        return Response("Authentification requise", 401, {'WWW-Authenticate': 'Basic'})
    return None

@app.route('/proxy', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy():
    erreur_auth = verifier_authentification()
    if erreur_auth:
        return erreur_auth

    # Récupération et validation de l'URL cible
    url_destination = request.args.get('url')
    if not url_destination:
        return "Paramètre 'url' manquant", 400

    # On conserve les en-têtes nécessaires
    en_tetes_a_conserver = ['content-type', 'user-agent', 'accept', 'origin', 'referer']
    en_tetes = {k: v for k, v in request.headers if k.lower() in en_tetes_a_conserver}

    # On gère le corps de la requête (important pour les uploads)
    corps = request.get_data()

    try:
        # Envoi de la requête vers la destination *depuis Render*
        reponse = requests.request(
            method=request.method,
            url=url_destination,
            headers=en_tetes,
            data=corps,
            cookies=request.cookies,
            allow_redirects=False,
            timeout=60  # Timeout plus long pour les fichiers volumineux
        )
    except Exception as e:
        return f"Erreur lors de l'appel vers la destination : {str(e)}", 500

    # On renvoie la réponse brute au client
    return Response(reponse.content, status=reponse.status_code, headers=dict(reponse.headers))

@app.route('/health')
def health():
    return "Proxy opérationnel", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)