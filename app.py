from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from spotify_helper import get_playlist_for_mood_type
from nlp_helper import detect_mood_from_text

app = Flask(__name__)
user_state = {}

@app.route("/webhook", methods=["POST"])
def webhook():
    sender = request.form.get("From")
    msg = request.form.get("Body").strip().lower()
    resp = MessagingResponse()

    # Reset user session
    if msg == "restart":
        user_state.pop(sender, None)
        resp.message("🔄 Restarted! Type 'menu' to start again.")
        return str(resp)

    # No session started yet
    if sender not in user_state:
        user_state[sender] = {"step": "waiting_for_menu"}
        resp.message("👋 Hi! Welcome to Mood Music Bot.\nType *menu* to explore moods or *restart* to reset.")
        return str(resp)

    state = user_state[sender]

    # Start mood menu
    if msg == "menu":
        user_state[sender] = {"step": "choose_mood"}
        resp.message(get_mood_menu())
        return str(resp)

    # Step 1: Choose Mood from menu
    if state["step"] == "choose_mood":
        moods = get_mood_dict()
        if msg in moods:
            selected_mood = moods[msg]
            if selected_mood == "manual":
                state["step"] = "manual_mood_input"
                resp.message("✍️ Please describe how you're feeling (e.g., 'I'm feeling low today')")
                return str(resp)

            state["mood"] = selected_mood
            state["step"] = "choose_type"
            resp.message(get_music_type_menu(selected_mood))
            return str(resp)
        else:
            resp.message("❌ Invalid option. Please choose from the mood list:\n" + get_mood_menu())
            return str(resp)

    # Step 1B: Manual Mood Input via NLP
    if state["step"] == "manual_mood_input":
        detected_mood = detect_mood_from_text(msg)
        valid_moods = get_mood_dict().values()

        if detected_mood not in valid_moods:
            resp.message("😕 Sorry, couldn't detect your mood. Please try again or type *menu*.")
            return str(resp)

        state["mood"] = detected_mood
        state["step"] = "choose_type"
        resp.message(f"✅ Detected mood: *{detected_mood.capitalize()}*\n" + get_music_type_menu(detected_mood))
        return str(resp)

    # Step 2: Choose music type
    if state["step"] == "choose_type":
        types = get_type_dict()
        if msg not in types:
            resp.message("❌ Invalid type. Please choose a valid number from 1–6.")
            return str(resp)

        mood = state["mood"]
        music_type = types[msg]

        try:
            playlist = get_playlist_for_mood_type(mood, music_type)
            reply = (
                f"🎧 Here's a *{music_type} {mood}* playlist:\n{playlist}\n\n"
                "Type *menu* to explore again or *restart* to reset."
            )
        except:
            reply = "⚠️ Could not fetch music right now. Please try again later."

        user_state.pop(sender, None)
        resp.message(reply)
        return str(resp)

    # Default fallback if none matched
    resp.message("🤖 I didn’t understand that. Type *menu* to start or *restart* to reset.")
    return str(resp)

# --- Helper Functions ---

def get_mood_dict():
    return {
        "1": "happy",
        "2": "sad",
        "3": "chill",
        "4": "romantic",
        "5": "energetic",
        "6": "calm",
        "7": "study",
        "8": "workout",
        "9": "manual"
    }

def get_mood_menu():
    return (
        "🎵 *Select Your Mood:*\n"
        "1. Happy\n"
        "2. Sad\n"
        "3. Chill\n"
        "4. Romantic\n"
        "5. Energetic\n"
        "6. Calm\n"
        "7. Study\n"
        "8. Workout\n"
        "9. ✍️ Enter Manually (Smart Mood Detection)\n\n"
        "Reply with a number (e.g., 3 or 9)"
    )

def get_type_dict():
    return {
        "1": "hindi",
        "2": "english",
        "3": "bollywood",
        "4": "lofi",
        "5": "instrumental",
        "6": "devotional"
    }

def get_music_type_menu(mood):
    return (
        f"🧠 You selected *{mood.capitalize()}* mood.\n"
        "🎶 Choose your music type:\n"
        "1. Hindi\n"
        "2. English\n"
        "3. Bollywood\n"
        "4. Lofi\n"
        "5. Instrumental\n"
        "6. Devotional\n\n"
        "Reply with a number (e.g., 1)"
    )
