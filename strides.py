# IMPORTS
import streamlit as st
import requests
import base64
import os
import time
from datetime import datetime, timedelta
import dotenv
import pandas as pd
import plotly.express as px
from pandasai import SmartDataframe
from pandasai.llm.openai import OpenAI

# LOAD ENV VARIABLES FOR TOKENS
dotenv_file = dotenv.find_dotenv()
dotenv.load_dotenv(dotenv_file, override=True)

# REFRESH STRAVA ACCESS TOKEN (NOT IN USE)
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
    print(tokens)
    
    # Update environment variables
    os.environ['INITIAL_ACCESS_TOKEN_MYSTRIDE'] = tokens['access_token']
    os.environ['INITIAL_REFRESH_TOKEN_MYSTRIDE'] = tokens['refresh_token']
    os.environ['TOKEN_EXPIRY_MYSTRIDE'] = str(tokens['expires_at'])
    dotenv.set_key(dotenv_file, "INITIAL_ACCESS_TOKEN_MYSTRIDE", os.environ['INITIAL_ACCESS_TOKEN_MYSTRIDE'])
    dotenv.set_key(dotenv_file, "INITIAL_REFRESH_TOKEN_MYSTRIDE", os.environ['INITIAL_REFRESH_TOKEN_MYSTRIDE'])
    dotenv.set_key(dotenv_file, "TOKEN_EXPIRY_MYSTRIDE", os.environ['TOKEN_EXPIRY_MYSTRIDE'])
    
    return tokens['access_token'], tokens['refresh_token'], int(tokens['expires_at'])

# REFRESH STRAVA DATA (NOT IN USE)
def get_activities_data():
    # STRAVA ACCESS TOKENS
    client_id_strava = os.environ.get('CLIENT_ID_MYSTRIDE')
    client_secret_strava = os.environ.get('CLIENT_SECRET_MYSTRIDE')
    access_token_strava = os.environ.get('INITIAL_ACCESS_TOKEN_MYSTRIDE')
    refresh_token_strava = os.environ.get('INITIAL_REFRESH_TOKEN_MYSTRIDE')
    expires_at = os.environ.get('TOKEN_EXPIRY_MYSTRIDE')    
    
    current_time = int(time.time())
    expires_at = int(expires_at)
    if current_time >= expires_at:
        print("Access token has expired, refreshing token...")
        access_token_strava, refresh_token_strava, expires_at = refresh_strava_access_token(client_id_strava, client_secret_strava, refresh_token_strava)   
    else:
        print("Access token is still valid.")

    # Append last 30 days of activities data
    thirty_days_ago = datetime.now() - timedelta(days=30)
    thirty_days_ago_unix = int(thirty_days_ago.timestamp())
    
    # Use the access token to get athlete data
    endpoint = f"https://www.strava.com/api/v3/athlete/activities?after={thirty_days_ago_unix}&access_token={access_token_strava}"
    response = requests.get(endpoint)
    
    return response.json()


def get_llm():
    try:
        # OPENAI TOKENS
        OPENAI_KEY = os.environ.get('OPENAI_TOKEN')
        # CREATE LLM
        llm_model = OpenAI(api_token=OPENAI_KEY)
        return llm_model
    except:
        return None

# MAIN STREAMLIT APP
def main():
    st.set_page_config(layout="wide")

    st.title('Strides')
    st.text('A personal strava data assistant')

    # Read anonymized csv
    df_activities = pd.read_csv('my_activities_anonymized.csv')

    # Convert date to datetime and extract month as new column
    df_activities['timestamp'] = pd.to_datetime(df_activities['start_date_local'])
    df_activities['month'] = df_activities['timestamp'].dt.month

    st.subheader('Overview of Activities Over Time')

    # Create pie chart of activities overall
    activity_counts = df_activities.groupby(['type']).size().reset_index(name='activity_counts')
    fig_pie = px.pie(activity_counts, values='activity_counts', names='type', color_discrete_sequence=px.colors.sequential.RdBu, title='Breakdown by Activity Counts')

    # Create the line plot of activities over time
    fig_hist = px.histogram(df_activities, x='timestamp', color = 'type', color_discrete_sequence=px.colors.sequential.RdBu, title='Activities Over Time')

    # Display the two plots side by side
    col1, col2 = st.columns(2)
    col1.plotly_chart(fig_pie)
    col2.plotly_chart(fig_hist)

    st.subheader('Interactive Stats over Time')

    # Allow user to select y axis
    stat_to_plot = st.selectbox(
        'Select the statistic to plot on y axis:',
        ('average_speed',
        'average_heartrate',
        'distance',
        'total_elevation_gain'
        )    
    )
    
    # Allow user to select variable for color gradient
    stat_for_gradient = st.selectbox(
        'Select the statistic to visualize via color gradient:',
        ('average_heartrate',
        'average_speed',     
        'distance',
        'total_elevation_gain'
        )    
    )

    # Create the scatter plot
    fig = px.scatter(df_activities[df_activities['type'] == 'Run'], x='timestamp', y=stat_to_plot, color = stat_for_gradient, color_continuous_scale=px.colors.sequential.RdBu_r, 
                labels={'timestamp': 'Timestamp', stat_to_plot: stat_to_plot.capitalize(), 'type': 'Activity Type'},
                title=f'{stat_to_plot.capitalize()} Over Time')
    
    # Show the plot 
    st.plotly_chart(fig)

    st.subheader('Chat with the Data')

    # Show the dataframe to the user
    st.write(df_activities.head(3))


    # ALLOW USER TO ENTER
    prompt = st.text_area("Enter your prompt for analysis of this dataset:")

    if st.button("Generate"):
        if prompt:
            with st.spinner("Generating a response, please wait..."):
                llm_model = get_llm()
                df_smart = SmartDataframe(df_activities, config={"llm": llm_model})
                if llm_model != None:
                    st.write(df_smart.chat(prompt))
                else:
                    st.warning("OpenAI Token is not accessible.")

        else:
            st.warning("Please enter a prompt.")
        

if __name__ == "__main__":
    main()