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

    if msg == "restart":
        user_state.pop(sender, None)
        resp.message("🔄 Restarted! Type 'menu' to start.")
        return str(resp)

    if msg == "menu":
        user_state[sender] = {"step": "choose_mood"}
        resp.message(get_mood_menu())
        return str(resp)

    if sender not in user_state:
        user_state[sender] = {"step": "choose_mood"}
        resp.message("👋 Welcome! Type 'menu' to get started or 'restart' to reset.")
        return str(resp)

    state = user_state[sender]

    # Step 1: Choose Mood
    if state["step"] == "choose_mood":
        moods = get_mood_dict()
        if msg in moods:
            selected_mood = moods[msg]
            if selected_mood == "manual":
                state["step"] = "manual_mood_input"
                resp.message("✍️ Please type how you're feeling (e.g., 'I'm feeling energetic today')")
                return str(resp)

            state["mood"] = selected_mood
            state["step"] = "choose_type"
            resp.message(get_music_type_menu(selected_mood))
            return str(resp)
        else:
            resp.message("❌ Invalid option. Please choose from the menu by typing 1–9.\n\n" + get_mood_menu())
            return str(resp)

    # Step 1B: Manual Mood Detection
    if state["step"] == "manual_mood_input":
        detected_mood = detect_mood_from_text(msg)
        valid_moods = get_mood_dict().values()

        if detected_mood not in valid_moods:
            resp.message("🤖 I couldn’t detect your mood accurately. Please try again or type 'menu'.")
            return str(resp)

        state["mood"] = detected_mood
        state["step"] = "choose_type"
        resp.message(f"✅ Detected mood: *{detected_mood.capitalize()}*\n" + get_music_type_menu(detected_mood))
        return str(resp)

    # Step 2: Choose Music Type
    if state["step"] == "choose_type":
        types = get_type_dict()
        if msg not in types:
            resp.message("❌ Invalid type. Please enter a number (1–6).")
            return str(resp)

        mood = state["mood"]
        music_type = types[msg]

        try:
            playlist = get_playlist_for_mood_type(mood, music_type)
            reply = (
                f"🎧 Here's a *{music_type} {mood}* playlist:\n{playlist}\n\n"
                "Type 'menu' to explore again or 'restart' to reset."
            )
        except:
            reply = "⚠️ Something went wrong while fetching music. Please try again."

        user_state.pop(sender, None)
        resp.message(reply)
        return str(resp)

    # Fallback
    resp.message("🤖 I didn’t understand that. Type 'menu' to restart.")
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
        "Reply with the number (e.g., 1)"
    )
