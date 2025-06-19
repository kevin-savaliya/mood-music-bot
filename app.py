from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from spotify_helper import get_playlist_for_mood_type

app = Flask(__name__)
user_state = {}

@app.route("/webhook", methods=["POST"])
def webhook():
    sender = request.form.get("From")
    msg = request.form.get("Body").strip().lower()
    resp = MessagingResponse()

    if msg == "restart":
        user_state.pop(sender, None)
        resp.message("🔄 Restarted! Type 'menu' to begin again.")
        return str(resp)

    if msg == "menu":
        reply = (
            "🎵 *Mood Options:*\n"
            "1. Happy\n"
            "2. Sad\n"
            "3. Chill\n"
            "4. Romantic\n"
            "5. Energetic\n"
            "6. Calm\n"
            "7. Study\n"
            "8. Workout\n"
            "\nType the number to choose mood."
        )
        user_state[sender] = {"step": "choose_mood"}
        resp.message(reply)
        return str(resp)

    # Default flow
    if sender not in user_state:
        user_state[sender] = {"step": "choose_mood"}
        resp.message("👋 Hi! Type 'menu' to begin or 'restart' anytime.")
        return str(resp)

    state = user_state[sender]

    # Step 1: Choose Mood
    if state["step"] == "choose_mood":
        moods = {
            "1": "happy",
            "2": "sad",
            "3": "chill",
            "4": "romantic",
            "5": "energetic",
            "6": "calm",
            "7": "study",
            "8": "workout"
        }
        if msg not in moods:
            return str(resp.message("❌ Invalid mood. Type 'menu' to see options."))

        state["mood"] = moods[msg]
        state["step"] = "choose_type"

        reply = (
            f"🧠 Mood set to *{moods[msg].capitalize()}*.\n"
            "🎶 Choose music type:\n"
            "1. Hindi\n"
            "2. English\n"
            "3. Bollywood\n"
            "4. Lofi\n"
            "5. Instrumental\n"
            "6. Devotional"
        )
        resp.message(reply)
        return str(resp)

    # Step 2: Choose Music Type
    if state["step"] == "choose_type":
        types = {
            "1": "hindi",
            "2": "english",
            "3": "bollywood",
            "4": "lofi",
            "5": "instrumental",
            "6": "devotional"
        }
        if msg not in types:
            return str(resp.message("❌ Invalid choice. Enter 1–6."))

        mood = state["mood"]
        music_type = types[msg]

        playlist = get_playlist_for_mood_type(mood, music_type)
        reply = (
            f"🎧 Here's a *{music_type} {mood}* playlist for you:\n"
            f"{playlist}\n\nType 'menu' to explore more or 'restart' to start over."
        )

        del user_state[sender]  # Reset session
        resp.message(reply)
        return str(resp)

    # Fallback
    resp.message("🤖 Sorry, I didn't get that. Type 'menu' to begin.")
    return str(resp)
