import pytest
import requests
import json
from pages.common import Common 

user_details = json.load(open("./test-data/valid/user_details.json"))
token_auth_credentials = json.load(open("./test-data/valid/token_auth_credentials.json"))
partial_update = json.load(open("./test-data/valid/partial_update_body.json"))
update = json.load(open("./test-data/valid/update_body.json"))

common = Common()
token = ''

@pytest.fixture(autouse=True)
def test_create_token(base_url):
    global token
    auth = common.create_token(base_url, token_auth_credentials)
    assert auth.status_code == 200
    token_json = auth.json()
    token = token_json['token']
    return token

def test_health_check(base_url):
    url = base_url + "/ping"
    ping = requests.get(url)
    assert ping.status_code == 201

def test_get_booking_ids(base_url):
    url = base_url + "/booking"
    get_booking_ids = requests.get(url)
    assert get_booking_ids.status_code == 200

def test_create_booking(base_url):
    url = base_url + "/booking"
    create_booking = requests.post(url, json=user_details)
    assert create_booking.status_code == 200
    data = create_booking.json()
    assert data['booking']['firstname'] == user_details['firstname']

def test_get_newly_created_booking(base_url):
    booking_id = common.test_create_new_booking(base_url)
    url = base_url + "/booking/" + str(booking_id)

    get_booking = requests.get(url)
    assert get_booking.status_code == 200

def test_update_booking(base_url):
    booking_id = common.test_create_new_booking(base_url)
    url = base_url + "/booking/" + str(booking_id)

    update_booking = requests.put(url, json = update, headers= { 'Cookie': 'token=' + token })
    assert update_booking.status_code == 200
    data = update_booking.json()
    assert data['additionalneeds'] == update['additionalneeds']


def test_partial_update_booking(base_url):
    booking_id = common.test_create_new_booking(base_url)
    url = base_url + "/booking/" + str(booking_id)

    partial_update_booking = requests.patch(url, json = partial_update, headers= { 'Cookie': 'token=' + token })
    assert partial_update_booking.status_code == 200
    data = partial_update_booking.json()
    assert data['totalprice'] == partial_update['totalprice']

def test_delete_booking(base_url):
    booking_id = common.test_create_new_booking(base_url)
    url = base_url + "/booking/" + str(booking_id)

    delete_booking = requests.delete(url, headers= { 'Cookie': 'token=' + token })
    assert delete_booking.status_code == 201
    get_booking = requests.get(url)
    assert get_booking.status_code == 404
