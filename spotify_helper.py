from urllib.parse import quote
import requests
import base64

CLIENT_ID = "c1256903fc6d46438a47d064e27b5278"
CLIENT_SECRET = "319ed56de8664101821a082669a3e79a"

def get_access_token():
    auth_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
    b64_auth = base64.b64encode(auth_string.encode()).decode()

    headers = {
        "Authorization": f"Basic {b64_auth}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {"grant_type": "client_credentials"}
    response = requests.post("https://accounts.spotify.com/api/token", headers=headers, data=data)
    return response.json()["access_token"]

def get_playlist_for_mood(mood, language):
    token = get_access_token()
    headers = {
        "Authorization": f"Bearer {token}"
    }

    query = f"{language} {mood} playlist"
    url = f"https://api.spotify.com/v1/search?q={quote(query)}&type=playlist&limit=1"
    response = requests.get(url, headers=headers)
    data = response.json()

    try:
        playlist_url = data["playlists"]["items"][0]["external_urls"]["spotify"]
        return playlist_url
    except:
        return "No playlist found. Try another mood/language!"
