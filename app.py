from flask import Flask, jsonify, request
import pandas as pd
import numpy as np
from flask_cors import CORS
from json import loads, dumps
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from urllib.parse import quote
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from surprise import Dataset, Reader, SVD, accuracy, dump
from surprise.model_selection import GridSearchCV, train_test_split


app = Flask(__name__)
CORS(app)
# Load the CSV file into a Pandas DataFrame
file_path = 'mergeproducts.csv'
df = pd.read_csv(file_path)

df['Discount'] = pd.to_numeric(df['Discount'].replace('', np.nan).str.rstrip('%'), errors='coerce')

# Features to consider for similarity calculation
features = ['Brand', 'Système d\'exploitation', 'Type de Processeur', 'Mémoire', 'Disque Dur']

# Vectorize the text features
vectorizer = TfidfVectorizer(stop_words=None, token_pattern=r'\b\w+\b', max_df=0.85, min_df=0.1, ngram_range=(1, 2))
feature_matrix = vectorizer.fit_transform(df[features].apply(lambda row: ' '.join(row.values.astype(str)), axis=1))

# Define a function to calculate similarity based on text features
def calculate_similarity(target_vector, candidate_vector):
    return cosine_similarity(target_vector, candidate_vector)[0][0]

# Load the model during the server startup
_, final_model = dump.load('recommendation.pkl')
print(final_model)

#Discount
def get_top_discounted_products(df, num_top_products=8):
    # Sort the DataFrame by the 'Discount' column in descending order
    sorted_df = df[df['Store']!='jumia'].sort_values(by='Discount', ascending=False)

    # Get the top N products
    top_products = sorted_df.head(num_top_products)
    print(top_products['Discount'])
    return top_products




# Get all products
@app.route('/products', methods=['GET'])
def get_products():
    #return jsonify({'products': df.to_dict(orient='records') })
    #products = df.to_dict(orient='records')
    result = df.to_json(orient="records")
    products = loads(result)
    
    if len(products) > 0:
        return jsonify({'products': products})
    return jsonify({'message': 'Product not found'}), 404
   



# Get a specific product by Ref
@app.route('/product/<string:product_ref>', methods=['GET'])
def get_product(product_ref):
    #product = df[df['Ref'] == product_ref].to_dict(orient='records')
    product = df[df['Ref'] == product_ref].to_json(orient='records')
    product = loads(product)

    if len(product) > 0:
        return jsonify({'product': product})
    return jsonify({'message': 'Product not found'}), 404


# Get a specific product by Name
@app.route('/products/<string:product_name>', methods=['GET'])
def get_product_by_name(product_name):
    # Convert the 'Discount' column to integers (if not already done)
    df['Discount'] = df['Discount'].str.rstrip('%').astype('int')

    # Retrieve the product by Name
    product = df[df['Name'].str.lower() == product_name.lower()].to_dict(orient='records')
    
    if len(product) > 0:
        return jsonify({'product': product})
    
    return jsonify({'message': 'Product not found'}), 404


# Get all products with optional filtering
@app.route('/search', methods=['GET'])
def get_products_filtered():
    # Get query parameters for filtering
    filters = {key: value for key, value in request.args.items()}

    # Apply filters to the DataFrame
    filtered_df = df
    for key, value in filters.items():
        filtered_df = filtered_df[filtered_df[key] == value].to_json(orient='records')
        filtered_df = loads(filtered_df)



    # Return the filtered products
    return jsonify({'products': filtered_df})


# Compare a specific product with others
@app.route('/compare/<string:product_ref>', methods=['GET'])
def compare_product(product_ref):
    # Get the details of the target product
    target_product = df[df['Ref'] == product_ref].to_dict(orient='records')
    if len(target_product) == 0:
        return jsonify({'message': 'Target product not found'}), 404

    # Compare the target product with others
    similarities = []
    target_vector = feature_matrix[df[df['Ref'] == product_ref].index[0]]

    for _, candidate in df.iterrows():
        if candidate['Ref'] != product_ref:
            candidate_vector = feature_matrix[candidate.name]
            similarity = calculate_similarity(target_vector, candidate_vector)
            similarities.append({
                'product': candidate['Ref'],
                'similarity': similarity
            })

    # Sort the results by similarity in descending order
    similarities = sorted(similarities, key=lambda x: x['similarity'], reverse=True)

    # Return the comparison results
    return jsonify(similarities)

def recommend_for_user(user_id,path_product,path_user_interaction , saved_model_path='recommendation.pkl', top_n=5):
    # Load the saved model
    _, final_model = dump.load(saved_model_path)
    
    product_df=pd.read_csv(path_product)
    user_interactions_df=pd.read_csv(path_user_interaction)    


    user_items = user_interactions_df[user_interactions_df['User_ID'] == user_id]['Item_ID'].unique()
    # Generate predictions for items the user has not interacted with
    unseen_items = product_df['Ref'][~product_df['Ref'].isin(user_items)].unique()
    user_predictions = [final_model.predict(user_id, item_id) for item_id in unseen_items]
   
    # Create a DataFrame from the list of recommended products
    recommended_products = []
    for prediction in user_predictions:
        item_id = prediction.iid
        estimate_score = prediction.est
        product_info = product_df[product_df['Ref'] == item_id].iloc[0].to_dict()
        recommended_product = {**product_info, 'Estimate_Score': estimate_score}
        recommended_products.append(recommended_product)
    recommended_df = pd.DataFrame(recommended_products)

 
    top_n_recommended_df = recommended_df.nlargest(top_n, 'Estimate_Score')
    return top_n_recommended_df

# New route for collaborative filtering recommendations
@app.route('/rec')
def collaborative_filtering_recommendations_route():
    # Extract parameters from the request URL
    # user_id = request.args.get('user_id', 'user_0')
    user_id = 'user_0'
    products_file = 'mergeproducts.csv'
    preferences_file = 'dummy_user_preferences.csv'
    model_path =  'recommendation.pkl'
    top_n = 5

    # Call the function with the extracted parameters
    recommended_products = recommend_for_user(user_id, products_file, preferences_file, saved_model_path=model_path, top_n=top_n)

    # Convert the recommendations DataFrame to a JSON representation
    json_recommendations = recommended_products.to_json(orient='records')
    json_recommendations = loads(json_recommendations)

    return jsonify(json_recommendations)

@app.route('/')
def home():
    # Call the function to get the top discounted products
    top_discounted_products = get_top_discounted_products(df)  # Adjust 'df' to your DataFrame

     # Convert the DataFrame to a JSON representation
    json_result = top_discounted_products.to_json(orient='records')

    json_result = loads(json_result)

    return jsonify({"top_discounted_products": json_result})

# Function to find all products with the same features
def find_all_products_with_features(request_features):
    # Ensure all required features are present
    if all(feature in request_features for feature in features):
        # Filter DataFrame based on the specified features
        filtered_df = df
        for feature, value in request_features.items():
            filtered_df = filtered_df[filtered_df[feature] == value]

        # Return the list of matching product references
        matching_products = filtered_df['Ref'].tolist()
        return matching_products
    else:
        return []

# Route for the search page
@app.route('/similair_product/<path:product_ref>', methods=['GET'])
def search_by_product_ref(product_ref):
    # URL-decode the product reference
    product_ref = quote(product_ref, safe='')

    # Get features for the given product reference
    filtered_df = df[df['Ref'].str.lower() == product_ref.lower()]
    print(filtered_df)
    if not filtered_df.empty:
        product_features = filtered_df[features].iloc[0].to_dict()
        #print(product_features)
        # Find similar products in other stores
        similar_products = find_all_products_with_features(product_features)
        print(similar_products)
        print({'product_ref': product_ref, 'similar_products': similar_products})
        return jsonify({'product_ref': product_ref, 'similar_products': similar_products})

    else:
        return jsonify({'message': 'Product not found'}), 404
    


# Running app
if __name__ == '__main__':
   app.run(debug=True)