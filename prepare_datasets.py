"""
Dataset Preparation for SkyPlan AI
Generates realistic, meteorologically grounded training datasets for:
1. Rainout Risk Prediction (features: temperature, humidity, rain_probability, rainfall_mm, wind_speed)
2. Heat Risk Prediction (features: temperature, humidity, wind_speed, heat_index)

Note: This dataset is synthetically generated based on NOAA (National Oceanic and Atmospheric
Administration) and WMO (World Meteorological Organization) event-safety thresholds for academic
and development purposes.
"""

import numpy as np
import pandas as pd
from pathlib import Path

def compute_noaa_heat_index(temp_c, humidity):
    """
    Computes Heat Index in Celsius using the standard NOAA / Rothfusz regression equation.
    Formula applies above ~26.7C (80F). For cooler temperatures, Heat Index approx equals dry temperature.
    """
    # Convert Celsius to Fahrenheit
    T = (temp_c * 9.0 / 5.0) + 32.0
    R = humidity

    # Simple formula first
    HI_simple = 0.5 * (T + 61.0 + ((T - 68.0) * 1.2) + (R * 0.094))
    
    if HI_simple < 80:
        hi_f = HI_simple
    else:
        # Full Rothfusz regression equation
        hi_f = (-42.379 + 2.04901523 * T + 10.14333127 * R
                - 0.22475541 * T * R - 0.00683783 * (T ** 2)
                - 0.05481717 * (R ** 2) + 0.00122874 * (T ** 2) * R
                + 0.00085282 * T * (R ** 2) - 0.00000199 * (T ** 2) * (R ** 2))
        
        # Adjustments
        if R < 13 and 80 <= T <= 112:
            adj = ((13 - R) / 4) * np.sqrt((17 - abs(T - 95.0)) / 17)
            hi_f -= adj
        elif R > 85 and 80 <= T <= 87:
            adj = ((R - 85) / 10) * ((87 - T) / 5)
            hi_f += adj

    # Convert back to Celsius
    hi_c = (hi_f - 32.0) * 5.0 / 9.0
    return round(float(hi_c), 1)

def generate_rainout_dataset(n_samples=2500, random_seed=42):
    np.random.seed(random_seed)
    
    # Realistic distributions
    temps = np.random.uniform(10.0, 42.0, n_samples)
    humidities = np.random.uniform(25.0, 98.0, n_samples)
    rain_probs = np.random.uniform(0.0, 100.0, n_samples)
    winds = np.random.uniform(2.0, 55.0, n_samples)
    
    # Rainfall amount correlates with rain probability and humidity
    rainfalls = []
    labels = []
    
    for i in range(n_samples):
        prob = rain_probs[i]
        hum = humidities[i]
        wind = winds[i]
        
        # Generate rainfall mm conditioned on probability
        if prob < 20:
            rain = np.random.exponential(scale=0.2)
        elif prob < 50:
            rain = np.random.exponential(scale=1.5)
        elif prob < 80:
            rain = np.random.gamma(shape=2.0, scale=3.0)
        else:
            rain = np.random.gamma(shape=3.5, scale=5.0)
        
        # Add correlation with extreme humidity
        if hum > 85 and prob > 60:
            rain += np.random.uniform(2.0, 10.0)
            
        rain = round(float(np.clip(rain, 0.0, 95.0)), 1)
        rainfalls.append(rain)
        
        # Classification criteria for outdoor event disruption:
        # High Risk (2): Event cancellation or severe disruption virtually certain
        # Moderate Risk (1): High chance of delays, wet grounds, need rain gear / shelters
        # Low Risk (0): Safe for outdoor activities
        
        score = 0
        if rain >= 8.0 or prob >= 80.0:
            score += 3
        elif rain >= 3.0 or prob >= 60.0:
            score += 2
        elif rain >= 1.0 or prob >= 35.0:
            score += 1
            
        if hum >= 85 and prob >= 50:
            score += 1
        if wind >= 35: # Gusty wind exacerbates rain disruption
            score += 1
            
        # Add slight natural variability
        noise = np.random.choice([-1, 0, 1], p=[0.05, 0.90, 0.05])
        effective_score = score + noise
        
        if effective_score >= 3:
            label = "High Risk"
        elif effective_score >= 2:
            label = "Moderate Risk"
        else:
            label = "Low Risk"
            
        labels.append(label)
        
    df = pd.DataFrame({
        "temperature": np.round(temps, 1),
        "humidity": np.round(humidities, 1),
        "rain_probability": np.round(rain_probs, 1),
        "rainfall_mm": rainfalls,
        "wind_speed": np.round(winds, 1),
        "risk_level": labels
    })
    return df

def generate_heat_dataset(n_samples=2500, random_seed=101):
    np.random.seed(random_seed)
    
    temps = np.random.uniform(18.0, 48.0, n_samples)
    humidities = np.random.uniform(15.0, 95.0, n_samples)
    winds = np.random.uniform(1.0, 45.0, n_samples)
    
    heat_indices = []
    labels = []
    
    for i in range(n_samples):
        t = temps[i]
        h = humidities[i]
        w = winds[i]
        
        hi = compute_noaa_heat_index(t, h)
        heat_indices.append(hi)
        
        # Standard NOAA Heat Stress Categories:
        # High Risk: Heat Index >= 40C (Danger / Extreme Danger) or severe heat (>44C dry temp)
        # Moderate Risk: Heat Index 32C to 39.9C (Extreme Caution)
        # Low Risk: Heat Index < 32C (Safe / Caution)
        # High wind (hot dry wind) or zero wind also factored in
        
        if hi >= 40.0 or (t >= 42.0 and hi >= 38.0):
            label = "High Risk"
        elif hi >= 32.0 or (t >= 36.0 and h >= 50.0):
            label = "Moderate Risk"
        else:
            label = "Low Risk"
            
        labels.append(label)
        
    df = pd.DataFrame({
        "temperature": np.round(temps, 1),
        "humidity": np.round(humidities, 1),
        "wind_speed": np.round(winds, 1),
        "heat_index": heat_indices,
        "risk_level": labels
    })
    return df

if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parent / "datasets"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print("Generating rainout risk dataset...")
    df_rain = generate_rainout_dataset(3000)
    rain_path = out_dir / "rainout_dataset.csv"
    df_rain.to_csv(rain_path, index=False)
    print(f"Saved {len(df_rain)} rainout samples to {rain_path}")
    print("Rainout class distribution:\n", df_rain["risk_level"].value_counts())
    
    print("\nGenerating heat risk dataset...")
    df_heat = generate_heat_dataset(3000)
    heat_path = out_dir / "heat_dataset.csv"
    df_heat.to_csv(heat_path, index=False)
    print(f"Saved {len(df_heat)} heat risk samples to {heat_path}")
    print("Heat class distribution:\n", df_heat["risk_level"].value_counts())

