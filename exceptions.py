class BusBidderError(Exception):
    category = "GENERAL"

class DataFileError(BusBidderError):        
    category = "DATA_FILE"

class InvalidRecordError(BusBidderError):   
    category = "INVALID_RECORD"

class PaymentError(BusBidderError):
    category = "PAYMENT"

class BookingError(BusBidderError):
    category = "BOOKING"

class SoldOutError(BookingError):
    category = "SOLD_OUT"

class InvalidReferenceError(BookingError):
    category = "INVALID_REFERENCE"

class CancellationError(BusBidderError):
    category = "CANCELLATION"

class ScoringError(BusBidderError):
    category = "SCORING"