import requests
import json

user_details = json.load(open("./test-data/valid/user_details.json"))
token_auth_credentials = json.load(open("./test-data/valid/token_auth_credentials.json"))
partial_update = json.load(open("./test-data/valid/partial_update_body.json"))
update = json.load(open("./test-data/valid/update_body.json"))

class Common:
    def test_create_new_booking(self, base_url):
        url = base_url + "/booking"
        response = requests.post(url, json=user_details)

        assert response.status_code == 200
        data = response.json()
        assert data['booking']['firstname'] == user_details['firstname']
        booking_id = data['bookingid']

        return booking_id
    
    def create_token(self, base_url, data):
        url = base_url + "/auth"
        auth = requests.post(url, json=data)
        return auth