import pandas as pd
import random

# Load items data from CSV file
items_df = pd.read_csv('final.csv')

# Generate a dummy user preferences dataset
num_users = 200  # Adjust the number of users as needed
user_preferences = []

for i in range(num_users):
    user_id = f"user_{i}"
    
    # Randomly select a subset of items for each user
    num_preferences = random.randint(5, 20)  # Adjust as needed
    preferences = random.sample(items_df['Ref'].tolist(), num_preferences)
    
    # Assign random ratings to each preference
    ratings = [random.randint(1, 5) for _ in range(num_preferences)]
    
    # Combine user preferences into a list of dictionaries
    user_preferences.extend([{"User_ID": user_id, "Item_ID": item_id, "Rating": rating} for item_id, rating in zip(preferences, ratings)])

# Create a Pandas DataFrame
user_preferences_df = pd.DataFrame(user_preferences)

# Save the user preferences dataset to a CSV file
user_preferences_df.to_csv("dummy_user_preferences.csv", index=False)
