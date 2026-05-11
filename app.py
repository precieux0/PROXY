import os
import requests
from urllib.parse import urlparse, parse_qs
from flask import Flask, request, Response

app = Flask(__name__)

PROXY_USER = os.environ.get('PROXY_USER', 'monuser')
PROXY_PASS = os.environ.get('PROXY_PASS', 'monpass')

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

    url_cible = request.args.get('url')
    if not url_cible:
        return "Paramètre 'url' manquant", 400

    # Pour les requêtes POST, on conserve les données du corps
    corps = request.get_data()
    
    # On transmet les en-têtes essentiels
    en_tetes_a_conserver = ['content-type', 'user-agent', 'accept', 'origin', 'referer']
    en_tetes = {k: v for k, v in request.headers if k.lower() in en_tetes_a_conserver}

    try:
        reponse = requests.request(
            method=request.method,
            url=url_cible,
            headers=en_tetes,
            data=corps,
            cookies=request.cookies,
            allow_redirects=False,
            timeout=60
        )
    except Exception as e:
        return f"Erreur lors de l'appel vers la destination : {str(e)}", 500

    return Response(reponse.content, status=reponse.status_code, headers=dict(reponse.headers))

@app.route('/health')
def health():
    return "Proxy opérationnel", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)