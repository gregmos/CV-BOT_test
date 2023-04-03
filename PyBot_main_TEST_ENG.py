import os
import openai
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    CallbackContext,
)
from telegram.ext.filters import Filters
import re
from TEST_PY_TEMPLATE import create_cv_doc
import logging
import stripe
from telegram import Update
from telegram.ext import CallbackContext
from database import create_database_schema, get_db_connection
import threading
from webhook_listener import webhook
from GPT_3 import improve_description, improve_job_duties, improve_achievements
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from flask import Flask

app = Flask(__name__)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Set your token values
TELEGRAM_API_TOKEN = '6038331382:AAFRLHkYrGxkMEemekesDFY6H9JGBo0e8_Y'
OPENAI_API_KEY = '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'
stripe.api_key = "sk_test_51MrQjBKmCidwM5Yfm9kjvE6y1EPa7A7KYBODT8npfmSHLLjYzQaM4RIQU2NuZyhVPEhJlJlpozwwUkO71RMub9DJ00WAkfyKNx"


openai.api_key = OPENAI_API_KEY

FIRST_LAST_NAME, PHONE_NUMBER, EMAIL, ADDRESS, DESCRIPTION, WORK_EXP, WORK_START_DATE, WORK_END_DATE, POSITION, COMPANY_NAME, JOB_DUTIES, ACHIEVEMENTS, EDUCATION, EDUCATION_START_DATE, EDUCATION_END_DATE, UNIVERSITY_NAME, SPECIALITY, LANGUAGE, PROFICIENCY_LEVEL, CREATE_RESUME, PAYMENT, CHECK_BALANCE = range(
    22
)
webhook(app)
app.add_url_rule('/webhook', view_func=webhook, methods=['POST'])
def run_flask_app():
    app.run(port=5000)

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    welcome_message = f"Hello {user.first_name}! Welcome to AI CV Bot.\n\n"\
                      "This bot will help you prepare your CV - every HR manager's dream. To make sure your text is both colourful and professional, we've connected ROBOTS to improve the text you've written.\n\n"\
                      "The bot will ask you questions about your job, education, other details you need for your CV, and will generate a nicely formatted CV at the end. All you have to do is insert a picture.\n\n"\
                      "To get started, simply click one of the buttons below."
    update.message.reply_text(welcome_message)

    keyboard = [
        [InlineKeyboardButton("Create CV", callback_data="create_resume")],
        [InlineKeyboardButton("Top up balance", callback_data="pay")],
        [InlineKeyboardButton("Check balance", callback_data="check_balance")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Please choose:", reply_markup=reply_markup)

def start_payment(update: Update, context: CallbackContext):
    update.callback_query.answer()

    # Create Stripe Checkout session
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'unit_amount': 500,  # Example price: $5.00
                'product_data': {
                    'name': 'CV Bot usage',
                    'description': '5 CV creations',
                },
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url='https://example.com/success',  # Replace with your success URL
        cancel_url='https://example.com/cancel',  # Replace with your cancel URL
    )

    update.effective_message.reply_text("Please click the link below to complete the payment:")
    update.effective_message.reply_text(session.url)

    return ConversationHandler.END


def check_balance(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_first_name = update.effective_user.first_name
    user_last_name = update.effective_user.last_name

    # Get the database connection and cursor
    with app.app_context():
        conn, cursor = get_db_connection()

        cursor.execute("SELECT cv_balance FROM users WHERE user_id = ?", (user_id,))
        user_data = cursor.fetchone()

        if user_data is None:
            cursor.execute("INSERT INTO users (user_id, first_name, last_name, cv_balance) VALUES (?, ?, ?, ?)", (user_id, user_first_name, user_last_name, 0))
            conn.commit()
            balance = 0
        else:
            balance = user_data[0]

    update.callback_query.answer()
    update.effective_message.reply_text(f"Your current balance is: {balance} CV creations")

    # Close the connection
    conn.close()

def create_resume(update: Update, context: CallbackContext):
    user_data = context.user_data
    balance = user_data.get("cv_balance", 0)

    if balance <= 0:
        update.callback_query.answer()
        keyboard = [
            [InlineKeyboardButton("Top up balance", callback_data="pay")],
            [InlineKeyboardButton("Cancel", callback_data="menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.effective_message.reply_text("Your balance is insufficient. Please top up your balance to create a resume.", reply_markup=reply_markup)
    else:
        # Continue with the process of creating a resume
        print("Creating new resume...")
        query = update.callback_query
        query.answer()

        if context.user_data:
            keyboard = [
                [InlineKeyboardButton("Cancel", callback_data="cancel_ongoing_resume")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(
                text="You already have a CV in progress. "
                     "Please cancel the current CV before creating a new one.",
                reply_markup=reply_markup
            )
            return ConversationHandler.END

        query.edit_message_text(text="Enter your first name and last name\n\n(e.g. John Doe):")
        return FIRST_LAST_NAME

def first_last_name(update, context):
    user_input = update.message.text
    context.user_data['first_last_name'] = user_input

    # Print user data to check if phone_number key is added
    print("User data after first_last_name:", context.user_data)

    # Check if phone number already exists in user_data
    if 'phone_number' in context.user_data:
        update.message.reply_text("Enter your email\n\n(e.g. xxxx@xxx.com):")
        return EMAIL

    update.message.reply_text("Enter your phone number\n\n(e.g. +79112345667):")
    return PHONE_NUMBER  # Change this line


def phone_number(update, context):
    user_input = update.message.text

    # Use a regular expression to check if the user has entered a valid phone number format
    pattern = r"^\+?\d{9,15}$"
    if not re.match(pattern, user_input):
        update.message.reply_text("Invalid phone number format. Please enter a valid phone number:")
        return PHONE_NUMBER

    context.user_data['phone_number'] = user_input

    # Print user data to check if phone_number key is added
    print("User data after phone_number:", context.user_data)

    update.message.reply_text("Enter your email\n\n(e.g. xxxx@xxx.com):")
    return EMAIL

def email(update, context):
    user_input = update.message.text
    context.user_data['email'] = user_input

    # Print user data to check if email is added
    print("User data after email:", context.user_data)

    update.message.reply_text("Enter your country and city of residence\n\n(e.g. Cyprus, Nicosia):")
    return ADDRESS

def address(update, context):
    user_input = update.message.text
    context.user_data['address'] = user_input

    # Print user data to check if address is added
    print("User data after address:", context.user_data)

    update.message.reply_text("Enter a short description of yourself as a professional\n\n(e.g. I am a lawyer with 8+ years of experience. I specialize on corporate law, intellectual property matters and data protection. I have experience in both international legal firms and large in-house companies. I have media articles on GDPR problems. Was recognized in Best Lawyers for Information Technology. Have a trademark attorney status.):")
    return DESCRIPTION

def description(update, context):
    user_input = update.message.text
    context.user_data['description'] = improve_description(user_input)

    # Print user data to check if description is added
    print("User data after description:", context.user_data)

    # Combine the message with the "Add work experience" button
    update.message.reply_text("Enter your employment details, starting with the most recent. Click on the 'Add work experience' button:",
                              reply_markup=InlineKeyboardMarkup([
                                  [InlineKeyboardButton("Add work experience", callback_data="add_work_experience")],
                              ]))
    return WORK_EXP

def add_work_experience(update, context):
    query = update.callback_query
    query.answer()
    if 'work_experiences' not in context.user_data:
        context.user_data['work_experiences'] = []

    query.edit_message_text("Specify the year and month you started work\n\n(e.g. 04.2014):")
    return WORK_START_DATE

def work_start_date(update, context):
    user_input = update.message.text
    work_experience = {'start_date': user_input}
    context.user_data['work_experiences'].append(work_experience)
    update.message.reply_text("Specify the month and year when your employment finished\n\n(e.g. 03.2017 or up to now):")
    return WORK_END_DATE

def work_end_date(update, context):
    user_input = update.message.text
    context.user_data['work_experiences'][-1]['end_date'] = user_input
    update.message.reply_text("Enter the title of the position\n\n(e.g. Lawyer):")
    return POSITION

def position(update, context):
    user_input = update.message.text
    context.user_data['work_experiences'][-1]['position'] = user_input
    update.message.reply_text("Enter the company name\n\n(e.g. LLC Innovations and Technologies):")
    return COMPANY_NAME

def company_name(update, context):
    user_input = update.message.text
    context.user_data['work_experiences'][-1]['company_name'] = user_input
    update.message.reply_text("Enter the job duties\n\n(e.g. Conducted legal researches related to various areas of law including, but not limited to, corporate law, commercial law, intellectual property law; Drafted bilingual international agreements (trademark and software licenses, supply agreements, etc.); Coordinated engagements with foreign subcontractors; Represented company in courts;):")
    return JOB_DUTIES

def job_duties(update, context):
    user_input = update.message.text
    context.user_data['work_experiences'][-1]['job_description'] = improve_job_duties(user_input)
    update.message.reply_text("Enter the achievements\n\n(e.g. Developed a strategy for the most appropriate contract scheme relating intellectual property of one of the world's largest beer brewers; Participated in the implementation of the electronics manufacturer restructuring (intellectual property and corporate issues); Successfully completed 3 M&A deals (1 external and 2 internal) involving shares of Cypriot companies):")
    return ACHIEVEMENTS

def achievements(update, context):
    user_input = update.message.text
    if user_input.lower() != 'n/a':
        context.user_data['work_experiences'][-1]['achievements'] = improve_achievements(user_input)
    else:
        context.user_data['work_experiences'][-1]['achievements'] = None
    update.message.reply_text(
        "Choose an option:",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Add another work experience",
                        callback_data="add_another_work_experience",
                    ),
                    InlineKeyboardButton("Go to the next section", callback_data="next_section"),
                ]
            ]
        ),
    )
    return WORK_EXP

def add_another_work_experience(update, context):
    query = update.callback_query
    query.answer()
    query.edit_message_text("Specify the year and month you started work\n\n(e.g. 04.2014):")
    return WORK_START_DATE

def next_section(update, context):
    query = update.callback_query
    query.answer()
    query.edit_message_text(
        "Enter your education details, starting with the most recent. Click on the 'Add Education' button:",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Add Education", callback_data="add_education"
                    )
                ]
            ]
        ),
    )

    return EDUCATION


def add_education(update, context):
    query = update.callback_query
    query.answer()

    if 'educations' not in context.user_data:
        context.user_data['educations'] = []

    query.edit_message_text("Specify the year and month you started study\n\n(e.g. 09.2010):")

    return EDUCATION_START_DATE

def education_start_date(update, context):
    user_input = update.message.text
    education = {'start_date': user_input}
    context.user_data['educations'].append(education)

    update.message.reply_text("Specify the month and year of graduation\n\n(e.g. 07.2014 or 'to date'):")

    return EDUCATION_END_DATE

def education_end_date(update, context):
    user_input = update.message.text
    context.user_data['educations'][-1]['end_date'] = user_input

    update.message.reply_text("Enter the name of university:\n\n(e.g. Harvard University)")

    return UNIVERSITY_NAME

def university_name(update, context):
    user_input = update.message.text
    context.user_data['educations'][-1]['university_name'] = user_input

    update.message.reply_text("Specify your degree\n\n(e.g. Bachelor of Law):")

    return SPECIALITY

def speciality(update, context):
    user_input = update.message.text
    context.user_data['educations'][-1]['speciality'] = user_input

    update.message.reply_text(
        "Choose an option:",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Add another degree", callback_data="add_another_degree"
                    ),
                    InlineKeyboardButton("Go to the next section", callback_data="next_section_languages"),
                ]
            ]
        ),
    )

    return EDUCATION

def add_another_degree(update, context):
    query = update.callback_query
    query.answer()
    query.edit_message_text("Specify the year and month you started study\n\n(e.g. 09.2010):")
    return EDUCATION_START_DATE

def next_section_languages(update, context):
    query = update.callback_query
    query.answer()
    query.edit_message_text(
        "Click on the 'Add Language' button:",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Add Language", callback_data="add_languages"
                    )
                ]
            ]
        ),
    )

    return LANGUAGE

def add_languages(update, context):
    query = update.callback_query
    query.answer()

    if "languages" not in context.user_data:
        context.user_data["languages"] = []

    query.edit_message_text("Enter the language you know\n\n(e.g. English):")

    return LANGUAGE

def language(update, context):
    user_input = update.message.text
    language = {"language": user_input}
    context.user_data["languages"].append(language)

    update.message.reply_text("Enter the proficiency level of the language\n\n(e.g. C1 or Advanced):")

    return PROFICIENCY_LEVEL

def proficiency_level(update, context):
    user_input = update.message.text
    context.user_data["languages"][-1]["proficiency_level"] = user_input

    update.message.reply_text(
        "Choose an option:",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Add another language", callback_data="add_another_language"
                    ),
                    InlineKeyboardButton("Send CV to Me", callback_data="send_cv"),
                ]
            ]
        ),
    )

    return LANGUAGE

def add_another_language(update, context):
    query = update.callback_query
    query.answer()
    query.edit_message_text("Enter the language you know\n\n(e.g. Spanish):")
    return LANGUAGE

def send_cv(update, context):
    print("send_cv function started")
    query = update.callback_query
    query.answer()

    query.edit_message_text("Wait a moment, the robots are working for you.")

    user_data = context.user_data

    document = create_cv_doc(user_data)  # Pass user_data instead of context

    # Save the document without using a temporary file
    output_file_name = "Your AI CV.docx"
    document.save(output_file_name)
    print(f"Output file name: {output_file_name}")
    print("Before sending the document")

    try:
        print("Trying to send the document")
        context.bot.send_document(chat_id=query.message.chat_id, document=open(output_file_name, "rb"))
        print("Document sent successfully")
    except Exception as e:
        print(f"Error while sending document: {e}")
    finally:
        print("Trying to delete the file")
        os.unlink(output_file_name)
        print("File deleted successfully")

    return ConversationHandler.END

def cancel(update, context):
    update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END

def main():
    with app.app_context():
        create_database_schema()

    threading.Thread(target=run_flask_app).start()
    updater = Updater(TELEGRAM_API_TOKEN, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
        ],
        states={
            FIRST_LAST_NAME: [MessageHandler(Filters.text & ~Filters.command, first_last_name)],
            PHONE_NUMBER: [
                MessageHandler(Filters.text & ~Filters.command, phone_number)],
            EMAIL: [MessageHandler(Filters.text & ~Filters.command, email)],
            ADDRESS: [MessageHandler(Filters.text & ~Filters.command, address)],
            DESCRIPTION: [MessageHandler(Filters.text & ~Filters.command, description)],
            WORK_EXP: [
                CallbackQueryHandler(add_work_experience, pattern="^add_work_experience$"),
                CallbackQueryHandler(add_another_work_experience, pattern="^add_another_work_experience$"),
                CallbackQueryHandler(next_section, pattern="^next_section$"),
            ],
            WORK_START_DATE: [MessageHandler(Filters.text & ~Filters.command, work_start_date)],
            WORK_END_DATE: [MessageHandler(Filters.text & ~Filters.command, work_end_date)],
            POSITION: [MessageHandler(Filters.text & ~Filters.command, position)],
            COMPANY_NAME: [MessageHandler(Filters.text & ~Filters.command, company_name)],
            JOB_DUTIES: [MessageHandler(Filters.text & ~Filters.command, job_duties)],
            ACHIEVEMENTS: [MessageHandler(Filters.text & ~Filters.command, achievements)],
            EDUCATION: [
                CallbackQueryHandler(next_section_languages, pattern="^next_section_languages$"),
                CallbackQueryHandler(add_education, pattern="^add_education$"),
                CallbackQueryHandler(add_another_degree, pattern="^add_another_degree$"),
            ],
            EDUCATION_START_DATE: [MessageHandler(Filters.text & ~Filters.command, education_start_date)],
            EDUCATION_END_DATE: [MessageHandler(Filters.text & ~Filters.command, education_end_date)],
            UNIVERSITY_NAME: [MessageHandler(Filters.text & ~Filters.command, university_name)],
            SPECIALITY: [MessageHandler(Filters.text & ~Filters.command, speciality)],
            LANGUAGE: [
                CallbackQueryHandler(add_languages, pattern="^add_languages$"),
                CallbackQueryHandler(add_another_language, pattern="^add_another_language$"),
                CallbackQueryHandler(send_cv, pattern="^send_cv$"),
                MessageHandler(Filters.text & ~Filters.command, language),
            ],
            PROFICIENCY_LEVEL: [MessageHandler(Filters.text & ~Filters.command, proficiency_level)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(create_resume, pattern="^create_resume$"))
    dp.add_handler(CallbackQueryHandler(start_payment, pattern="^pay$"))
    dp.add_handler(CallbackQueryHandler(check_balance, pattern="^check_balance$"))
    dp.add_handler(conv_handler)

    updater.start_polling()

    updater.idle()

if __name__ == "__main__":
    main()