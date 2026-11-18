import re

OFFER_ID_RE    = re.compile(r"^[A-Z]{2}-\d{3,}$")                                   # SO-101
BOOKING_REF_RE = re.compile(r"^[A-Z]{2}-\d{3,}-[A-Za-zÀ-ÿ ]{2,40}-\d{3,}-\d{3,}$")  # SO-101-Raol-101-105
TIME_RE        = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")                           # 08:30
BUS_CODE_RE    = re.compile(r"^[A-Z]{3}$")                                          # SOL
LUGGAGE_RE     = re.compile(r"^[1-9]\d* bags?$")                                    # 2 bags
CARD_RE        = re.compile(r"^\d{16}$")
EXPIRY_RE      = re.compile(r"^(0[1-9]|1[0-2])/\d{2}$")
CVV_RE         = re.compile(r"^\d{3,4}$")