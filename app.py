import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

import pandas as pd
from io import BytesIO
import plotly.express as px
import pybaseball as pyb
import math

# https://blog.streamlit.io/make-your-st-pyplot-interactive/
APP_NAME = "Tigers Questionnaire"

# Page Configuration
st.set_page_config(
    page_title=APP_NAME,
    layout="wide",
    initial_sidebar_state="expanded",
)

# plot pitch movement plots using matplotlib
def movement_plots(data):
    fig, ax = plt.subplots(figsize=(5, 5))

    for outcome, df_group in data.groupby('PitchType'):
        ax.scatter(df_group['HorzBreak'], df_group['InducedVerticalBreak'], label=outcome)

    ax.set_xlim(-30, 30)
    ax.set_ylim(-30, 30)
    ax.set_xlabel('PlateX')
    ax.set_ylabel('PlateZ')
    ax.set_title('Movement Plot')
    ax.legend()
    plt.grid(True)

    # add black x and y grid lines
    ax.axhline(0, color='black', linewidth=2)
    ax.axvline(0, color='black', linewidth=2) 

    # save plot as png before displaying it as an image
    buf = BytesIO()
    plt.savefig(buf, format="png")

    with center_column: 
        st.image(buf, use_column_width=True)

# Plot an interactive plot using Plotly
def interactive_movement_plots(data):
    fig = px.scatter(data, x='HorzBreak', y='InducedVerticalBreak',
                    color='PitchType',  
                    hover_data=['ReleaseSpeed','PitchCall'], 
                    title='Movement Plot')

    # add black x and y grid lines
    fig.add_hline(y=0, line_color='black', line_width=2)
    fig.add_vline(x=0, line_color='black', line_width=2)

    # change display so that the x and y ranges are equal
    fig.update_xaxes(showgrid=True, range=[-30, 30])
    fig.update_yaxes(showgrid=True, range=[-30, 30])

    with center_column: 
        st.plotly_chart(fig, use_container_width=True,width=600,height=600)

    
def interactive_hitter_plots(data):

    # Bounds for strikezone found here https://www.baseballprospectus.com/news/article/40891/prospectus-feature-the-universal-strike-zone/
    leftBound = -8.5
    rightBound = 8.5
    lowerBound = 19.5
    upperBound = 41.8

    fig = px.scatter(data, x='PlateX', y='PlateZ',
                    color='LaunchSpeed',  
                    custom_data=['At_Bat_Num','PitchType','LaunchSpeed','LaunchAngle','PitchCall'],
                    title='Hitter Plot')

    # add black x and y grid lines
    fig.add_hline(y=30.65, line_color='black', line_width=2)
    fig.add_vline(x=0, line_color='black', line_width=2)

    fig.update_xaxes(showgrid=True, range=[-24, 24])
    fig.update_yaxes(showgrid=True, range=[7.5, 54])

    # change the format of what is displayed when hovering over datapoint
    fig.update_traces(
        hovertemplate="<br>".join([
            "At-Bat: %{customdata[0]}",
            "Pitch Type: %{customdata[1]}",
            "Launch Speed: %{customdata[2]} mph",
            "Launch Angle: %{customdata[3]} degrees",
            "Result: %{customdata[4]}",        
        ])
    )     

    # add strike zone box
    fig.add_shape(type="rect",
        x0=leftBound, y0=lowerBound, x1=rightBound, y1=upperBound,
        line=dict(color="RoyalBlue"),
        opacity=0.5,
    )
    with center_column:
        st.plotly_chart(fig, use_container_width=True,width=600,height=600)

# code inspiration found from pybaseballs documentation: https://github.com/jldbc/pybaseball/blob/master/pybaseball/plotting.py
# only takes in data where ball is put inplay
def spray_chart(inplay_data,indiv_player):
    # pull stadium plot to overlay hits on
    stadium_img = mpimg.imread('tigers_stadium.png')

    fig, ax = plt.subplots()
    ax.imshow(stadium_img, extent=[-300, 300, -125, 500])

    colorby = 'PitchCall'
    color_label = 'PitchCall'
    legend_title = 'PitchCall'
    size = 60
    
    scatters = []
    for color in inplay_data[color_label].unique():
        color_sub_data = inplay_data[inplay_data[color_label] == color]
        scatters.append(ax.scatter(
            color_sub_data["LandingPositionX"], color_sub_data['LandingPositionY'], size, label=color, alpha=0.5
        ))
        if(indiv_player):
            # Iterate over the rows of color_sub_data to annotate each point
            for _, row in color_sub_data.iterrows():
                ax.annotate(str(row['At_Bat_Num']),  # Convert 'at-bat' to string if it's not already
                            (row["LandingPositionX"], row['LandingPositionY'])
                            )
        
    plt.legend(handles=scatters, title=legend_title, bbox_to_anchor=(1, 1.1), loc='upper left')

    buf = BytesIO()
    plt.savefig(buf, format="png")
    with center_column:
        st.image(buf, use_column_width=True)

# get summary of each of hitters at-bats
def AB_summary(data):
    st.write('\n')
    st.markdown("<h3 style='text-decoration: underline;'>At-Bat Results</h3>", unsafe_allow_html=True)
    for i in range(len(data)):
        st.write(f'AB {i+1} Result: {list(data.PitchCall)[i]} on {list(data.Balls)[i]}-{list(data.Strikes)[i]} count')

# get Batting average, slugging percentage, and on baseb percentage for each player
def hitter_stats(data):
    st.markdown("<h3 style='text-decoration: underline;'>Hitter Stats</h3>", unsafe_allow_html=True)
    in_play_results = list(data.PitchResult)
    
    num_PA = len(data)
    num_AB = num_PA - in_play_results.count("Walk")

    BA = in_play_results.count("Hit") / num_AB
    SLG = sum(data.slg) / num_AB
    OBP = (in_play_results.count("Hit") + in_play_results.count("Walk")) / num_PA

    st.write(f'Batting Average: {BA: .3f}')
    st.write(f'Slugging Percentage: {SLG: .3f}')
    st.write(f'On Base Percentage: {OBP: .3f}')

# get dataframe for either the home team or away team
# if hitter, make hitter_flag 1
def get_team_df(data,hitter_flag):
    home_away = st.sidebar.selectbox("Home or Away Team:", ["Home","Away"])
    if(home_away=='Away'):
        mask = data.Inning_Top_Bottom == 'Top'
    else: 
        mask = data.Inning_Top_Bottom == 'Bottom'

    if(hitter_flag):
        return data[mask]
    else:
        return data[~mask]

# get data for specific pitcher and get specific pitches to display on their plot
def get_pitcher_data(data,option):
    pitcher_data = data[data.PitcherId==option]
    pitches_counts = pitcher_data.PitchType.value_counts()
    pitches = pitches_counts.index.tolist()

    ticker = st.sidebar.multiselect('Select Pitches to Display:', pitches, default=pitches)

    return pitcher_data[pitcher_data.PitchType.isin(ticker)]

data = pd.read_csv('data_new.csv')
title_image_path = 'Tigers_Logo.jpeg'

# Include image and app name on the left sidebar
st.sidebar.image(title_image_path, use_column_width=True)
st.sidebar.title(APP_NAME)

# Allow user to select which charts they want to see 
tab_option = st.sidebar.selectbox("Choose an option", ["Pitcher Movement (Interactive)","Pitcher Movement (Static)","Hitter Plots","Team Hitting Plots"])

    
# Display content based on the selected tab option
if tab_option == "Pitcher Movement (Interactive)":
    st.header("Pitcher Movement (Interactive)")

    # get team data (flag set to 0 since we want pitchers)
    team_data = get_team_df(data,0)

    option = st.selectbox("Choose a Player", options=sorted(team_data.PitcherId.unique()))

    if option:
        left_column, center_column, right_column = st.columns([1, 1, 1])

        # select pitcher and specific pitches
        pitcher_data = get_pitcher_data(team_data,option)
        
        # plot movement plot
        interactive_movement_plots(pitcher_data)

if tab_option == "Pitcher Movement (Static)":
    st.header("Pitcher Movement")

    team_data = get_team_df(data,0)
        
    option = st.selectbox("Choose a Player", options=sorted(team_data.PitcherId.unique()))

    if option:
        left_column, center_column, right_column = st.columns([1, 1, 1])

        # select pitcher and specific pitches
        pitcher_data = get_pitcher_data(team_data,option)

        # plot movement plot
        movement_plots(pitcher_data)

elif tab_option == "Hitter Plots":
    st.header("Hitter Plots")

    team_data = get_team_df(data,1)

    option = st.selectbox("Choose a Player", options=sorted(team_data.BatterId.unique()))
    if option:
        left_column, center_column, right_column = st.columns([1, 1, 1])

        # get dataframe for specific hitter
        hitter_data = team_data[team_data.BatterId==option]
        in_play_data = hitter_data[hitter_data.PitchResult != 'Not In-Play']

        # put at-bat summary in the left column and game statisitcs in the right column
        with left_column:
            AB_summary(in_play_data)

        with right_column:
            hitter_stats(in_play_data)

        # allow user to select which at-bats to see
        ABs = sorted(hitter_data.At_Bat_Num.unique())
        ticker = st.sidebar.multiselect('Choose At-Bats to Display:', ABs, default=ABs)
        hitter_data = hitter_data[hitter_data.At_Bat_Num.isin(ticker)]

        # plot hitter plot and spray chart
        interactive_hitter_plots(hitter_data)
        spray_chart(hitter_data[((hitter_data.PitchResult != 'Walk') & (hitter_data.PitchResult != 'Not In-Play') & (hitter_data.PitchCall!='strikeout'))],1)


elif tab_option == 'Team Hitting Plots':
    st.header("Team Hitter Plots")
    team_data = get_team_df(data,1)

    left_column, center_column, right_column = st.columns([1, 1, 1])
    in_play_data = team_data[team_data.PitchResult != 'Not In-Play']

    with right_column:
        hitter_stats(in_play_data)

    interactive_hitter_plots(team_data)
    with left_column:
        spray_chart(team_data[((team_data.PitchResult != 'Walk') & (team_data.PitchResult != 'Not In-Play') & (team_data.PitchCall!='strikeout'))],0)