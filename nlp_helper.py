from textblob import TextBlob

def detect_mood_from_text(text):
    text = text.lower()

    # Keywords (you can expand this)
    mood_keywords = {
        "happy": ["happy", "great", "joy", "fun", "excited", "awesome", "cheerful"],
        "sad": ["sad", "down", "depressed", "low", "unhappy", "cry"],
        "chill": ["chill", "relax", "laid back", "peaceful", "vibe"],
        "romantic": ["love", "romantic", "heart", "crush", "affection"],
        "energetic": ["energy", "hype", "dance", "party", "boost", "power"],
        "calm": ["calm", "soft", "peaceful", "slow", "serene", "ambient"],
        "study": ["study", "focus", "reading", "work", "concentrate"],
        "workout": ["workout", "gym", "run", "exercise", "training"]
    }

    # Check keywords
    for mood, keywords in mood_keywords.items():
        if any(word in text for word in keywords):
            return mood

    # Fallback: sentiment-based
    polarity = TextBlob(text).sentiment.polarity
    if polarity > 0.3:
        return "happy"
    elif polarity < -0.3:
        return "sad"
    else:
        return "chill"  # neutral fallback
