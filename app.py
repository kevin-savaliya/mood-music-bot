from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from spotify_helper import get_playlist_for_mood

app = Flask(__name__)
user_state = {}

@app.route("/webhook", methods=["POST"])
def webhook():
    sender = request.form.get("From")
    msg = request.form.get("Body").strip().lower()
    resp = MessagingResponse()

    if sender not in user_state:
        user_state[sender] = {"step": "choose_mood"}

    state = user_state[sender]

    # Step 1: Ask for Mood
    if state["step"] == "choose_mood":
        moods = {
            "1": "happy",
            "2": "sad",
            "3": "chill",
            "4": "romantic"
        }

        if msg not in moods:
            reply = (
                "🎵 Select your mood:\n"
                "1. Happy\n"
                "2. Sad\n"
                "3. Chill\n"
                "4. Romantic\n"
                "Reply with the number (e.g., 2)"
            )
            resp.message(reply)
            return str(resp)

        state["mood"] = moods[msg]
        state["step"] = "choose_language"

        reply = (
            f"🌐 You selected *{moods[msg].capitalize()}* mood.\n"
            "Now choose language:\n"
            "1. English\n"
            "2. Hindi\n"
            "Reply with the number"
        )
        resp.message(reply)
        return str(resp)

    # Step 2: Ask for Language
    if state["step"] == "choose_language":
        languages = {
            "1": "english",
            "2": "hindi"
        }

        if msg not in languages:
            reply = (
                "🌐 Please choose a valid language option:\n"
                "1. English\n"
                "2. Hindi"
            )
            resp.message(reply)
            return str(resp)

        language = languages[msg]
        mood = state["mood"]

        playlist = get_playlist_for_mood(mood, language)

        reply = (
            f"🎧 Here's a *{language} {mood}* playlist for you:\n"
            f"{playlist}\n\n"
            f"Click to open in Spotify!"
        )

        # Reset user state
        del user_state[sender]

        resp.message(reply)
        return str(resp)

    # Fallback
    resp.message("Sorry, I didn't understand. Please type a number from the options.")
    return str(resp)
