import os
import time
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from openai import OpenAI
from dotenv import load_dotenv

# Load variables from .env file (for local testing)
load_dotenv()

# Fetch keys securely from environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize Groq client using OpenAI SDK format
client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=GROQ_API_KEY
)

# Two different AI personas for debate using Groq
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

def groq_completion_with_fallback(system_prompt, user_prompt):
    """Try multiple Groq models sequentially so if one fails, the next one takes over"""
    models_to_try = [
        "llama-3.1-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
        "gemma2-9b-it"
    ]
    
    for model_name in models_to_try:
        try:
            completion = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            if completion and completion.choices:
                return completion.choices[0].message.content
        except Exception as e:
            print(f"Model {model_name} failed: {str(e)}")
            continue # Try next model
            
    raise Exception("Sabhi Groq models fail ho gaye hain ya available nahi hain.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to ArgueArenaBot (Groq Multi-Model Edition)!\n\n"
        "Send me any topic, and Groq Optimist will debate against Groq Skeptic live!"
    )

async def handle_debate_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    topic = update.message.text
    
    await update.message.reply_text(f"🥊 **Topic Received:** *{topic}*\n\n🔥 Groq AI vs AI debate starting, please wait...")

    current_argument = topic
    rounds = 3
    
    for i in range(rounds):
        try:
            # --- AI 1: Groq Optimist with Multi-Model Fallback ---
            opt_prompt = f"Topic: {topic}\nPrevious point to counter: {current_argument}"
            optimist_text = await asyncio.to_thread(groq_completion_with_fallback, PERSONA_OPTIMIST, opt_prompt)
            current_argument = optimist_text
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"🟢 **Groq Optimist (Round {i+1}):**\n{optimist_text}"
            )
            await asyncio.sleep(2)

            # --- AI 2: Groq Skeptic with Multi-Model Fallback ---
            skep_prompt = f"Topic: {topic}\nPrevious point to counter: {current_argument}"
            skeptic_text = await asyncio.to_thread(groq_completion_with_fallback, PERSONA_SKEPTIC, skep_prompt)
            current_argument = skeptic_text
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"🔴 **Groq Skeptic (Round {i+1}):**\n{skeptic_text}"
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
    
    print("🤖 ArgueArenaBot is running with Groq Multi-Model Fallback...")
    app.run_polling()

if __name__ == '__main__':
    main()
