import streamlit as st
import requests
import base64
import os

# Replace these with your client ID and client secret
client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')

# Function to get access token
def get_access_token(client_id, client_secret):
    url = 'https://accounts.spotify.com/api/token'
    headers = {
        'Authorization': 'Basic ' + base64.b64encode((client_id + ':' + client_secret).encode('utf-8')).decode('utf-8')
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

def main():
    st.title("Match My Stride")

    # Create a text input widget
    user_input = st.text_input("Temporary - enter a song:")

    # Check if user_input is not empty
    if user_input:
        # Call the function to process the input
        song_name = user_input
        
        # Get access token
        access_token = get_access_token(client_id, client_secret)
        
        # Example usage
        song_details = search_song(access_token, song_name)

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