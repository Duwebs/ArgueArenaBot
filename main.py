import os
import time
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import google.generativeai as genai
from dotenv import load_dotenv

# Load variables from .env file (for local testing)
load_dotenv()

# Fetch keys securely from environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure classic genai
genai.configure(api_key=GEMINI_API_KEY)

# Use the classic stable model name
generation_config = {
    "temperature": 0.9,
    "max_output_tokens": 150,
}
model = genai.GenerativeModel(model_name="gemini-1.5-flash", generation_config=generation_config)

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

def generate_classic_gemini(system_prompt, user_prompt):
    """Generate response using classic google-generativeai SDK"""
    full_prompt = f"{system_prompt}\n\n{user_prompt}"
    try:
        response = model.generate_content(full_prompt)
        if response and response.text:
            return response.text
    except Exception as e:
        raise Exception(f"Gemini Classic Error: {str(e)}")
        
    raise Exception("Empty response from Gemini.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to ArgueArenaBot (Classic Edition)!\n\n"
        "Send me any topic, and Optimist will debate against Skeptic live on Telegram!"
    )

async def handle_debate_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    topic = update.message.text
    
    await update.message.reply_text(f"🥊 **Topic Received:** *{topic}*\n\n🔥 Live Telegram debate starting, please wait...")

    current_argument = topic
    rounds = 3
    
    for i in range(rounds):
        try:
            # --- AI 1: Optimist ---
            opt_prompt = f"Topic: {topic}\nPrevious point to counter: {current_argument}"
            optimist_text = await asyncio.to_thread(generate_classic_gemini, PERSONA_OPTIMIST, opt_prompt)
            current_argument = optimist_text
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"🟢 **Optimist (Round {i+1}):**\n{optimist_text}"
            )
            await asyncio.sleep(2)

            # --- AI 2: Skeptic ---
            skep_prompt = f"Topic: {topic}\nPrevious point to counter: {current_argument}"
            skeptic_text = await asyncio.to_thread(generate_classic_gemini, PERSONA_SKEPTIC, skep_prompt)
            current_argument = skeptic_text
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"🔴 **Skeptic (Round {i+1}):**\n{skeptic_text}"
            )
            await asyncio.sleep(2)
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error during debate: {str(e)}")
            break

    await update.message.reply_text("🏁 **Debate Finished!** Send another topic for a new round.")

def main():
    if not TELEGRAM_BOT_TOKEN:
        print("❌ Error: TELEGRAM_BOT_TOKEN is missing!")
        return

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_debate_topic))
    
    print("🤖 ArgueArenaBot Classic is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
