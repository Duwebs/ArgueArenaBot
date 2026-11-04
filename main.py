import os
import time
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from google import genai
from openai import OpenAI
from dotenv import load_dotenv

# Load variables from .env file (for local testing)
load_dotenv()

# Fetch keys securely from environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize AI clients
gemini_client = genai.Client(api_key=GEMINI_API_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Two different AI personas for debate
PERSONA_OPTIMIST = (
    "You are an enthusiastic, futuristic optimist. You look at the bright side, "
    "believe in rapid innovation, and defend technology and progress strongly. "
    "Keep your response concise (2-3 sentences max) and directly challenge or build upon the opponent's previous point."
)

PERSONA_SKEPTIC = (
    "You are a sharp, practical, and sarcastic skeptic. You look for flaws, "
    "risks, hidden costs, and practical failures. "
    "Keep your response concise (2-3 sentences max) and directly counter the opponent's previous point."
)

def generate_gemini_stable(prompt_text):
    """Generate content using the ultra-stable gemini-1.5-flash model"""
    try:
        response = gemini_client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt_text
        )
        if response and response.text:
            return response.text
    except Exception as e:
        raise Exception(f"Gemini Error: {str(e)}")
        
    raise Exception("Gemini response returned empty.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to ArgueArenaBot (Cross-AI Edition)!\n\n"
        "Send me any topic, and Gemini (Optimist) will debate against ChatGPT (Skeptic) live!"
    )

async def handle_debate_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    topic = update.message.text
    
    await update.message.reply_text(f"🥊 **Topic Received:** *{topic}*\n\n🔥 Gemini vs ChatGPT debate starting, please wait...")

    current_argument = topic
    rounds = 3
    
    for i in range(rounds):
        try:
            # --- AI 1: Gemini (Optimist) ---
            gemini_prompt = f"{PERSONA_OPTIMIST}\n\nTopic: {topic}\nPrevious point to counter: {current_argument}"
            
            optimist_text = await asyncio.to_thread(generate_gemini_stable, gemini_prompt)
            current_argument = optimist_text
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"🟢 **Gemini (Optimist - Round {i+1}):**\n{optimist_text}"
            )
            await asyncio.sleep(2)

            # --- AI 2: OpenAI / ChatGPT (Skeptic) ---
            completion = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": PERSONA_SKEPTIC},
                    {"role": "user", "content": f"Topic: {topic}\nPrevious point to counter: {current_argument}"}
                ]
            )
            skeptic_text = completion.choices[0].message.content
            current_argument = skeptic_text
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"🔴 **ChatGPT (Skeptic - Round {i+1}):**\n{skeptic_text}"
            )
            await asyncio.sleep(2)
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error during debate: {str(e)}")
            break

    await update.message.reply_text("🏁 **Debate Finished!** Send a new topic if you want another debate.")

def main():
    if not TELEGRAM_BOT_TOKEN:
        print("❌ Error: TELEGRAM_BOT_TOKEN is missing!")
        return

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_debate_topic))
    
    print("🤖 ArgueArenaBot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
