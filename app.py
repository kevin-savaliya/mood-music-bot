from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse
from spotify_helper import get_playlist_for_mood_type
from nlp_helper import detect_mood_from_text

app = Flask(__name__)
user_state = {}

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        sender = request.form.get("From")
        msg = request.form.get("Body").strip().lower()
        print(f"Received message from {sender}: {msg}")
        resp = MessagingResponse()

        # Restart session
        if msg == "restart":
            user_state.pop(sender, None)
            resp.message("🔄 Restarted! Type *menu* to begin.")
            return Response(str(resp), mimetype="application/xml")

        # New session
        if sender not in user_state:
            user_state[sender] = {"step": "waiting"}
            resp.message("👋 Welcome to Mood Music Bot! Type *menu* to get started.")
            return Response(str(resp), mimetype="application/xml")

        state = user_state[sender]

        # Menu command
        if msg == "menu":
            state["step"] = "choose_mood"
            resp.message(get_mood_menu())
            return Response(str(resp), mimetype="application/xml")

        # Mood selection from menu
        if state["step"] == "choose_mood":
            moods = get_mood_dict()
            if msg in moods:
                selected_mood = moods[msg]
                if selected_mood == "manual":
                    state["step"] = "manual_mood_input"
                    resp.message("✍️ Please describe your current mood in a sentence.")
                    return Response(str(resp), mimetype="application/xml")
                else:
                    state["mood"] = selected_mood
                    state["step"] = "choose_type"
                    resp.message(get_music_type_menu(selected_mood))
                    return Response(str(resp), mimetype="application/xml")
            else:
                resp.message("❌ Invalid choice. Please choose a number from 1–9.\n" + get_mood_menu())
                return Response(str(resp), mimetype="application/xml")

        # NLP mood detection from user sentence
        # Step 1b: Manual NLP mood
        if state["step"] == "manual_mood_input":
            detected_mood = detect_mood_from_text(msg)
            valid_moods = get_mood_dict().values()
            print(f"🧠 NLP detected mood: {detected_mood}")

            # Safety fallback
            if not detected_mood or detected_mood.strip() == "":
                resp.message("⚠️ Unable to detect mood. Please describe differently or type *menu*.")
                return Response(str(resp), mimetype="application/xml")

            if detected_mood.lower() not in valid_moods:
                resp.message(
                    f"😕 Sorry, detected mood *{detected_mood}* is not in our list.\n"
                    "Try again with different words or type *menu* to start over."
                )
                return Response(str(resp), mimetype="application/xml")

            # Proceed to music type selection
            state["mood"] = detected_mood
            state["step"] = "choose_type"
            menu = get_music_type_menu(detected_mood)
            print(f"🎯 Sending music type menu for detected mood: {detected_mood}")
            resp.message(f"✅ Mood detected: *{detected_mood.capitalize()}*\n{menu}")
            return Response(str(resp), mimetype="application/xml")


        # Music type selection
        if state["step"] == "choose_type":
            types = get_type_dict()
            if msg not in types:
                resp.message("❌ Invalid type. Choose a number from 1–6.")
                return Response(str(resp), mimetype="application/xml")

            mood = state.get("mood", "happy")
            music_type = types[msg]

            try:
                playlist_url = get_playlist_for_mood_type(mood, music_type)
                reply = (
                    f"🎧 Here's a *{music_type.capitalize()} {mood.capitalize()}* playlist:\n"
                    f"{playlist_url}\n\n"
                    "Type *menu* to explore again or *restart* to reset."
                )
                resp.message(reply)
            except Exception as e:
                print("⚠️ Error getting playlist:", e)
                resp.message("⚠️ Something went wrong. Please try again later.")

            # Clean session after recommendation
            user_state.pop(sender, None)
            return Response(str(resp), mimetype="application/xml")

        # Fallback
        resp.message("🤖 I didn’t understand that. Type *menu* to start or *restart* to reset.")
        return Response(str(resp), mimetype="application/xml")

    except Exception as e:
        print("🔥 Error in webhook:", e)
        return "Error", 500

# --- Helper Dictionaries and Menus ---

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
        "🎵 *Choose Your Mood:*\n"
        "1. Happy\n"
        "2. Sad\n"
        "3. Chill\n"
        "4. Romantic\n"
        "5. Energetic\n"
        "6. Calm\n"
        "7. Study\n"
        "8. Workout\n"
        "9. ✍️ Enter Manually\n\n"
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
        f"🧠 Mood: *{mood.capitalize()}*\n"
        "🎶 Choose music type:\n"
        "1. Hindi\n"
        "2. English\n"
        "3. Bollywood\n"
        "4. Lofi\n"
        "5. Instrumental\n"
        "6. Devotional\n\n"
        "Reply with a number (e.g., 1)"
    )

# Run app
if __name__ == "__main__":
    app.run(debug=True)
