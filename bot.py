import fitz  # PyMuPDF
import re
import os
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Function to download file from a given URL
def download_file(url, filename):
    response = requests.get(url, stream=True)
    with open(filename, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024):
            f.write(chunk)

# Function to extract questions from the PDFPDF
import pytesseract
from pdf2image import convert_from_path

def extract_questions(pdf_path):
    doc = fitz.open(pdf_path)
    extracted_text = ""

    for page in doc:
        text = page.get_text("text")
        if not text.strip():  # If no text, use OCR
            images = convert_from_path(pdf_path)
            for img in images:
                extracted_text += pytesseract.image_to_string(img)
        else:
            extracted_text += text

    # Debug: Print extracted text
    print("Extracted Text:\n", extracted_text[:1000])  

    # Improved Regex
    pattern = re.findall(
        r"Q\.\d+[\s.:]+([\s\S]+?)\nA\)[\s]+([\s\S]+?)\nB\)[\s]+([\s\S]+?)\nC\)[\s]+([\s\S]+?)\nD\)[\s]+([\s\S]+?)\nCorrect Answer:\s*([A-D])",
        extracted_text, re.DOTALL)

    questions = []
    for match in pattern:
        q_text = f"Q. {match[0].strip()}\n"
        q_text += f"A). {match[1].strip()}\nB). {match[2].strip()}\nC). {match[3].strip()}\nD). {match[4].strip()}\n"
        q_text += f"Correct Answer: {match[5]}"
        questions.append(q_text)

    return questions

# Start command handler
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Send me a **PDF file** (max 20MB) or a **Google Drive/Dropbox link** to a larger PDF, and I'll extract questions for you!")

# Handle Google Drive or Dropbox links
def handle_text(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    if "drive.google.com" in text or "dropbox.com" in text:
        update.message.reply_text("Downloading file from the provided link...")
        
        file_path = "downloaded_file.pdf"
        try:
            download_file(text, file_path)
            questions = extract_questions(file_path)
            os.remove(file_path)

            if questions:
                for q in questions[:10]:  # Limit messages
                    update.message.reply_text(q)
            else:
                update.message.reply_text("No valid questions found in the document.")
        except Exception as e:
            update.message.reply_text(f"Failed to download or process the file: {e}")
    else:
        update.message.reply_text("Please send a valid Google Drive or Dropbox link.")

# Handle PDF files (up to 20MB)
def handle_document(update: Update, context: CallbackContext) -> None:
    file = update.message.document
    
    if file.file_size > 20 * 1024 * 1024:  # Check if file is larger than 20MB
        update.message.reply_text("File is too large! Please upload it to Google Drive or Dropbox and share the link.")
        return

    file_path = f"{file.file_id}.pdf"
    file_obj = context.bot.get_file(file.file_id)
    file_obj.download(file_path)

    update.message.reply_text("Extracting questions...")

    questions = extract_questions(file_path)
    os.remove(file_path)

    if questions:
        for q in questions[:10]:
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
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))

    print("Bot is running...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
