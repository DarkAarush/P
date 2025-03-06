import pdfplumber
import re
import json
import os
from pyrogram import Client, filters
from pyrogram.types import Message

# Bot credentials (replace with your own)
API_ID = "25638120"
API_HASH = "3b702ecd94ca01b76c1b78451a33833c"
BOT_TOKEN = "5647751734:AAGf0uUjBf1C7NyqOeeMf1UXy4tQfXAZwro"

bot = Client("QuizBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Extract MCQs from PDF
def extract_quiz_questions(pdf_path):
    quiz_data = []
    question_pattern = re.compile(r"^\d+\..*")  # Matches "1. What is..."
    option_pattern = re.compile(r"^[A-D]\).*")  # Matches "A) Option"

    with pdfplumber.open(pdf_path) as pdf:
        question_data = None

        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            lines = text.split("\n")
            for line in lines:
                line = line.strip()

                if question_pattern.match(line):
                    if question_data and len(question_data["options"]) >= 2:
                        quiz_data.append(question_data)
                    question_data = {"question": line, "options": [], "correct_option_id": None}

                elif option_pattern.match(line) and question_data:
                    question_data["options"].append(line[3:].strip())  # Remove "A) ", "B) " etc.

                    # Detect correct answer (if marked with *)
                    if "*" in line:
                        question_data["correct_option_id"] = len(question_data["options"]) - 1

        if question_data and len(question_data["options"]) >= 2:
            quiz_data.append(question_data)

    return quiz_data

# Handle PDF Uploads
@bot.on_message(filters.document & filters.private)
async def handle_pdf(client, message: Message):
    pdf_file = await message.download()
    quiz_questions = extract_quiz_questions(pdf_file)

    if not quiz_questions:
        await message.reply("❌ No valid quiz questions found!")
        os.remove(pdf_file)
        return

    json_file = pdf_file.replace(".pdf", ".json")
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(quiz_questions, f, ensure_ascii=False, indent=4)

    await message.reply_document(json_file, caption="✅ Extracted quiz data!")
    os.remove(pdf_file)
    os.remove(json_file)

# Start the bot
bot.run()
