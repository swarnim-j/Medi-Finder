from flask import Flask, render_template, request
import requests
import os
from flask import current_app
from twilio.rest import Client
# from twilio.twiml.voice_response import VoiceResponse

app = Flask(__name__)

app.debug = True

app.config['GOOGLE_MAPS_API_KEY'] = os.environ['GOOGLE_MAPS_API_KEY']
radius = 10000

app.config['TWILIO_PHONE_NUMBER'] = os.environ['TWILIO_PHONE_NUMBER']
app.config['TWILIO_ACCOUNT_SID'] = os.environ['TWILIO_ACCOUNT_SID']
app.config['TWILIO_AUTH_TOKEN'] = os.environ['TWILIO_AUTH_TOKEN']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/hospitals', methods=['POST'])
def hospitals():
    with current_app.app_context():
        api_key = current_app.config['GOOGLE_MAPS_API_KEY']
        lat = request.form['latitude']
        lng = request.form['longitude']
        print(lat, lng)
        url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius={radius}&type=hospital&key={api_key}"
        response = requests.get(url)
        data = response.json()
        hospitals = []
        for result in data['results']:
            hospitals.append({'name': result['name'], 'address': result.get('vicinity', 'Address not available'), 'place_id': result['place_id']})
        return render_template('hospitals.html', hospitals=hospitals, latitude=lat, longitude=lng)

@app.route('/call_hospital', methods=['POST'])
def call_hospital():
    try:
        with current_app.app_context():
            latitude = request.form['latitude']
            longitude = request.form['longitude']
            hospital_place_id = request.form['hospital_place_id']
            # hospital_name = request.form['hospital_name']

            api_key = current_app.config['GOOGLE_MAPS_API_KEY']
            account_sid = current_app.config['TWILIO_ACCOUNT_SID']
            auth_token = current_app.config['TWILIO_AUTH_TOKEN']
            client = Client(account_sid, auth_token)

            # reverse geocoding
            url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={latitude},{longitude}&key={api_key}"
            response = requests.get(url)
            data = response.json()
            print(data['results'])
            address = data["results"][0]["formatted_address"]
            print(address)

            # nearby hospitals
            url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={latitude},{longitude}&radius={radius}&type=hospital&key={api_key}"
            response = requests.get(url)
            data = response.json()
            hospitals = []
            for result in data['results']:
                hospitals.append({'name': result['name'], 'address': result.get('vicinity', 'Address not available'), 'place_id': result['place_id']})

            if hospital_place_id:
                for i, hospital in enumerate(hospitals):
                    if hospital['place_id'] == hospital_place_id:
                        hospitals.pop(i)
                        hospitals.insert(0, hospital)
                        break

            # phone number of hospital
            url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={hospital_place_id}&fields=international_phone_number&key={api_key}"
            response = requests.get(url)
            data = response.json()
            hospital_phone_number = data["result"]["international_phone_number"]

            print(hospital_phone_number)

            message = f"Please send an ambulance as soon as possible to {address}. This is an emergency"

            call = client.calls.create(
                twiml=f'<Response><Say>{message}</Say></Response>',
                to='+919411245121', # to=hospital_phone_number,
                # hospital number changed to mine so that accidental calls to hospitals are avoided
                from_=current_app.config['TWILIO_PHONE_NUMBER']
            )

            return render_template("hospitals.html", hospitals=hospitals, hospital_place_id=hospital_place_id, latitude=latitude, longitude=longitude)
    except Exception as e:
        print(e)
        return render_template("hospitals.html", hospitals=hospitals, hospital_place_id=hospital_place_id, latitude=latitude, longitude=longitude)

        

if __name__ == '__main__':
    app.run(debug=True)