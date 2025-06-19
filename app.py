from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse
from spotify_helper import get_playlist_for_mood_type
from nlp_helper import detect_mood_from_text
import logging

app = Flask(__name__)
user_state = {}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        logger.info("Received GET request for webhook verification")
        return "Webhook is active", 200

    try:
        # Log full request data for debugging
        logger.info(f"Received POST request: {request.form}")

        # Validate incoming request
        if not request.form:
            logger.error("No form data received in POST request")
            resp = MessagingResponse()
            resp.message("Error: No form data received")
            return Response(
                str(resp),
                status=400,
                mimetype="application/xml",
                headers={"Content-Type": "application/xml; charset=utf-8"}
            )

        sender = request.form.get("From")
        msg = request.form.get("Body", "").strip().lower()

        if not sender or not msg:
            logger.error(f"Missing sender or message: sender={sender}, msg={msg}")
            resp = MessagingResponse()
            resp.message("Error: Missing sender or message")
            return Response(
                str(resp),
                status=400,
                mimetype="application/xml",
                headers={"Content-Type": "application/xml; charset=utf-8"}
            )

        logger.info(f"📩 Processing message from {sender}: {msg}")
        resp = MessagingResponse()

        # Initialize new session
        if sender not in user_state:
            user_state[sender] = {"step": "waiting"}
            logger.info(f"New session created for {sender}")

        state = user_state[sender]

        # Handle menu command explicitly
        if msg == "menu":
            state["step"] = "choose_mood"
            menu_text = get_mood_menu()
            logger.info(f"Sending mood menu to {sender}: {menu_text}")
            resp.message(menu_text)
            return Response(
                str(resp),
                status=200,
                mimetype="application/xml",
                headers={"Content-Type": "application/xml; charset=utf-8"}
            )

        # Restart session
        if msg == "restart":
            user_state.pop(sender, None)
            logger.info(f"Session restarted for {sender}")
            resp.message("🔄 Restarted! Type *menu* to begin.")
            return Response(
                str(resp),
                status=200,
                mimetype="application/xml",
                headers={"Content-Type": "application/xml; charset=utf-8"}
            )

        # Mood selection
        if state["step"] == "choose_mood":
            moods = get_mood_dict()
            if msg in moods:
                selected_mood = moods[msg]
                if selected_mood == "manual":
                    state["step"] = "manual_mood_input"
                    resp.message("✍️ Please describe your current mood in a sentence.")
                else:
                    state["mood"] = selected_mood
                    state["step"] = "choose_type"
                    menu_text = get_music_type_menu(selected_mood)
                    logger.info(f"Sending music type menu for mood {selected_mood} to {sender}")
                    resp.message(menu_text)
                return Response(
                    str(resp),
                    status=200,
                    mimetype="application/xml",
                    headers={"Content-Type": "application/xml; charset=utf-8"}
                )
            else:
                menu_text = get_mood_menu()
                logger.info(f"Invalid mood choice from {sender}, resending menu")
                resp.message("❌ Invalid choice. Please choose a number from 1–9.\n" + menu_text)
                return Response(
                    str(resp),
                    status=200,
                    mimetype="application/xml",
                    headers={"Content-Type": "application/xml; charset=utf-8"}
                )

        # Manual NLP mood detection
        if state["step"] == "manual_mood_input":
            detected_mood = detect_mood_from_text(msg)
            valid_moods = get_mood_dict().values()
            logger.info(f"🧠 NLP detected mood: {detected_mood}")

            if not detected_mood or detected_mood.strip() == "":
                logger.info(f"Failed to detect mood from {sender}, requesting retry")
                resp.message("⚠️ Unable to detect mood. Please describe differently or type *menu*.")
                return Response(
                    str(resp),
                    status=200,
                    mimetype="application/xml",
                    headers={"Content-Type": "application/xml; charset=utf-8"}
                )

            if detected_mood.lower() not in valid_moods:
                logger.info(f"Unsupported mood {detected_mood} detected for {sender}")
                resp.message(
                    f"😕 Sorry, detected mood *{detected_mood}* is not supported.\n"
                    "Try again with different words or type *menu* to start over."
                )
                return Response(
                    str(resp),
                    status=200,
                    mimetype="application/xml",
                    headers={"Content-Type": "application/xml; charset=utf-8"}
                )

            state["mood"] = detected_mood
            state["step"] = "choose_type"
            menu = get_music_type_menu(detected_mood)
            logger.info(f"Sending music type menu for detected mood {detected_mood} to {sender}")
            resp.message(f"✅ Mood detected: *{detected_mood.capitalize()}*")
            resp.message(menu)
            return Response(
                str(resp),
                status=200,
                mimetype="application/xml",
                headers={"Content-Type": "application/xml; charset=utf-8"}
            )

        # Music type selection
        if state["step"] == "choose_type":
            types = get_type_dict()
            if msg not in types:
                logger.info(f"Invalid type choice from {sender}")
                resp.message("❌ Invalid type. Choose a number from 1–6.")
                return Response(
                    str(resp),
                    status=200,
                    mimetype="application/xml",
                    headers={"Content-Type": "application/xml; charset=utf-8"}
                )

            mood = state.get("mood", "happy")
            music_type = types[msg]

            try:
                playlist_url = get_playlist_for_mood_type(mood, music_type)
                reply = (
                    f"🎧 Here's a *{music_type.capitalize()} {mood.capitalize()}* playlist:\n"
                    f"{playlist_url}\n\n"
                    "Type *menu* to explore again or *restart* to reset."
                )
                logger.info(f"Sending playlist URL to {sender}: {playlist_url}")
                resp.message(reply)
            except Exception as e:
                logger.error(f"Error getting playlist for {sender}: {str(e)}")
                resp.message("⚠️ Something went wrong. Please try again later.")

            user_state.pop(sender, None)
            return Response(
                str(resp),
                status=200,
                mimetype="application/xml",
                headers={"Content-Type": "application/xml; charset=utf-8"}
            )

        # Fallback
        logger.info(f"Unrecognized input from {sender}: {msg}")
        resp.message("🤖 I didn’t understand that. Type *menu* to start or *restart* to reset.")
        return Response(
            str(resp),
            status=200,
            mimetype="application/xml",
            headers={"Content-Type": "application/xml; charset=utf-8"}
        )

    except Exception as e:
        logger.error(f"🔥 Webhook error for {sender}: {str(e)}")
        resp = MessagingResponse()
        resp.message("⚠️ Server error. Please try again later.")
        return Response(
            str(resp),
            status=500,
            mimetype="application/xml",
            headers={"Content-Type": "application/xml; charset=utf-8"}
        )

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
    app.run(debug=True, host="0.0.0.0", port=5000)