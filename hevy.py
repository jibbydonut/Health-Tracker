import requests
import pandas as pd
from dotenv import load_dotenv
import os
import json
from sqlalchemy import create_engine

def parse_json(row):
    try:
        # Replace single quotes with double quotes, then parse JSON
        return json.loads(row.replace("'", "\""))
    except json.JSONDecodeError as e:
        print(f"Error parsing row: {e}")
        return None


# Load environment variables from .env file
load_dotenv()


# get DB Creds
user = os.getenv("POSTGRES_USER")
password = os.getenv("POSTGRES_PASSWORD")
host = os.getenv("POSTGRES_HOST")
port = os.getenv("POSTGRES_PORT")
database = os.getenv("POSTGRES_DB")

# SQL alchemy connection string
engine = create_engine(f"postgresql://{user}:{password}@{host}:{port}/{database}")

# Access the API key from the environment variable
api_key = os.getenv("HEVY_API_KEY")
workout_url = "https://api.hevyapp.com/v1/workouts/events"
exercise_url = "https://api.hevyapp.com/v1/exercise_templates"
headers = {
    "accept": "application/json",
    "api-key": api_key
}

# Parameters for the API request
workout_page_size = 10
workout_page = 1
exercise_page_size = 100
exercise_page = 1
since = "1970-01-01T00:00:00Z"
workouts = []
exercise_templates = []

# gets all exercises in Hevy DB
while True:
    exercise_params = {
        "page": exercise_page,
        "pageSize": exercise_page_size
    }
    response = requests.get(exercise_url, headers=headers, params=exercise_params)

    if response.status_code != 200:
        print(f"Request failed: {response.status_code}")
        break
    
    data = response.json()
    templates = data.get("exercise_templates", [])
    
    # Break if there are no more templates
    if not templates:
        break
    
    # Add templates to the exercise_templates list
    exercise_templates.extend(templates)
    
    # Update the page for the next request
    exercise_page += 1

df_exercises = pd.DataFrame(exercise_templates)

# Push workexercises outs to csv and to postgres
df_exercises.to_csv("exercise_templates.csv",index=False)
df_exercises.to_sql("src__hevy_exercises", engine, if_exists="replace", index=False)

while True:
    params = {
        "page": workout_page,
        "pageSize": workout_page_size,
        "since": since
    }
    response = requests.get(workout_url, headers=headers, params=params)
        
        # Check if the request was successful
    if response.status_code != 200:
        print(f"Request failed: {response.status_code}")
        break
        
    data = response.json()
    events = data.get("events", [])
        
        # Break if there are no more events
    if not events:
        break
        
        # Add events to the workouts list
    workouts.extend(events)
        
        # Update the page for the next request
    workout_page += 1


def flatten_workouts(data):
    rows = []
    for item in data:
        workout = item.get("workout", {})
        workout_id = workout.get("id")
        workout_title = workout.get("title")
        workout_start = workout.get("start_time")
        workout_end = workout.get("end_time")
        
        for exercise in workout.get("exercises", []):
            exercise_title = exercise.get("title")
            exercise_template_id = exercise.get("exercise_template_id")
            
            for workout_set in exercise.get("sets", []):
                set_index = workout_set.get("index")
                set_type = workout_set.get("set_type")
                weight_kg = workout_set.get("weight_kg")
                reps = workout_set.get("reps")
                
                # Append the flattened data as a row
                rows.append({
                    "workout_id": workout_id,
                    "workout_title": workout_title,
                    "workout_start": workout_start,
                    "workout_end": workout_end,
                    "exercise_title": exercise_title,
                    "exercise_template_id": exercise_template_id,
                    "set_index": set_index,
                    "set_type": set_type,
                    "weight_kg": weight_kg,
                    "reps": reps,
                })
    
    return pd.DataFrame(rows)

# Convert to DataFrame
df_workouts = flatten_workouts(workouts)

# Convert the data to a pandas DataFrame and save to CSV
df_workouts = pd.DataFrame(df_workouts)

# Push workouts to csv and to postgres
df_workouts.to_csv("workouts.csv", index=False)
df_workouts.to_sql("src__hevy_workouts", engine, if_exists="replace", index=False)
