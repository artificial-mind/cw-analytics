"""
Generate synthetic training data for delay prediction ML model.

Creates realistic shipment data with delay labels based on known patterns:
- Port congestion
- Carrier reliability
- Seasonal patterns
- Route complexity
"""
import random
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json


# Shipping routes with different delay characteristics
MAJOR_ROUTES = [
    # Asia to North America (Trans-Pacific)
    {"origin": "Shanghai", "destination": "Los Angeles", "base_delay_rate": 0.15, "transit_days": 14},
    {"origin": "Shanghai", "destination": "Long Beach", "base_delay_rate": 0.18, "transit_days": 15},
    {"origin": "Ningbo", "destination": "Long Beach", "base_delay_rate": 0.20, "transit_days": 16},
    {"origin": "Yantian", "destination": "Seattle", "base_delay_rate": 0.12, "transit_days": 13},
    {"origin": "Busan", "destination": "Los Angeles", "base_delay_rate": 0.14, "transit_days": 12},
    
    # Asia to Europe
    {"origin": "Shanghai", "destination": "Rotterdam", "base_delay_rate": 0.25, "transit_days": 35},
    {"origin": "Shanghai", "destination": "Hamburg", "base_delay_rate": 0.28, "transit_days": 36},
    {"origin": "Yantian", "destination": "Felixstowe", "base_delay_rate": 0.30, "transit_days": 38},
    {"origin": "Singapore", "destination": "Rotterdam", "base_delay_rate": 0.22, "transit_days": 32},
    {"origin": "Port Klang", "destination": "Le Havre", "base_delay_rate": 0.26, "transit_days": 34},
    
    # Intra-Asia
    {"origin": "Shanghai", "destination": "Singapore", "base_delay_rate": 0.08, "transit_days": 7},
    {"origin": "Singapore", "destination": "Jakarta", "base_delay_rate": 0.10, "transit_days": 4},
    {"origin": "Hong Kong", "destination": "Singapore", "base_delay_rate": 0.07, "transit_days": 5},
    
    # North America to Europe
    {"origin": "New York", "destination": "Rotterdam", "base_delay_rate": 0.18, "transit_days": 11},
    {"origin": "Los Angeles", "destination": "Hamburg", "base_delay_rate": 0.35, "transit_days": 24},
]

# Carriers with different reliability scores
CARRIERS = [
    {"name": "MAERSK", "reliability": 0.92, "delay_modifier": -0.05},
    {"name": "MSC", "reliability": 0.88, "delay_modifier": 0.00},
    {"name": "CMA CGM", "reliability": 0.85, "delay_modifier": 0.03},
    {"name": "COSCO", "reliability": 0.90, "delay_modifier": -0.02},
    {"name": "HAPAG-LLOYD", "reliability": 0.91, "delay_modifier": -0.03},
    {"name": "ONE", "reliability": 0.87, "delay_modifier": 0.02},
    {"name": "EVERGREEN", "reliability": 0.86, "delay_modifier": 0.04},
    {"name": "HMM", "reliability": 0.84, "delay_modifier": 0.05},
]

# Seasonal delay factors
SEASONAL_DELAY_FACTORS = {
    1: 0.05,   # January - Chinese New Year prep
    2: 0.15,   # February - Chinese New Year peak
    3: 0.10,   # March - Post-CNY recovery
    4: 0.02,   # April - Normal
    5: 0.00,   # May - Normal
    6: 0.00,   # June - Normal
    7: 0.03,   # July - Summer volume
    8: 0.05,   # August - Peak season prep
    9: 0.08,   # September - Peak season
    10: 0.12,  # October - Peak season
    11: 0.10,  # November - Holiday rush
    12: 0.08,  # December - Year-end
}

# Day of week factors (port congestion)
WEEKDAY_FACTORS = {
    0: 0.02,   # Monday
    1: 0.01,   # Tuesday
    2: 0.00,   # Wednesday
    3: 0.01,   # Thursday
    4: 0.03,   # Friday
    5: 0.05,   # Saturday - weekend congestion
    6: 0.05,   # Sunday - weekend congestion
}


def generate_shipment_sample(shipment_id: int) -> Dict[str, Any]:
    """Generate a single realistic shipment training sample."""
    
    # Random route
    route = random.choice(MAJOR_ROUTES)
    
    # Random carrier
    carrier = random.choice(CARRIERS)
    
    # Random departure date (last 12 months)
    days_ago = random.randint(0, 365)
    etd = datetime.now() - timedelta(days=days_ago)
    month = etd.month
    day_of_week = etd.weekday()
    
    # Calculate ETA
    eta = etd + timedelta(days=route["transit_days"])
    
    # Calculate delay probability
    delay_prob = route["base_delay_rate"]
    delay_prob += carrier["delay_modifier"]
    delay_prob += SEASONAL_DELAY_FACTORS[month]
    delay_prob += WEEKDAY_FACTORS[day_of_week]
    
    # Random factors
    if random.random() < 0.10:  # 10% chance of exceptional circumstances
        delay_prob += random.uniform(0.15, 0.30)  # Weather, strikes, etc.
    
    # Clamp probability
    delay_prob = max(0.0, min(1.0, delay_prob))
    
    # Determine if delayed
    will_delay = random.random() < delay_prob
    
    # If delayed, calculate delay duration
    if will_delay:
        # Delays typically 1-7 days, with exponential distribution
        delay_hours = int(random.expovariate(1/48))  # Mean 48 hours
        delay_hours = max(24, min(delay_hours, 168))  # Clamp to 1-7 days
    else:
        delay_hours = 0
    
    # Risk flag (correlated with delays)
    risk_flag = will_delay and random.random() < 0.6  # 60% of delays are flagged
    
    # Container type
    container_type = random.choice(["20GP", "40GP", "40HC", "45HC"])
    
    return {
        "shipment_id": f"TRAIN-{shipment_id:05d}",
        "origin_port": route["origin"],
        "destination_port": route["destination"],
        "carrier_name": carrier["name"],
        "carrier_reliability": carrier["reliability"],
        "etd": etd.isoformat(),
        "eta": eta.isoformat(),
        "month": month,
        "day_of_week": day_of_week,
        "transit_days": route["transit_days"],
        "container_type": container_type,
        "risk_flag": risk_flag,
        "base_delay_rate": route["base_delay_rate"],
        "seasonal_factor": SEASONAL_DELAY_FACTORS[month],
        "weekday_factor": WEEKDAY_FACTORS[day_of_week],
        "delay_probability": round(delay_prob, 3),
        # Target labels
        "will_delay": will_delay,
        "delay_hours": delay_hours,
        "delay_category": "delayed" if will_delay else "on_time"
    }


def generate_training_dataset(num_samples: int = 1000) -> pd.DataFrame:
    """
    Generate complete training dataset.
    
    Args:
        num_samples: Number of training samples to generate
        
    Returns:
        DataFrame with training data
    """
    print(f"🔄 Generating {num_samples} training samples...")
    
    samples = []
    for i in range(num_samples):
        sample = generate_shipment_sample(i)
        samples.append(sample)
        
        if (i + 1) % 100 == 0:
            print(f"   Generated {i + 1}/{num_samples} samples...")
    
    df = pd.DataFrame(samples)
    
    # Print statistics
    delay_rate = df["will_delay"].mean()
    avg_delay_hours = df[df["will_delay"]]["delay_hours"].mean()
    
    print(f"\n📊 Dataset Statistics:")
    print(f"   Total samples: {len(df)}")
    print(f"   Delayed: {df['will_delay'].sum()} ({delay_rate*100:.1f}%)")
    print(f"   On-time: {(~df['will_delay']).sum()} ({(1-delay_rate)*100:.1f}%)")
    print(f"   Avg delay (delayed shipments): {avg_delay_hours:.1f} hours")
    print(f"   Risk flagged: {df['risk_flag'].sum()}")
    
    # Distribution by route
    print(f"\n📍 Top Routes:")
    route_counts = df.groupby(["origin_port", "destination_port"]).size().sort_values(ascending=False).head(5)
    for (origin, dest), count in route_counts.items():
        route_df = df[(df["origin_port"] == origin) & (df["destination_port"] == dest)]
        delay_pct = route_df["will_delay"].mean() * 100
        print(f"   {origin} → {dest}: {count} shipments ({delay_pct:.1f}% delayed)")
    
    # Distribution by carrier
    print(f"\n🚢 Carrier Performance:")
    for carrier in df["carrier_name"].unique():
        carrier_df = df[df["carrier_name"] == carrier]
        delay_pct = carrier_df["will_delay"].mean() * 100
        print(f"   {carrier}: {len(carrier_df)} shipments ({delay_pct:.1f}% delayed)")
    
    return df


def save_training_data(df: pd.DataFrame, filepath: str = "data/training_data.csv"):
    """Save training data to CSV."""
    import os
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df.to_csv(filepath, index=False)
    print(f"\n✅ Training data saved to: {filepath}")


if __name__ == "__main__":
    # Generate 1000 samples
    df = generate_training_dataset(1000)
    
    # Save to file
    save_training_data(df, "data/training_data.csv")
    
    print("\n✅ Training data generation complete!")
    print(f"📁 File: data/training_data.csv")
    print(f"📊 Shape: {df.shape}")
    print(f"\nNext step: Train the ML model with train_delay_model.py")
