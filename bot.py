import os
import fitz  # PyMuPDF
import re
import pytesseract
from pdf2image import convert_from_path
import pdfplumber
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# 🔹 (Windows Only) Set Tesseract Path
# Uncomment if using Windows and update the path
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ✅ Function to extract text from normal PDFs
def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            text += page.get_text("text") + "\n"
    except Exception as e:
        print(f"❌ Error using PyMuPDF: {e}")

    if not text.strip():
        print("⚠ No text found with PyMuPDF. Trying pdfplumber...")
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = "\n".join([page.extract_text() or "" for page in pdf.pages])
        except Exception as e:
            print(f"❌ Error using pdfplumber: {e}")

    return text.strip()

# ✅ Function to extract text using OCR (for scanned PDFs)
def extract_text_from_scanned_pdf(pdf_path):
    text = ""
    try:
        images = convert_from_path(pdf_path)
        for img in images:
            text += pytesseract.image_to_string(img) + "\n"
    except Exception as e:
        print(f"❌ OCR Extraction Failed: {e}")

    return text.strip()

# ✅ Function to extract questions from the text
def extract_questions(pdf_path):
    text = extract_text_from_pdf(pdf_path)

    if not text:
        print("⚠ No text found in PDF. Trying OCR...")
        text = extract_text_from_scanned_pdf(pdf_path)

    if not text:
        print("❌ No text extracted, even with OCR.")
        return []

    print("\n🔍 Extracted Text (First 500 chars):")
    print(text[:50000])  # Debugging output

    # 🔹 Improved regex for different formats
    pattern = re.findall(
        r"Q(?:\.|\s)?\d+[\s.:]+([\s\S]+?)\nA\)[\s]+([\s\S]+?)\nB\)[\s]+([\s\S]+?)\nC\)[\s]+([\s\S]+?)\nD\)[\s]+([\s\S]+?)\nCorrect Answer:\s*([A-D])",
        text, re.DOTALL
    )

    if not pattern:
        print("⚠ No questions found with regex. Check text format.")

    questions = []
    for match in pattern:
        q_text = f"Q. {match[0].strip()}\n"
        q_text += f"A). {match[1].strip()}\nB). {match[2].strip()}\nC). {match[3].strip()}\nD). {match[4].strip()}\n"
        q_text += f"Correct Answer: {match[5]}"
        questions.append(q_text)

    return questions

# ✅ Start command handler
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Send me a PDF file containing questions, and I'll extract them for you!")

# ✅ Handle incoming PDF files
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

    os.remove(file_path)  # Cleanup

    if questions:
        for q in questions[:5]:  # Send first 5 questions (avoid spam)
            update.message.reply_text(q)
        if len(questions) > 5:
            update.message.reply_text(f"...and {len(questions) - 5} more questions found!")
    else:
        update.message.reply_text("No valid questions found in the document.")

# ✅ Main function to start the bot
def main():
    TOKEN = "5647751734:AAGf0uUjBf1C7NyqOeeMf1UXy4tQfXAZwro"  # 🔹 Replace with your actual Telegram Bot Token

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document.mime_type("application/pdf"), handle_document))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
