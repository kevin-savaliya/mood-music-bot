from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    msg = request.form.get("Body")
    resp = MessagingResponse()

    if "sad" in msg.lower():
        reply = "Cheer up! Here's a playlist for you 🎶"
    else:
        reply = "Hi! Send me your mood and I’ll share music 🎧"

    resp.message(reply)
    return str(resp)

if __name__ == "__main__":
    app.run()
