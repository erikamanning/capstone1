from app import db, headers, CURRENT_CONGRESS_SESSION
from models import Bill
import requests
from get_app_data.get_bill_data_utility_functions import create_bill, get_slugs, get_bill_data

def get_all_slugs(congress, chamber):

    all_slugs = []
    total = 20
    i = 0
    length = 20

    while length >= 20:

        offset = total * i
        req = requests.get(f'https://api.propublica.org/congress/v1/{congress}/{chamber}/bills/introduced.json?offset={offset}', headers=headers)

        json = req.json()

        bill_data = json["results"][0]['bills']

        slugs = get_slugs(bill_data)

        length = len(slugs)

        for slug in slugs:
            all_slugs.append(slug)

        i+=1
    
    return all_slugs

def get_some_slugs(congress, chamber, status, max_offset):

    all_slugs = []
    total = 20
    i = 0
    length = 20

    while i <= max_offset:

        offset = total * i

        req = requests.get(f'https://api.propublica.org/congress/v1/{congress}/{chamber}/bills/{status}.json?offset={offset}', headers=headers)

        json = req.json()

        bill_data = json["results"][0]['bills']

        slugs = get_slugs(bill_data)

        for slug in slugs:
            all_slugs.append(slug)

        i+=1

    return all_slugs


# get all bill data from the current congressional session.
current_senate_slugs = get_all_slugs(CURRENT_CONGRESS_SESSION, "both")
get_bill_data(current_senate_slugs, CURRENT_CONGRESS_SESSION)

