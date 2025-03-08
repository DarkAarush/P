import fitz  # PyMuPDF
import re
import os
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Function to extract questions from the PDF
def extract_questions(pdf_path):
    doc = fitz.open(pdf_path)
    extracted_text = ""

    for page in doc:
        extracted_text += page.get_text()

    # Regex pattern to match questions
    pattern = re.findall(r"Q\.\d+\s+(.+?)\nAns\s+A\)\s+(.+?)\s+B\)\s+(.+?)\s+C\)\s+(.+?)\s+D\)\s+(.+?)\s+Correct Answer:\s+([A-D])", extracted_text)

    questions = []
    for match in pattern:
        q_text = f"Q. {match[0]}\n"
        q_text += f"A). {match[1]}\nB). {match[2]}\nC). {match[3]}\nD). {match[4]}\n"
        q_text += f"Correct Answer: {match[5]}"
        questions.append(q_text)

    return questions

# Start command handler
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Send me a PDF file containing questions, and I'll extract them for you!")

# Handle PDF files
def handle_document(update: Update, context: CallbackContext) -> None:
    file = update.message.document
    if file.mime_type != "application/pdf":
        update.message.reply_text("Please upload a valid PDF file.")
        return

    file_path = f"{file.file_id}.pdf"
    file = context.bot.get_file(file.file_id)
    file.download(file_path)

    update.message.reply_text("Extracting questions...")

    questions = extract_questions(file_path)

    os.remove(file_path)  # Remove file after extraction

    if questions:
        for q in questions:
            update.message.reply_text(q)
    else:
        update.message.reply_text("No valid questions found in the document.")

# Main function
def main():
    TOKEN = "5647751734:AAGf0uUjBf1C7NyqOeeMf1UXy4tQfXAZwro"

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document.mime_type("application/pdf"), handle_document))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
