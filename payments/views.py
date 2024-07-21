# utils.py
from paystackapi.paystack import Paystack
import logging
from django.conf import settings
import uuid

logger = logging.getLogger(__name__)
paystack = Paystack(secret_key=settings.PAYSTACK_SECRET_KEY)

def initiate_paystack_transaction(file_upload, payment_amount, user_email=None, callback_url=None):
    unique_id = file_upload.unique_id
    unique_reference = str(uuid.uuid4())  # Generate a unique reference using UUID
    transaction_params = {
        "reference": unique_reference,
        "amount": int(payment_amount * 100),  # Amount in kobo
        "currency": "GHS",
        "metadata": {
            "file_upload_id": file_upload.id,
            "unique_id": unique_id,
        },
        "callback_url": callback_url,
    }

    # Include email in transaction_params only if it is provided
    if user_email:
        transaction_params["email"] = user_email

    try:
        response = paystack.transaction.initialize(**transaction_params)
        logger.debug("Paystack response: %s", response)
        payment_link = response['data']['authorization_url']
        logger.debug("Payment link generated: %s", payment_link)
        return payment_link
    except Exception as e:
        logger.error("Error creating Paystack transaction: %s", str(e))
        logger.error("Paystack response: %s", response)  # Log the full response
        raise

import requests
from django.conf import settings

def verify_paystack_transaction(reference):
    url = f'https://api.paystack.co/transaction/verify/{reference}'
    headers = {
        'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
        'Content-Type': 'application/json',
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        response_data = response.json()
        if response_data['status'] and response_data['data']['status'] == 'success':
            return True, response_data
        else:
            return False, response_data
    else:
        return False, response.json()