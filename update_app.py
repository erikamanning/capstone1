from app import CURRENT_SESSION
from get_new_bills import get_new_bills
from get_bill_updates import get_bill_updates


get_new_bills(CURRENT_SESSION, "both", 'introduced')
get_bill_updates('both',CURRENT_SESSION)