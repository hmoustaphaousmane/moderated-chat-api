from google import genai
from google.genai import types
import sys

MODEL_ID = "gemini-2.5-flash"

SYSTEM_PROMPT = ("""
    You are a helpful and positive assistant.
    Your primary goal is to provide concise, friendly, and informative answers.
    You must always adhere strictly to all safety policies and never provide harmful instructions.
    """
)

# List of banned keywords for basic moderation
BANNED_KEYWORDS = [
    'kill', 'murder', 'assassinate', 'harm', 'hurt',
    'hack', 'exploit', 'breach', 'unauthorized access',
    'bomb', 'explosive', 'weapon', 'terrorist',
    'hate', 'discriminate', 'racist', 'sexist'
]

# Safety configuration (additional Gemini built-in moderation)
SAFETY_SETTINGS = [
    types.SafetySetting(
        category="HARM_CATEGORY_DANGEROUS_CONTENT",
        threshold="BLOCK_LOW_AND_ABOVE",
    ),
]

# moderation
def violates_policy(text: str) -> bool:
    """Check if text contains any banned keywords."""
    text_lower = text.lower()
    return any(word in text_lower for word in BANNED_KEYWORDS)

def redact_text(text: str) -> str:
    """Redact banned keywords from text output."""
    redacted = text
    for word in BANNED_KEYWORDS:
        redacted = redacted.replace(word, "*")
    return redacted


def chat_with_gemini(user_prompt: str):
    """Send moderated user input to Gemini and handle moderation on output."""
    
    # Input moderation
    if violates_policy(user_prompt):
        print("Your input violated the moderation policy. Please rephrase.")
        return

    # Initialize Gemini client
    try:
        client = genai.Client()
    except Exception as e:
        print(f"Failed to initialize Gemini client: {e}")
        sys.exit(1)

    # Combine system and user prompts
    combined_prompt = f"{SYSTEM_PROMPT}\n\nUser: {user_prompt}\nAssistant:"

    # Generate model response
    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=combined_prompt,
            config=types.GenerateContentConfig(
                safety_settings=SAFETY_SETTINGS,
            ),
        )
    except Exception as e:
        print(f"API call failed: {e}")
        return

    # Extract model text
    ai_text = response.text or "(No response returned.)"

    # Output moderation
    if violates_policy(ai_text):
        print("Output contained restricted terms. Showing redacted version:\n")
        ai_text = redact_text(ai_text)

    print("\nGemini says:\n" + ai_text)


if __name__ == "__main__":
    try:
        prompt = input("Enter your prompt: ").strip()
        chat_with_gemini(prompt)
    except KeyboardInterrupt:
        print("\nSession cancelled.")
