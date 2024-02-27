import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
column_mapping = {
                    'DISPONIBILITÉ': 'Availability',
                    'Marque': 'Brand',
                    'Taille de l\'écran': 'Taille de l\'écran',
                    'Couleur': 'Couleur',
                    'Garantie': 'Garantie',
                    'Système d\'exploitation': 'Système d\'exploitation',
                    'Processeur': 'Type de Processeur',
                    'Disque Dur': 'Disque Dur',
                    'Carte Graphique': 'Carte Graphique',
                    'Mémoire':'Mémoire'
                }
# Set to keep track of processed product URLs
processed_urls = set()
# Fonction pour extraire les données à partir de la page produit de MyTEK
def extract_product_data(product_url):
    response = requests.get(product_url)
    soup = BeautifulSoup(response.content, 'html.parser')
        # Check if the product URL has already been processed
    if product_url in processed_urls:
        print(f"Skipping already processed product: {product_url}")
        return []

    # Add the product URL to the set of processed URLs
    processed_urls.add(product_url)
    # Recherche de la liste ordonnée (ol) avec la classe spécifiée
    ordered_list = soup.find('ol', {'class': 'products list items product-items'})

    data_list = []

    if ordered_list:
        # Recherche de tous les éléments li à l'intérieur de la liste ordonnée
        list_items = ordered_list.find_all('li', {'class': 'item product product-item'})
        column_names = ['Name', 'product_url']
        for list_item in list_items:
            # Extrait le lien (href) à l'intérieur de chaque élément li
            product_desc = list_item.find('div', {'class': 'prdtBILImg'})
            item_link = product_desc.find('a')['href'] if product_desc else None

            # Ouvre le lien dans le navigateur par défaut
            if item_link:
                # Fetch le contenu de la page liée
                linked_response = requests.get(item_link)
                linked_soup = BeautifulSoup(linked_response.content, 'html.parser')
                
                # Extrait le nom du produit à partir de la balise span avec la classe page-title
                product_name_span = linked_soup.find('span', {'class': 'base'})
                product_name = product_name_span.text.strip() if product_name_span else None
                
                # Extrait les données de la table additional-attributes
                additional_attributes_wrapper = linked_soup.find('div', {'class': 'additional-attributes-wrapper'})
                table = additional_attributes_wrapper.find('table', {'class': 'data table additional-attributes'}) if additional_attributes_wrapper else None
                                # Convert the table data to a dictionary
                selected_columns = ['DISPONIBILITÉ', 'Marque', 'Taille de l\'écran','Couleur','Garantie','Système d\'exploitation','Processeur','Disque Dur','Carte Graphique','Mémoire'] 
                # Define a mapping for old column names to new column names
                column_mapping = {
                    'DISPONIBILITÉ': 'Availability',
                    'Marque': 'Brand',
                    'Taille de l\'écran': 'Taille de l\'écran',
                    'Couleur': 'Couleur',
                    'Garantie': 'Garantie',
                    'Système d\'exploitation': 'Système d\'exploitation',
                    'Processeur': 'Type de Processeur',
                    'Disque Dur': 'Disque Dur',
                    'Carte Graphique': 'Carte Graphique',
                    'Mémoire':'Mémoire'
                }
                table_data = {}
                if table:
                    rows = table.find_all('tr')
                    for row in rows:
                        columns = row.find_all(['th', 'td'])
                        key = columns[0].text.strip()
                        value = columns[1].text.strip()
                         # Check if the key is in the list of selected columns
                        if key in selected_columns:
                            # Use the mapping dictionary to get the new column name
                            new_key = column_mapping.get(key, key)
                            table_data[new_key] = value
                            

                # Extrait la note ou le pourcentage de la classe rating-result
                #reviews_summary = linked_soup.find('div', {'class': 'product-reviews-summary'})
                #rating_result = reviews_summary.find('div', {'class': 'review-summary'}).find('span', {'class': 'rating-result'})
                #rating_percentage = rating_result['title'] if rating_result else None
                                # Find additional attributes wrapper
                additional_attributes_wrapper1 = linked_soup.find('div', {'class': 'carousel-item active'})
                
                # Find image tag within the additional attributes wrapper
                image_tag = additional_attributes_wrapper1.find('img') if additional_attributes_wrapper1 else None
                
                # Extract the 'src' attribute from the image tag
                image_url = image_tag['src'] if image_tag else None

                 # Find elements containing special price, old price, and discount
                final_price_span = linked_soup.find('div', {'class': 'product-info-price'})
                final_price_element = final_price_span.find('span', {'class': 'price'})
                final_price_value = int(''.join(filter(lambda x: x.isdigit(), final_price_element.text.strip())))
                
                special_price_container = linked_soup.find('span', {'class': 'special-price'})
                special_price_element = special_price_container.find('span', {'class': 'price'}) if special_price_container else None
                special_price_value = int(''.join(filter(lambda x: x.isdigit(), special_price_element.text.strip()))) if special_price_element else None

                discount_element = linked_soup.find('span', {'class': 'discount-price'})
                discount_str = discount_element.text.strip() if discount_element else None
                discount_value = int(''.join(filter(lambda x: x.isdigit(), discount_str))) if special_price_element else None


                old_price_container = linked_soup.find('span', {'class': 'old-price'})
                old_price_element = old_price_container.find('span', {'class': 'price'}) if old_price_container else None
                old_price_str = old_price_element.text.strip() if old_price_element else None
                old_price_value = int(''.join(filter(lambda x: x.isdigit(), old_price_str))) if old_price_str else None

                reference_container = linked_soup.find('div', {'class': 'product attribute sku'})
                referencee = reference_container.find('div', {'class': 'value'})
                reference = referencee.text if referencee else None

                

                # Check for None before accessing properties
                if all([product_name, item_link]):
                    column_names+= list(table_data.keys())+['Image URL','Store','Price','Old Price','Discount','Ref']
                    
                    data = {
                        'Name': product_name,
                        #'Rating Percentage': rating_percentage,
                        'product_url': item_link,
                         **table_data,  # Include table data in the dictionary
                        'Image URL':image_url,
                        'Store':'MyTek',
                        'Price': special_price_value if special_price_value is not None else final_price_value ,
                        'Old Price':old_price_value,
                        'Discount':discount_value,
                        'Ref':reference,

                    }

                    data_list.append(data)

    return data_list,column_names
#column_names = ['Name', 'product_url'] + list(column_mapping.values()) + ['Image URL', 'Store', 'Price', 'Old Price', 'Discount', 'Ref']

base_url = 'https://www.mytek.tn/informatique/ordinateurs-portables.html?p='
current_page_number = 1
max_pages=23
while current_page_number <= max_pages:
    current_page_url = f'{base_url}{current_page_number}'
    data,column_names = extract_product_data(current_page_url)
    print(f"table_data_keys: {column_names},{data}")
    if not data:
        break  # No more pages to process

    # Création d'un DataFrame pandas à partir des données
    df = pd.DataFrame(data,columns=column_names)

    # Enregistrement des données dans un fichier CSV
    df.to_csv('mytek_product_data.csv', mode='a', index=False, header=not processed_urls)

    print(f"Les données de la page {current_page_url} ont été extraites et enregistrées dans 'mytek_product_data.csv'")
    
    current_page_number += 1
