from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from spotify_helper import get_playlist_for_mood

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    msg = request.form.get("Body")
    mood = msg.lower()

    playlist_link = get_playlist_for_mood(mood)
    response_text = f"Here’s a {mood} playlist for you 🎶:\n{playlist_link}"

    resp = MessagingResponse()
    resp.message(response_text)
    return str(resp)
