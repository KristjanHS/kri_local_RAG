import numpy as np
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Dew‑point calculation using Magnus‑Tetens approximation
# ---------------------------------------------------------------------------
a_const: float = 17.625
b_const: float = 243.04


def calculate_dew_point(temp_c: float, rh: float) -> float:
    """Return dew‑point (°C) for given temperature (°C) and RH (0‑100 %)."""
    alpha = np.log(rh / 100.0) + (a_const * temp_c) / (b_const + temp_c)
    return (b_const * alpha) / (a_const - alpha)


# ---------------------------------------------------------------------------
# Grid definition — higher resolution for "middle" values
# ---------------------------------------------------------------------------
temperatures = np.arange(15.0, 28.5, 0.5)  # 0.5 °C steps for finer precision
humidities = np.arange(55.0, 79.0, 1.0)  # 1 % RH steps

# Compute dew‑point matrix
dew_points = np.empty((len(humidities), len(temperatures)))
for i, rh in enumerate(humidities):
    for j, t in enumerate(temperatures):
        dew_points[i, j] = calculate_dew_point(float(t), float(rh))

# Create a text matrix for data labels (dew point values)
text_labels = np.empty_like(dew_points, dtype=object)
for i in range(len(humidities)):
    for j in range(len(temperatures)):
        text_labels[i, j] = f"{dew_points[i, j]:.2f}"

# ---------------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------------
st.title("Dew Point Ventilation Advisor")
st.markdown(
    """
This tool helps you decide whether to ventilate your home based on current indoor and outdoor conditions.\
It calculates the dew point for both indoor and outdoor air and visualizes them on a heatmap.
"""
)

col1, col2 = st.columns(2)
with col1:
    indoor_temp = st.number_input("Indoor temperature (°C)", min_value=0.0, max_value=40.0, value=21.0, step=0.1)
    indoor_rh = st.number_input("Indoor relative humidity (%)", min_value=0.0, max_value=100.0, value=50.0, step=0.1)
with col2:
    outdoor_temp = st.number_input("Outdoor temperature (°C)", min_value=-30.0, max_value=40.0, value=10.0, step=0.1)
    outdoor_rh = st.number_input("Outdoor relative humidity (%)", min_value=0.0, max_value=100.0, value=70.0, step=0.1)

# Calculate dew points
indoor_dp = calculate_dew_point(indoor_temp, indoor_rh)
outdoor_dp = calculate_dew_point(outdoor_temp, outdoor_rh)

# If points overlap, nudge them slightly for visibility
nudge = 0.15 if (indoor_temp == outdoor_temp and indoor_rh == outdoor_rh) else 0
indoor_x = indoor_temp + nudge
outdoor_x = outdoor_temp - nudge

# ---------------------------------------------------------------------------
# Plotly heatmap — blue (low DP) ➜ red (high DP)
# ---------------------------------------------------------------------------
blue_red_scale = [[0.0, "blue"], [1.0, "red"]]

fig = go.Figure(
    data=go.Heatmap(
        x=temperatures,
        y=humidities,
        z=dew_points,
        colorscale=blue_red_scale,
        colorbar=dict(title="Dew Point (°C)"),
        hovertemplate=("Temperature: %{x:.1f}°C<br>" "Humidity: %{y:.0f}%<br>" "Dew Point: %{z:.2f}°C<extra></extra>"),
        text=text_labels,
        texttemplate="%{text}",
        textfont={"size": 10, "color": "black"},
    )
)

fig.update_layout(
    title="Dew Point Temperature (°C)",
    xaxis_title="Temperature (°C)",
    yaxis_title="Relative Humidity (%)",
    template="plotly_white",
)

fig.update_xaxes(
    tickvals=temperatures,
    ticktext=[f"{t:.1f}" for t in temperatures],
    tickangle=0,
)
fig.update_yaxes(
    tickvals=humidities,
    ticktext=[f"{h:.0f}" for h in humidities],
)

# Add large dots for indoor and outdoor points with offset text positions
fig.add_trace(
    go.Scatter(
        x=[indoor_x],
        y=[indoor_rh],
        mode="markers+text",
        marker=dict(size=18, color="green", line=dict(width=2, color="black")),
        name="Indoor",
        text=[f"Indoor\nDP: {indoor_dp:.2f}°C"],
        textposition="top right",
        textfont=dict(size=12, color="black"),
        hovertemplate=(
            f"<b>Indoor</b><br>Temp: %{{x:.1f}}°C<br>RH: %{{y:.0f}}%<br>" f"Dew Point: {indoor_dp:.2f}°C<extra></extra>"
        ),
    )
)
fig.add_trace(
    go.Scatter(
        x=[outdoor_x],
        y=[outdoor_rh],
        mode="markers+text",
        marker=dict(size=18, color="blue", line=dict(width=2, color="black")),
        name="Outdoor",
        text=[f"Outdoor\nDP: {outdoor_dp:.2f}°C"],
        textposition="bottom left",
        textfont=dict(size=12, color="black"),
        hovertemplate=(
            f"<b>Outdoor</b><br>Temp: %{{x:.1f}}°C<br>RH: %{{y:.0f}}%<br>"
            f"Dew Point: {outdoor_dp:.2f}°C<extra></extra>"
        ),
    )
)

fig.update_layout(
    legend=dict(
        orientation="h",
        x=0.5,
        y=-0.2,
        xanchor="center",
        yanchor="top",
        font=dict(size=14),
    )
)

# ---------------------------------------------------------------------------
# Display results
# ---------------------------------------------------------------------------
st.subheader("Results")
st.write(f"**Indoor dew point:** {indoor_dp:.2f}°C")
st.write(f"**Outdoor dew point:** {outdoor_dp:.2f}°C")
if outdoor_dp <= indoor_dp - 2:
    st.success("✅ Ventilate (outdoor dew point is at least 2°C lower)")
else:
    st.warning("❌ Do NOT ventilate (outdoor dew point is not 2°C lower)")

st.plotly_chart(fig, use_container_width=True)
