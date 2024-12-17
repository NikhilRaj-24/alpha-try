from flask import Flask, render_template, request, jsonify
import pandas as pd
import os

# Region mapping with more precise city assignments
REGION_MAP = {
    "Delhi-NCR": {
        "Delhi": ["Delhi"],
        "NCR": ["Gurgaon", "Noida", "Ghaziabad", "Faridabad"]
    },
    "North India": [
        "Ludhiana", "Jalandhar", "Ambala", "Lucknow", "Meerut", "Chandigarh",
        "Mohali", "Panchkula", "Kharar", "Dehradun"
    ],
    "East India": ["Kolkata", "Kharagpur"],
    "West India": {
        "Maharashtra": ["Mumbai", "Pune", "Thane", "Navi Mumbai", "Sangli", "Kalyan", "Badlapur", "Nashik"],
        "Gujarat": ["Ahmedabad", "Surat", "Vadodara"]
    },
    "South India": {
        "Karnataka": ["Bangalore", "Mysore", "Gulbarga"],
        "Telangana": ["Hyderabad", "Secunderabad", "Ranga Reddy"],
        "Tamil Nadu": ["Chennai", "Coimbatore"]
    }
}

COLUMN_ORDER = [
    "Make", "Model", "Variant", "Transmission", "Fuel Type",
    "Price_numeric", "Distance_numeric", "City", "Age"
]

app = Flask(__name__, static_url_path='/static')

DATA_PATH = os.path.join("data", "transformed_data.csv")

def get_region_for_city(city: str) -> str:
    for region, cities in REGION_MAP.items():
        if isinstance(cities, dict):
            for sub_region, sub_cities in cities.items():
                if city in sub_cities:
                    return region
        elif isinstance(cities, list):
            if city in cities:
                return region
    return "Unknown"

# Load data once
df = pd.read_csv(DATA_PATH)
df['Region'] = df['City'].apply(get_region_for_city)
df = df[COLUMN_ORDER + ['Region']].dropna()

def filter_data(df, filters, use_all_regions=False, use_full_age_range=False, min_records=10):
    filtered_df = df.copy()
    for col in ['Make', 'Model', 'Variant', 'Transmission', 'Fuel Type']:
        val = filters.get(col)
        if val and val != "All":
            filtered_df = filtered_df[filtered_df[col] == val]

    if filtered_df.empty:
        return filtered_df, True

    reference_car = filtered_df.iloc[0]
    region_fallback = False

    # Region Filtering
    if not use_all_regions:
        region = get_region_for_city(reference_car['City'])
        region_cities = []
        for region_key, region_value in REGION_MAP.items():
            if region_key == region:
                if isinstance(region_value, dict):
                    for sub_region_cities in region_value.values():
                        region_cities.extend(sub_region_cities)
                elif isinstance(region_value, list):
                    region_cities.extend(region_value)

        region_filtered_df = filtered_df[filtered_df['City'].isin(region_cities)]
        if len(region_filtered_df) < min_records:
            region_filtered_df = filtered_df
            region_fallback = True
    else:
        region_filtered_df = filtered_df
        region_fallback = True

    # Age-based filtering
    if not use_full_age_range:
        base_age = reference_car['Age']
        for age_range in range(2, 11):
            age_filtered_df = region_filtered_df[
                (region_filtered_df['Age'] >= base_age - age_range) &
                (region_filtered_df['Age'] <= base_age + age_range)
            ]
            # Reapply filters
            for col in ['Make', 'Model', 'Variant', 'Transmission', 'Fuel Type']:
                val = filters.get(col)
                if val and val != "All":
                    age_filtered_df = age_filtered_df[age_filtered_df[col] == val]

            if len(age_filtered_df) >= min_records:
                return age_filtered_df, region_fallback

        return age_filtered_df if len(age_filtered_df) > 0 else region_filtered_df, region_fallback

    return region_filtered_df, region_fallback

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/options", methods=["POST"])
def options():
    data = request.json
    filters = {
        "Make": data.get("Make", "All"),
        "Model": data.get("Model", "All"),
        "Variant": data.get("Variant", "All"),
        "Transmission": data.get("Transmission", "All"),
        "Fuel Type": data.get("FuelType", "All")
    }

    # Always get all makes from full dataset
    makes = ["All"] + sorted(df["Make"].unique())

    # Filter for models based on Make
    model_subset = df.copy()
    if filters["Make"] != "All":
        model_subset = model_subset[model_subset["Make"] == filters["Make"]]
    models = ["All"] + sorted(model_subset["Model"].unique())

    # Filter for variants based on Make and Model
    variant_subset = model_subset.copy()
    if filters["Model"] != "All":
        variant_subset = variant_subset[variant_subset["Model"] == filters["Model"]]
    variants = ["All"] + sorted(variant_subset["Variant"].unique())

    # Filter for transmission based on Make, Model, Variant
    transmission_subset = variant_subset.copy()
    if filters["Variant"] != "All":
        transmission_subset = transmission_subset[transmission_subset["Variant"] == filters["Variant"]]
    transmissions = ["All"] + sorted(transmission_subset["Transmission"].unique())

    # Filter for fuel type based on Make, Model, Variant
    fuel_subset = variant_subset.copy()
    if filters["Variant"] != "All":
        fuel_subset = fuel_subset[fuel_subset["Variant"] == filters["Variant"]]
    fuel_types = ["All"] + sorted(fuel_subset["Fuel Type"].unique())

    return jsonify({
        "Make": makes,
        "Model": models,
        "Variant": variants,
        "Transmission": transmissions,
        "FuelType": fuel_types
    })

@app.route("/filter", methods=["POST"])
def filter_endpoint():
    data = request.json
    filters = {
        "Make": data.get("Make", "All"),
        "Model": data.get("Model", "All"),
        "Variant": data.get("Variant", "All"),
        "Transmission": data.get("Transmission", "All"),
        "Fuel Type": data.get("FuelType", "All")
    }
    use_all_regions = data.get("UseAllRegions", False)
    use_full_age_range = data.get("UseFullAgeRange", False)

    filtered_data, region_fallback = filter_data(
        df,
        filters,
        use_all_regions=use_all_regions,
        use_full_age_range=use_full_age_range
    )

    result = filtered_data.to_dict(orient="records")
    if len(filtered_data) > 0:
        if use_all_regions or region_fallback:
            region_display = "All Regions"
        else:
            first_car_region = get_region_for_city(filtered_data.iloc[0]['City'])
            region_display = first_car_region if first_car_region != "Unknown" else "All Regions"

        if use_full_age_range:
            age_range_display = "Full"
        else:
            min_age = filtered_data['Age'].min()
            max_age = filtered_data['Age'].max()
            age_range_display = f"From {min_age} to {max_age}"
    else:
        region_display = "All Regions"
        age_range_display = "N/A"

    return jsonify({
        "records": result,
        "total_records": len(filtered_data),
        "region": region_display,
        "age_range": age_range_display
    })

if __name__ == "__main__":
    app.run(debug=True)
