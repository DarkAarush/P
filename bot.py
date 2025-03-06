import json
import re
import pdfplumber
from telegram import Update, Document
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

TOKEN = "5647751734:AAGf0uUjBf1C7NyqOeeMf1UXy4tQfXAZwro"

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

# Function to extract questions & options
def extract_questions_and_options(text):
    questions = []
    
    # Pattern for multiple-choice questions (MCQs)
    question_pattern = re.compile(r"(\d+\..*?\?)\s*(A\).+?)(B\).+?)(C\).+?)(D\).+?)", re.DOTALL)
    
    for match in question_pattern.findall(text):
        question = match[0].strip()
        options = [opt.strip() for opt in match[1:]]
        questions.append({"question": question, "options": options})
    
    return questions

# Handler for PDF uploads
def handle_document(update: Update, context: CallbackContext):
    file = update.message.document
    if not file.file_name.endswith(".pdf"):
        update.message.reply_text("Please upload a valid PDF file.")
        return
    
    file_path = f"downloads/{file.file_name}"
    file.get_file().download(file_path)
    
    # Extract text from PDF
    pdf_text = extract_text_from_pdf(file_path)
    
    # Extract questions and options
    questions_and_options = extract_questions_and_options(pdf_text)

    if not questions_and_options:
        update.message.reply_text("No questions found in the PDF.")
        return

    # Save to JSON file
    json_path = f"questions/{file.file_name.replace('.pdf', '.json')}"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(questions_and_options, f, indent=4, ensure_ascii=False)

    # Send response to user
    response_text = "**Extracted Questions:**\n\n"
    for idx, item in enumerate(questions_and_options, 1):
        response_text += f"{idx}. {item['question']}\n"
        for opt in item["options"]:
            response_text += f"{opt}\n"
        response_text += "\n"
    
    update.message.reply_text(response_text[:4096])  # Telegram message limit

# Start command
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Send me a PDF with multiple-choice questions, and I'll extract them!")

# Main function to start the bot
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document.mime_type("application/pdf"), handle_document))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
