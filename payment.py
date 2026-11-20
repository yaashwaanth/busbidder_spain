

from exceptions import PaymentError
# from logging import get_logger
from cust_logging import get_logger
from regex_patters import CARD_RE, EXPIRY_RE, CVV_RE

log = get_logger()


def validate_card(number, expiry, cvv):
    digits = number.replace(" ", "")
    if not CARD_RE.match(digits):
        raise PaymentError("Card number must be 16 digits.")
    if not EXPIRY_RE.match(expiry.strip()):
        raise PaymentError("Expiry must be in MM/YY format.")
    if not CVV_RE.match(cvv):
        raise PaymentError("CVV must be 3 or 4 digits.")
    return digits


def log_payment(traveller_id, offer_id, amount, digits):

    log.info("Payment accepted: traveller=%s offer=%s amount=%.2f card=****%s",
             traveller_id, offer_id, amount, digits[-4:])