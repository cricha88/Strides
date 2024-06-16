import streamlit as st
import requests
import base64
import os
import time
import dotenv

dotenv_file = dotenv.find_dotenv()
dotenv.load_dotenv(dotenv_file, override=True)

# SPOTIFY ACCESS TOKENS
client_id_spotify = os.environ.get('CLIENT_ID_MYSPOT')
client_secret_spotify = os.environ.get('CLIENT_SECRET_MYSPOT')

# STRAVA ACCESS TOKENS
client_id_strava = os.environ.get('CLIENT_ID_MYSTRIDE')
client_secret_strava = os.environ.get('CLIENT_SECRET_MYSTRIDE')
access_token_strava = os.environ.get('INITIAL_ACCESS_TOKEN_MYSTRIDE')
refresh_token_strava = os.environ.get('INITIAL_REFRESH_TOKEN_MYSTRIDE')
expires_at = os.environ.get('TOKEN_EXPIRY_MYSTRIDE')

print(expires_at)

# Function to get access token
def get_spotify_access_token(client_id_spotify, client_secret_spotify):
    url = 'https://accounts.spotify.com/api/token'
    headers = {
        'Authorization': 'Basic ' + base64.b64encode((client_id_spotify + ':' + client_secret_spotify).encode('utf-8')).decode('utf-8')
    }
    data = {
        'grant_type': 'client_credentials'
    }
    response = requests.post(url, headers=headers, data=data)
    response_data = response.json()
    return response_data['access_token']

# Function to search for a song
def search_song(access_token, song_name):
    url = 'https://api.spotify.com/v1/search'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    params = {
        'q': song_name,
        'type': 'track',
        'limit': 1
    }
    response = requests.get(url, headers=headers, params=params)
    response_data = response.json()
    if response_data['tracks']['items']:
        track = response_data['tracks']['items'][0]
        return {
            'name': track['name'],
            'artist': track['artists'][0]['name'],
            'album': track['album']['name'],
            'release_date': track['album']['release_date'],
            'spotify_url': track['external_urls']['spotify']
        }
    else:
        return None


def refresh_strava_access_token(client_id, client_secret, refresh_token):
    response = requests.post(
        url='https://www.strava.com/oauth/token',
        data={
            'client_id': client_id_strava,
            'client_secret': client_secret_strava,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token_strava
        }
    )
    
    tokens = response.json()
    
    # Update environment variables
    os.environ['INITIAL_ACCESS_TOKEN_MYSTRIDE'] = tokens['access_token']
    os.environ['INITIAL_REFRESH_TOKEN_MYSTRIDE'] = tokens['refresh_token']
    os.environ['TOKEN_EXPIRY_MYSTRIDE'] = str(tokens['expires_at'])
    dotenv.set_key(dotenv_file, "INITIAL_ACCESS_TOKEN_MYSTRIDE", os.environ['INITIAL_ACCESS_TOKEN_MYSTRIDE'])
    dotenv.set_key(dotenv_file, "INITIAL_REFRESH_TOKEN_MYSTRIDE", os.environ['INITIAL_REFRESH_TOKEN_MYSTRIDE'])
    dotenv.set_key(dotenv_file, "TOKEN_EXPIRY_MYSTRIDE", os.environ['TOKEN_EXPIRY_MYSTRIDE'])
    
    return tokens['access_token'], tokens['refresh_token'], int(tokens['expires_at'])


def get_activities_data(expires_at, client_id_strava, client_secret_strava, access_token_strava, refresh_token_strava):
    current_time = int(time.time())
    expires_at = int(expires_at)
    if current_time >= expires_at:
        print("Access token has expired, refreshing token...")
        access_token_strava, refresh_token_strava, expires_at = refresh_strava_access_token(client_id_strava, client_secret_strava, refresh_token_strava)   
    else:
        print("Access token is still valid.")

    # Use the access token to get athlete data
    endpoint = f"https://www.strava.com/api/v3/athlete/activities?after=1717215795&access_token={access_token_strava}"
    response = requests.get(endpoint)
    
    return response.json()




def main():
    st.title("Match My Stride")

    # Create a text input widget
    user_input = st.text_input("Temporary - enter a song:")

    # Check if user_input is not empty
    if user_input:
        # Call the function to process the input
        song_name = user_input
        
        # Get access token
        spotify_access_token = get_spotify_access_token(client_id_spotify, client_secret_spotify)
        
        # Example usage
        song_details = search_song(spotify_access_token, song_name)

        # Get activities data
        activities = get_activities_data(expires_at, client_id_strava, client_secret_strava, access_token_strava, refresh_token_strava)

        if activities:
            st.write(activities)

        # Display the result
        if song_details:
            st.write(f"Song Name: {song_details['name']}")
            st.write(f"Artist: {song_details['artist']}")
            st.write(f"Album: {song_details['album']}")
            st.write(f"Release Date: {song_details['release_date']}")
            st.write(f"Spotify URL: {song_details['spotify_url']}")
        else:
            st.write(f"No results found for '{song_name}'")



if __name__ == "__main__":
    main()