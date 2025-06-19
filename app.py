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
        print(f"Received message from {sender}: {msg}")  # Debug log
        resp = MessagingResponse()

        # Reset session
        if msg == "restart":
            user_state.pop(sender, None)
            resp.message("🔄 Restarted! Type *menu* to start again.")
            return Response(str(resp), mimetype="application/xml")


        # Initialize if first time
        if sender not in user_state:
            user_state[sender] = {"step": "waiting_for_menu"}
            resp.message("👋 Welcome to Mood Music Bot!\nType *menu* to get started.")
            return Response(str(resp), mimetype="application/xml")


        state = user_state[sender]

        # Show menu
        if msg == "menu":
            user_state[sender] = {"step": "choose_mood"}
            resp.message(get_mood_menu())
            return Response(str(resp), mimetype="application/xml")


        # Step 1: Mood selection
        if state["step"] == "choose_mood":
            moods = get_mood_dict()
            if msg in moods:
                selected_mood = moods[msg]
                if selected_mood == "manual":
                    state["step"] = "manual_mood_input"
                    resp.message("✍️ Please describe your mood (e.g., 'I'm feeling low today')")
                    return Response(str(resp), mimetype="application/xml")

                state["mood"] = selected_mood
                state["step"] = "choose_type"
                resp.message(get_music_type_menu(selected_mood))
                return Response(str(resp), mimetype="application/xml")

            else:
                resp.message("❌ Invalid option. Please choose a number from 1 to 9.\n" + get_mood_menu())
                return Response(str(resp), mimetype="application/xml")


        # Step 1b: Manual NLP mood
        if state["step"] == "manual_mood_input":
            detected_mood = detect_mood_from_text(msg)
            valid_moods = get_mood_dict().values()
            print(f"Detected mood: {detected_mood}")  # Debug log

            if detected_mood not in valid_moods:
                resp.message("😕 Sorry, couldn't detect your mood. Try again or type *menu*.")
                return Response(str(resp), mimetype="application/xml")


            state["mood"] = detected_mood
            state["step"] = "choose_type"
            resp.message(f"✅ Detected mood: *{detected_mood.capitalize()}*\n" + get_music_type_menu(detected_mood))
            return Response(str(resp), mimetype="application/xml")


        # Step 2: Choose music type
        if state["step"] == "choose_type":
            types = get_type_dict()
            if msg not in types:
                resp.message("❌ Invalid type. Choose a number from 1 to 6.")
                return Response(str(resp), mimetype="application/xml")


            mood = state["mood"]
            music_type = types[msg]

            try:
                playlist = get_playlist_for_mood_type(mood, music_type)
                reply = (
                    f"🎧 Here's a *{music_type} {mood}* playlist:\n{playlist}\n\n"
                    "Type *menu* to try again or *restart* to reset."
                )
            except Exception as e:
                print("Error fetching playlist:", e)
                reply = "⚠️ Could not get music. Try again later."

            user_state.pop(sender, None)
            resp.message(reply)
            return Response(str(resp), mimetype="application/xml")


        # Fallback
        resp.message("🤖 I didn’t understand. Type *menu* to start or *restart* to reset.")
        return Response(str(resp), mimetype="application/xml")


    except Exception as e:
        print("Error in webhook:", e)
        return "Error", 500

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
        "🎵 *Choose Your Mood:*\n"
        "1. Happy\n"
        "2. Sad\n"
        "3. Chill\n"
        "4. Romantic\n"
        "5. Energetic\n"
        "6. Calm\n"
        "7. Study\n"
        "8. Workout\n"
        "9. ✍️ Enter Mood Manually\n\n"
        "Reply with a number (e.g., 3)"
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
        f"🧠 Detected Mood: *{mood.capitalize()}*\n"
        "🎶 Pick Music Type:\n"
        "1. Hindi\n"
        "2. English\n"
        "3. Bollywood\n"
        "4. Lofi\n"
        "5. Instrumental\n"
        "6. Devotional\n\n"
        "Reply with a number (e.g., 2)"
    )

# 🟢 Required for local running
if __name__ == "__main__":
    app.run(debug=True)
