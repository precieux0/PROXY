import os
import requests
from flask import Flask, request, Response

app = Flask(__name__)

PROXY_USER = os.environ.get('PROXY_USER', 'mon_utilisateur')
PROXY_PASS = os.environ.get('PROXY_PASS', 'mon_mot_de_passe_securise')

def verifier_authentification():
    auth = request.authorization
    if not auth or auth.username != PROXY_USER or auth.password != PROXY_PASS:
        return Response("Authentification requise", 401, {'WWW-Authenticate': 'Basic'})
    return None

@app.route('/proxy', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'])
def proxy():
    erreur_auth = verifier_authentification()
    if erreur_auth:
        return erreur_auth

    url = request.args.get('url')
    if not url:
        return "Paramètre 'url' manquant", 400

    en_tetes_a_exclure = ['host', 'authorization', 'proxy-authorization', 'content-length']
    en_tetes = {k: v for k, v in request.headers if k.lower() not in en_tetes_a_exclure}

    try:
        reponse = requests.request(
            method=request.method,
            url=url,
            headers=en_tetes,
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False,
            stream=True
        )
    except Exception as e:
        return f"Erreur : {str(e)}", 500

    return Response(reponse.content, status=reponse.status_code, headers=dict(reponse.headers))

@app.route('/health')
def health():
    return "Proxy opérationnel", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
