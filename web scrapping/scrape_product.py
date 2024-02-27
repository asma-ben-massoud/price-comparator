import requests
import csv
import pandas as pd
from bs4 import BeautifulSoup
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

def scrape_product_info(url,store):
    try:
        # Make an HTTP request to the URL
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad requests

        # Parse the HTML content with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')


        current_price = soup.find('span', class_="-b -ltr -tal -fs24 -prxs").text.strip()
        current_price=current_price+'0' if current_price else None
        current_price=int(''.join(filter(lambda x: x.isdigit() or x == 'T' or x == 'N' or x == 'D', current_price)).replace('TND', ''))

        old_price_element = soup.find('span', class_="-tal -gy5 -lthr -fs16 -pvxs")
        old_price = old_price_element.text.strip() if old_price_element else None
        old_price=old_price+'0' if old_price else None
        old_price=int(''.join(filter(lambda x: x.isdigit() or x == 'T' or x == 'N' or x == 'D', old_price)).replace('TND', ''))if old_price else None

        if old_price is not None and current_price is not None:
            discount_price=old_price-current_price
        else:
            discount_price=None
        #discount_element = soup.find('span', class_="bdg _dsct _dyn -mls")
        #discount = discount_element.text.strip() if discount_element else None

        rating_element = soup.find('div', class_="stars _m _al")
        rating = rating_element.text.strip().split()[0] if rating_element else None

        # Extract image URL
        image_url_element = soup.find('div', class_="sldr").find('a', class_="itm")['href']

        # Extract "Offre Black Friday" tag
        black_friday_tag = soup.find('a', class_="bdg _sm", string="Offre Black Friday")

        # Extract product name
        product_name_element = soup.find('h1', class_="-fs20 -pts -pbxs")
        product_name = product_name_element.text.strip() if product_name_element else None
        brand=product_name.split()[0] if product_name else None

        # Find the SKU element
        sku_element =  soup.find('li', {'class': '-pvxs'})

        # Extract the text content
        if sku_element and sku_element.span:
            sku_text = sku_element.span.next_sibling.strip()
            Ref=sku_text.replace(": ", "")
        else:
            Ref=None


        # Return the extracted information as a dictionary
        product_info = {
            'Price': current_price,
            'Old Price': old_price,
            'Discount': discount_price,
            #'rating': rating,
            'Image URL': image_url_element,
            #'black_friday_tag': True if black_friday_tag else False,
            'Name': product_name,
            "Availability": "EN Stock",
            "Ref":Ref,
            "Brand": brand,
            'product_url':url,
            'Store':store,

        }

        

        return product_info

    except requests.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return None

def extract_technical_info(url):
    # Make an HTTP request to the URL
    response = requests.get(url)
    desired_keys_mapping = {
            "Système opérateur": 'Système d\'exploitation',
            'Mémoire': 'Mémoire',
            'Garantie': 'Garantie',
            'Taille': 'Taille de l\'écran',
            'Processeur': 'Type de Processeur',
            'Disque dur': 'Disque Dur',
            'Carte graphique': 'Carte Graphique',
            'Couleur': 'Couleur'
        }


    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content with BeautifulSoup
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find the element containing technical information
        technical_info_element = soup.find('div', class_='markup -pam')

        if technical_info_element:
            # Extract the technical information list
            technical_info_list = [li.text.strip() for li in technical_info_element.find('ul').find_all('li')]
            # Modified list
            info_dict = {}

            for info in technical_info_list:
                # Remove unwanted characters like '\xa0'
                clean_info = info.replace('\xa0', '')

                # Split by the first occurrence of ':'
                split_info = clean_info.split(':', 1)
                # Check if the split resulted in two values
                if len(split_info) == 2:
                    key, value = split_info
                    # Remove leading and trailing whitespaces from key and value
                    key = key.strip()
                    value = value.strip()
                    # Check if the key is in the values of desired_keys_mapping
                    if key in desired_keys_mapping:
                        # Use the desired key in your tech_info dictionary
                        info_dict[desired_keys_mapping[key]] = value

                   
        



           

            return info_dict
        else:
            return "Technical information not found."
    else:
        return f"Error fetching the URL. Status code: {response.status_code}"



def flatten_dict(d, parent_key='', sep=':'):
    flattened = {}
    for k, v in d.items():
        new_key = f"{parent_key} {sep} {k}".strip() if parent_key else k
        if isinstance(v, dict):
            flattened.update(flatten_dict(v, new_key, sep=sep))
        else:
            flattened[new_key] = v
    return flattened


def scrape_and_extract_all_info(url):
    product_info = scrape_product_info(url)
    technical_info = extract_technical_info(url)
    merged_dict = {**flatten_dict(technical_info), **product_info }
    return merged_dict

"""
# Example usage:
product_url = 'https://www.jumia.com.tn/asus-pc-portable-d515da-ryzen-3-3250u-512-ssd-4g-w11-bleu-sac-a-dos-garantie-1an-745911.html'
result =scrape_product_info(product_url,"jumia")
print(result)
'''tech = extract_technical_info(product_url)
print(tech)

# Convert the dictionary to a pandas DataFrame
df = pd.DataFrame([result])

# Save the DataFrame to an Excel file
df.to_excel('output.xlsx', index=False)'''"""