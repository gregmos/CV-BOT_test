import logging
import stripe
from flask import Flask, request, Response
from stripe import Webhook
from database import get_db_connection, create_database_schema
from flask import current_app as app

logging.basicConfig(level=logging.INFO)  # Set the logging level


def webhook(app):
    @app.route('/webhook', methods=['POST'])
    def inner_webhook():
        webhook_secret = ''

        payload = request.data
        sig_header = request.headers.get('stripe-signature')

        try:
            event = Webhook.construct_event(payload, sig_header, webhook_secret)
            logging.info("Webhook event constructed")
        except ValueError:
            # Invalid payload
            logging.error("Invalid payload")
            return Response(status=400)
        except stripe.error.SignatureVerificationError:
            # Invalid signature
            logging.error("Invalid signature")
            return Response(status=400)

        # Handle the event
        if event.type == 'checkout.session.completed':
            session = event.data.object
            user_id = session.client_reference_id
            logging.info(f"Updating user balance for user_id: {user_id}")

            # Update user's balance here
            conn = get_db_connection()  # Get the connection from the function
            cursor = conn.cursor()  # Call the cursor() method on the connection object
            cursor.execute("UPDATE users SET cv_balance = cv_balance + 5 WHERE user_id = ?", (user_id,))
            conn.commit()
            logging.info(f"User balance updated for user_id: {user_id}")

        return Response(status=200)
