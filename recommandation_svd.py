import pandas as pd
from surprise import Dataset, Reader, SVD, accuracy, dump
from surprise.model_selection import GridSearchCV, train_test_split

def build_and_save_model(path_user_interactions, save_path='recommendation.pkl'):
    user_interactions_df=pd.read_csv(path_user_interactions)
    # Define the Reader object
    reader = Reader(rating_scale=(0, 5))  # Assuming ratings are on a scale from 0 to 5

    # Load the dataset using Surprise's Dataset class
    data = Dataset.load_from_df(user_interactions_df[['User_ID', 'Item_ID', 'Rating']], reader)

    # Split the data into training and testing sets
    trainset, _ = train_test_split(data, test_size=0.2, random_state=42)

    # Define the parameter grid for GridSearchCV
    param_grid = {'n_factors': [50, 100, 150],
                  'n_epochs': [20, 30, 40],
                  'lr_all': [0.005, 0.01, 0.02],
                  'reg_all': [0.02, 0.1, 0.2]}

    # Use GridSearchCV to find the best combination of hyperparameters
    grid_search = GridSearchCV(SVD, param_grid, measures=['rmse'], cv=3)
    grid_search.fit(data)

    # Get the best set of hyperparameters
    best_params = grid_search.best_params['rmse']
    print(f"Best hyperparameters: {best_params}")

    # Train the model with the best hyperparameters
    final_model = SVD(**best_params)
    final_model.fit(trainset)

    # Make predictions on the test set
    predictions = final_model.test(_)

    # Evaluate the final model using RMSE
    rmse = accuracy.rmse(predictions)
    print(f"Final RMSE: {rmse}")
    # Save the model to a file
    dump.dump(save_path, algo=final_model)
    print(f"Model saved to {save_path}")

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


# test:
#build_and_save_model('dummy_user_preferences.csv', save_path='recommandation.pkl')
print(recommend_for_user('user_88', 'Fproducts.csv','dummy_user_preferences.csv', saved_model_path='recommendation.pkl', top_n=5))
