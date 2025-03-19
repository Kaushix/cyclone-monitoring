import streamlit as st
import requests
import pandas as pd
import plotly.express as px

st.title("🌪️ Real-Time & Recent Cyclone Monitoring")

# NOAA Real-time Cyclone API
REALTIME_CYCLONE_URL = "https://www.nhc.noaa.gov/CurrentStorms.json"

# IBTrACS dataset (latest available data)
IBTRACS_CSV_URL = "https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r00/access/csv/ibtracs.last3years.list.v04r00.csv"

@st.cache_data(ttl=1800)  # Cache for 30 minutes
def fetch_real_time_cyclones():
    """Fetches real-time active cyclones from NOAA API."""
    try:
        response = requests.get(REALTIME_CYCLONE_URL)
        response.raise_for_status()
        data = response.json()

        active_storms = []
        for storm in data.get("storms", []):
            active_storms.append({
                "Name": storm["name"],
                "Wind Speed (knots)": storm["wind"],
                "Pressure (hPa)": storm["pressure"],
                "Latitude": storm["lat"],
                "Longitude": storm["lon"]
            })

        return pd.DataFrame(active_storms) if active_storms else None
    except requests.exceptions.RequestException as e:
        st.error(f"⚠️ Error fetching real-time cyclone data: {e}")
        return None

@st.cache_data(ttl=86400)  # Cache for 24 hours
def fetch_last_50_cyclones():
    """Fetches the last 50 cyclones from IBTrACS dataset."""
    try:
        df = pd.read_csv(IBTRACS_CSV_URL, skiprows=[1])  # Skip the second row (metadata)

        # Select relevant columns
        df_filtered = df[["NAME", "SEASON", "ISO_TIME", "WMO_WIND", "WMO_PRES", "LAT", "LON"]].dropna()
        df_filtered.rename(columns={"NAME": "Name", "SEASON": "Year", "ISO_TIME": "Date", 
                                    "WMO_WIND": "Wind Speed (knots)", "WMO_PRES": "Pressure (hPa)", 
                                    "LAT": "Latitude", "LON": "Longitude"}, inplace=True)

        # Convert date column to datetime format
        df_filtered["Date"] = pd.to_datetime(df_filtered["Date"])

        # Get the latest 50 cyclones
        last_50_cyclones = df_filtered.sort_values(by="Date", ascending=False).groupby("Name").first().reset_index()
        last_50_cyclones = last_50_cyclones.head(50)  # Limit to the last 50 unique storms

        return last_50_cyclones
    except Exception as e:
        st.error(f"⚠️ Error fetching last 50 cyclones: {e}")
        return None

# Fetch data
real_time_data = fetch_real_time_cyclones()
past_cyclone_data = fetch_last_50_cyclones()

# Display real-time cyclones
if real_time_data is not None:
    st.subheader("📌 Active Cyclones (Real-Time)")
    st.write(real_time_data)

    # Map visualization
    fig1 = px.scatter_mapbox(
        real_time_data,
        lat="Latitude",
        lon="Longitude",
        size="Wind Speed (knots)",
        color="Wind Speed (knots)",
        hover_name="Name",
        zoom=2,
        title="🌍 Real-Time Cyclone Tracking"
    )
    fig1.update_layout(mapbox_style="open-street-map")
    st.plotly_chart(fig1)
else:
    st.success("✅ No active cyclones detected.")

# Display last 50 cyclones
if past_cyclone_data is not None:
    st.subheader("📜 Last 50 Cyclones (Historical)")
    st.write(past_cyclone_data)

    # Line plot of cyclone wind speeds
    fig2 = px.line(
        past_cyclone_data,
        x="Date",
        y="Wind Speed (knots)",
        hover_name="Name",
        title="🌀 Wind Speed of Last 50 Cyclones"
    )
    st.plotly_chart(fig2)
else:
    st.warning("⚠️ Could not retrieve the last 50 cyclones.")
