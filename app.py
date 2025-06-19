from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from spotify_helper import get_playlist_for_mood

app = Flask(__name__)

# Track session (simplified state)
user_state = {}

@app.route("/webhook", methods=["POST"])
def webhook():
    sender = request.form.get("From")
    msg = request.form.get("Body").strip().lower()
    resp = MessagingResponse()

    if sender not in user_state:
        user_state[sender] = {}

    state = user_state[sender]

    if "mood" not in state:
        # Step 1: Ask for mood
        state["step"] = "choose_mood"
        reply = (
            "🎵 Select your mood:\n"
            "1. Happy\n"
            "2. Sad\n"
            "3. Chill\n"
            "4. Romantic\n"
            "Reply with the number (e.g., 2)"
        )
    elif "language" not in state:
        if state["step"] == "choose_mood":
            moods = {
                "1": "happy",
                "2": "sad",
                "3": "chill",
                "4": "romantic"
            }
            mood = moods.get(msg)
            if not mood:
                return str(resp.message("❌ Invalid choice. Please enter 1-4."))
            state["mood"] = mood
            state["step"] = "choose_language"
            reply = (
                "🌐 Choose language:\n"
                "1. English\n"
                "2. Hindi\n"
                "Reply with the number"
            )
    else:
        if state["step"] == "choose_language":
            languages = {"1": "english", "2": "hindi"}
            language = languages.get(msg)
            if not language:
                return str(resp.message("❌ Invalid choice. Please enter 1 or 2."))

            mood = state["mood"]
            # Fetch song/playlist link
            playlist_link = get_playlist_for_mood(mood, language)

            reply = (
                f"🎧 Here's a {language} {mood} playlist for you:\n"
                f"{playlist_link}\n\n"
                f"Click to open in Spotify app!"
            )

            # Reset state
            del user_state[sender]

    resp.message(reply)
    return str(resp)
