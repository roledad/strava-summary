"""
Plot the data
"""
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio

from data import decimal_to_time, time_to_decimal, get_run_data

# pylint: disable=C0301
# pylint: disable=W0612

# Set plotly to render in browser
pio.renderers.default = "browser"

def generate_plots(read_date=None):
    """Generates the summary and plot HTML."""
    if read_date is None:
        read_date = datetime.now() - timedelta(days=30)
    run_df = get_run_data(read_date)
    start_date = pd.to_datetime(run_df['start_date_local']).min().date().strftime("%Y-%m-%d")
    end_date = pd.to_datetime(run_df['start_date_local']).max().date().strftime("%Y-%m-%d")
    # Calculate summary statistics
    summary_stats = {
        'Time Period': f"{start_date} ~ {end_date}",
        'Total Distance (miles)': run_df['distance_mile'].sum(),
        'Total Moving Time (hours)': run_df['moving_time_minute'].sum() / 60,
        'Total Elevation Gain (ft)': run_df['total_elevation_gain_ft'].sum(),
        'Average Pace (min/mile)': decimal_to_time(run_df['pace'].apply(time_to_decimal).mean()),
        'Average Heart Rate (bpm)': run_df['average_heartrate'].mean(),
        'Average Watts': run_df['average_watts'].mean()
    }

    summary_html = f"""
        <div class="metric"><strong>Time Period:</strong> {summary_stats['Time Period']}</div>
        <div class="metric"><strong>Number of Runs:</strong> {len(run_df)}</div>
        <div class="metric"><strong>Total Distance:</strong> {summary_stats['Total Distance (miles)']:.1f} miles</div>
        <div class="metric"><strong>Total Moving Time:</strong> {summary_stats['Total Moving Time (hours)']:.1f} hours</div>
        <div class="metric"><strong>Total Elevation Gain:</strong> {summary_stats['Total Elevation Gain (ft)']:.0f} ft</div>
        <div class="metric"><strong>Average Pace:</strong> {summary_stats['Average Pace (min/mile)']} min/mi</div>
        <div class="metric"><strong>Average Heart Rate:</strong> {summary_stats['Average Heart Rate (bpm)']:.1f} bpm</div>
        <div class="metric"><strong>Average Watts:</strong> {summary_stats['Average Watts']:.1f}</div>
    """

    # Define the variables and their bin configurations
    variables_config = {
        'distance_mile': {
            'bins': [0, 3, 6, 9, 12, 15, 18, 20, float('inf')],
            'labels': ['<3', '3-6', '6-9', '9-12', '12-15', '15-18', '18-20', '>20'],
            'title': 'Distance (miles)',
            'xlabel': 'Distance (miles)'
        },
        'moving_time_minute': {
            'bins': [0, 30, 45, 60, 75, 90, 105, 120, float('inf')],
            'labels': ['<30', '30-45', '45-60', '60-75', '75-90', '90-105', '105-120', '>120'],
            'title': 'Moving Time (minutes)',
            'xlabel': 'Time (minutes)'
        },
        'pace': {
            'bins': [0, 7, 8, 9, 10, float('inf')],
            'labels': ['<7', '7-8', '8-9', '9-10', '>10'],
            'title': 'Pace (min/mile)',
            'xlabel': 'Pace (min/mile)'
        },
        'total_elevation_gain_ft': {
            'bins': [0, 50, 150, 250, 350, 450, 550, float('inf')],
            'labels': ['<50', '50-150', '150-250', '250-350', '350-450', '450-550', '>550'],
            'title': 'Elevation Gain (ft)',
            'xlabel': 'Elevation (ft)'
        },
        'average_heartrate': {
            'bins': [0, 140, 150, 160, 170, 180, float('inf')],
            'labels': ['<140', '140-150', '150-160', '160-170', '170-180', '>180'],
            'title': 'Average Heart Rate (bpm)',
            'xlabel': 'Heart Rate (bpm)'
        },
        'average_watts': {
            'bins': [0, 150, 160, 170, 180, 190, 200, 210, float('inf')],
            'labels': ['<150', '150-160', '160-170', '170-180', '180-190', '190-200', '200-210', '>210'],
            'title': 'Average Watts',
            'xlabel': 'Watts'
        }
    }

    # Create subplots
    fig = make_subplots(
        rows=2, cols=3,
        subplot_titles=[config['title'] for config in variables_config.values()]
    )

    # Colors for the bars
    colors = ['skyblue', 'lightgreen', 'lightcoral', 'gold', 'plum', 'lightsteelblue']

    for idx, (var, config) in enumerate(variables_config.items()):
        row = (idx // 3) + 1
        col = (idx % 3) + 1

        plot_data = run_df[var].apply(time_to_decimal) if var == "pace" else run_df[var]
        hist, bin_edges = np.histogram(plot_data, bins=config['bins'])

        percentages = (hist / len(plot_data) * 100).round(1)

        fig.add_trace(
            go.Bar(
                x=config['labels'],
                y=hist,
                name=config['title'],
                marker_color=colors[idx],
                text=[f'{pct}%' if pct > 0 else '' for pct in percentages],
                textposition='auto',
                showlegend=False
            ),
            row=row, col=col
        )

    fig.update_layout(height=800, showlegend=False)

    plot_html = pio.to_html(fig, full_html=False, include_plotlyjs='cdn') # type: ignore

    return summary_html, plot_html

if __name__ == '__main__':
    summary, plot = generate_plots()
    # To test locally, you can save to a file
    with open("local_test.html", "w", encoding="utf-8") as f:
        f.write("<h1>Summary</h1>")
        f.write(summary)
        f.write("<h1>Plot</h1>")
        f.write(plot)
    print("Generated local_test.html")
