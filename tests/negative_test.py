import requests
import json
from pages.common import Common 

user_details_invalid_name = json.load(open("./test-data/invalid/user_details_invalid_name.json"))
user_details_invalid_json = json.load(open("./test-data/invalid/user_details_invalid_json.json"))
user_details_missing_date = json.load(open("./test-data/invalid/user_details_missing_date.json"))
invalid_token_auth_credentials = json.load(open("./test-data/invalid/invalid_token_auth_credentials.json"))
update = json.load(open("./test-data/valid/update_body.json"))

common = Common()

def test_cannot_create_booking_invalid_name(base_url):
    url = base_url + "/booking"
    create_booking = requests.post(url, json=user_details_invalid_name)
    assert create_booking.status_code == 500

def test_cannot_create_booking_invalid_json(base_url):
    url = base_url + "/booking"
    create_booking = requests.post(url, json=user_details_invalid_json)
    assert create_booking.status_code == 500

def test_cannot_create_booking_missing_date(base_url):
    url = base_url + "/booking"
    create_booking = requests.post(url, json=user_details_missing_date)
    assert create_booking.status_code == 500

def test_cannot_create_token_invalid_credentials(base_url):
    create_token = common.create_token(base_url, invalid_token_auth_credentials)
    assert create_token.status_code == 200
    data = create_token.json()
    assert data['reason'] == 'Bad credentials'

def test_cannot_update_booking_invalid_token(base_url):
    url = base_url + "/booking/1"

    update_booking = requests.put(url, json = update, headers= { 'Cookie': 'token=123abc' })
    assert update_booking.status_code == 403

def test_cannot_delete_booking_invalid_token(base_url):
    url = base_url + "/booking/1"

    delete_booking = requests.delete(url, headers= { 'Cookie': 'token=123abc' })
    assert delete_booking.status_code == 403
