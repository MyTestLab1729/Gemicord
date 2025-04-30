import discord
import requests
import base64
import random
import io
import dotenv
import os


dotenv.load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GEMINI_TEXT_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
GEMINI_IMAGE_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp-image-generation:generateContent?key={GEMINI_API_KEY}"

# Discord setup
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

EMOJI_REACTIONS = ["🤖", "✨", "😄", "🔥", "💡", "🌈", "🎨", "📸"]

# TEXT-only Gemini call
def ask_gemini(prompt):
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    response = requests.post(GEMINI_TEXT_API_URL, headers=headers, json=data)
    if response.status_code == 200:
        try:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        except KeyError:
            return "Gemini API responded but no valid text found."
    else:
        return f"Error {response.status_code}: {response.text}"

# TEXT + IMAGE Gemini call
def generate_gemini_content(prompt):
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}
    }
    response = requests.post(GEMINI_IMAGE_API_URL, headers=headers, json=data)
    
    if response.status_code != 200:
        return {"error": f"Error {response.status_code}: {response.text}"}
    
    try:
        parts = response.json()['candidates'][0]['content']['parts']
        result = {"text": None, "image": None}

        for part in parts:
            if "text" in part:
                result["text"] = part["text"]
            elif "inlineData" in part:
                image_data = part["inlineData"]["data"]
                result["image"] = base64.b64decode(image_data)

        return result
    except Exception as e:
        return {"error": str(e)}

@client.event
async def on_ready():
    print(f"Bot is ready. Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    content = message.content.strip()

    if content.startswith("!ask"):
        prompt = content[len("!ask"):].strip()
        if not prompt:
            await message.channel.send("Please provide a prompt after `!ask`.")
            return

        await message.channel.send("Thinking... 🤔")
        response = ask_gemini(prompt)
        MAX_CHARS = 2000
        for i in range(0, len(response), MAX_CHARS):
            msg = await message.channel.send(response[i:i+MAX_CHARS])
            await msg.add_reaction(random.choice(EMOJI_REACTIONS))

    elif content.startswith("!draw"):
        prompt = content[len("!draw"):].strip()
        if not prompt:
            await message.channel.send("Please provide a prompt after `!draw`.")
            return

        await message.channel.send("Creating magic... 🧠🎨")

        result = generate_gemini_content(prompt)
        if "error" in result:
            await message.channel.send(result["error"])
            return

        # Send text if available
        if result["text"]:
            msg = await message.channel.send(result["text"])
            await msg.add_reaction(random.choice(EMOJI_REACTIONS))

        # Send image if available
        if result["image"]:
            image_file = discord.File(io.BytesIO(result["image"]), filename="gemini_image.png")
            await message.channel.send(file=image_file)

client.run(DISCORD_BOT_TOKEN)
