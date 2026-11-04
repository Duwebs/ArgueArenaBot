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
HF_TOKEN = os.getenv("HF_TOKEN")

# Initialize Hugging Face client using OpenAI SDK format (Serverless Inference API)
client = OpenAI(
    base_url="https://api-inference.huggingface.co/v1",
    api_key=HF_TOKEN
)

# Two different AI personas for debate using Llama
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

def hf_completion(system_prompt, user_prompt):
    """Generate content using Hugging Face serverless router"""
    try:
        completion = client.chat.completions.create(
            model="meta-llama/Llama-3.3-70b-Instruct",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=150
        )
        if completion and completion.choices:
            return completion.choices[0].message.content
    except Exception as e:
        raise Exception(f"Hugging Face Error: {str(e)}")
        
    raise Exception("Hugging Face response returned empty.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to ArgueArenaBot (Hugging Face Edition)!\n\n"
        "Send me any topic, and Llama Optimist will debate against Llama Skeptic live!"
    )

async def handle_debate_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    topic = update.message.text
    
    await update.message.reply_text(f"🥊 **Topic Received:** *{topic}*\n\n🔥 Llama AI vs AI debate starting, please wait...")

    current_argument = topic
    rounds = 3
    
    for i in range(rounds):
        try:
            # --- AI 1: Llama as Optimist ---
            opt_prompt = f"Topic: {topic}\nPrevious point to counter: {current_argument}"
            optimist_text = await asyncio.to_thread(hf_completion, PERSONA_OPTIMIST, opt_prompt)
            current_argument = optimist_text
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"🟢 **Llama Optimist (Round {i+1}):**\n{optimist_text}"
            )
            await asyncio.sleep(2)

            # --- AI 2: Llama as Skeptic ---
            skep_prompt = f"Topic: {topic}\nPrevious point to counter: {current_argument}"
            skeptic_text = await asyncio.to_thread(hf_completion, PERSONA_SKEPTIC, skep_prompt)
            current_argument = skeptic_text
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"🔴 **Llama Skeptic (Round {i+1}):**\n{skeptic_text}"
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
    
    print("🤖 ArgueArenaBot is running with Hugging Face...")
    app.run_polling()

if __name__ == '__main__':
    main()
