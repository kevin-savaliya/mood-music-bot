import requests
import base64

CLIENT_ID = 'c1256903fc6d46438a47d064e27b5278'
CLIENT_SECRET = '319ed56de8664101821a082669a3e79a'

def get_access_token():
    auth_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")

    headers = {
        "Authorization": f"Basic {auth_base64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "grant_type": "client_credentials"
    }

    url = "https://accounts.spotify.com/api/token"
    result = requests.post(url, headers=headers, data=data)
    json_result = result.json()
    return json_result["access_token"]


def get_playlist_for_mood(mood):
    token = get_access_token()

    headers = {
        "Authorization": f"Bearer {token}"
    }

    query = f"{mood} playlist"
    url = f"https://api.spotify.com/v1/search?q={query}&type=playlist&limit=1"
    response = requests.get(url, headers=headers)
    data = response.json()

    try:
        playlist_url = data['playlists']['items'][0]['external_urls']['spotify']
        return playlist_url
    except IndexError:
        return "No playlist found for that mood."
