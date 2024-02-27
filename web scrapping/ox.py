from scrape_product import flatten_dict
import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests
from bs4 import BeautifulSoup
import pandas as pd

# Function to clean text by replacing '\xa0' with space
def clean_text(text):
    return text.replace('\xa0', ' ')

# Function to scrape product information from a given URL
def scrape_product_info(product_url, store):
    response = requests.get(product_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract information from the product page
        image_element = soup.find('img', class_='thumb')
        image_url = image_element['data-image-large-src'] if image_element else None

        name_element = soup.find('h1', class_='page-title')
        name = clean_text(name_element.span.text.strip()) if name_element else None

        brand_element = soup.find('img', class_='img-fluid manufacturer-logo')
        brand = clean_text(brand_element.get('alt').strip()) if brand_element else None


        availability_element = soup.find('span', class_='badge-success')
        availability = clean_text(availability_element.text.strip()) if availability_element else None

        price_element = soup.find('span', class_='product-price')
        price = clean_text(price_element.text.strip()) if price_element else None
        price=int(''.join(filter(lambda x: x.isdigit() or x == 'T' or x == 'N' or x == 'D', price)).replace('TND', ''))
        # Check if old price and discount are available
        old_price_tag = soup.find('span', class_='regular-price')
        discount_tag = soup.find('span', class_='badge-discount')

        old_price = clean_text(old_price_tag.text.strip()) if old_price_tag else None
        if old_price is not None:
            old_price=int(''.join(filter(lambda x: x.isdigit() or x == 'T' or x == 'N' or x == 'D', old_price)).replace('TND', ''))
        discount = clean_text(discount_tag.text.strip()) if discount_tag else None
        if discount is not None:
            discount=int(''.join(filter(lambda x: x.isdigit() or x == 'T' or x == 'N' or x == 'D', discount)).replace('TND', ''))
        
        # Find the div with class 'product-reference' and extract the reference value
        reference_div = soup.find('div', class_='product-reference')

        if reference_div:
            reference_label = reference_div.find('label', class_='label')
            
            # Check if the label is 'Référence' and extract the reference value
            if reference_label and reference_label.text.strip() == 'Référence':
                reference_span = reference_div.find('span')
                reference_value = reference_span.text.strip() if reference_span else None
            
        
        # Define the desired keys for technical info
        desired_keys_mapping = {
            "Système d'exploitation": 'Système d\'exploitation',
            'Mémoire:': 'Mémoire',
            'Garantie': 'Garantie',
            'Taille Ecran': 'Taille de l\'écran',
            'Processeur': 'Type de Processeur',
            'Disque dur': 'Disque Dur',
            'Carte graphique:': 'Carte Graphique',
            'Couleur': 'Couleur'
        }

   
        data_sheet = soup.find('dl', class_='data-sheet')
        tech_info = {}

        if data_sheet:
            for dt, dd in zip(data_sheet.find_all('dt', class_='name'), data_sheet.find_all('dd', class_='value')):
                key = clean_text(dt.text.strip())
                value = clean_text(dd.text.strip())

                # Check if the key is in the values of desired_keys_mapping
                if key in desired_keys_mapping:
                    # Use the desired key in your tech_info dictionary
                    tech_info[desired_keys_mapping[key]] = value

        # Combine all information into a dictionary
        product_dict = {
            "Image URL": image_url,
            "Name": name,
            "Brand": brand,
            "Availability": availability,
            "Price": price,
            "Old Price": old_price,
            "Discount": discount,
            "Ref": reference_value,
            "Store":store,
            "product_url": product_url,
       
        }
        final_dict={**flatten_dict(tech_info), **product_dict }

        return final_dict

        return product_dict
# Function to extract product URLs from the main page
def extract_product_urls(base_url, store_name, max_pages=5):
    all_products_info = []
    page_num = 1

    while page_num <= max_pages:
        url = f'{base_url}?page={page_num}'
        response = requests.get(url)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all product anchor tags
            product_anchors = soup.find_all('a', class_='thumbnail')

            # Extract product URLs
            page_product_urls = [anchor['href'] for anchor in product_anchors]

            # Check if there are no more products
            if not page_product_urls:
                break

            all_products_info.extend(page_product_urls)
            print("page",page_num)
            page_num += 1
        else:
            print(f"Error accessing {url}. Exiting.")
            break

    return all_products_info
def main(main_page_url):
    # Step 1: Extract product URLs from the main page
    product_urls = extract_product_urls(main_page_url,'OXtek',48)

    # Step 2: Scrape information from each product page
    all_product_info = []
    for product_url in product_urls:
        product_info = scrape_product_info(product_url,"OXtek")
        all_product_info.append(product_info)

    return all_product_info

#scrape all pages 
def get_all_products(base_url,store):
    all_product_urls = set()
    page_num = 1

    while True:
        url = f'{base_url}?page={page_num}'

        try:
            # Make an HTTP request to the URL
            response = requests.get(url)
            response.raise_for_status()  # Check if the request was successful
            html = response.text
        except requests.exceptions.RequestException as e:
            print(f"Error fetching the URL: {e}")
            break  # Break out of the loop if an error occurs

        # Parse the HTML content with BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        # Find all product anchor tags
        product_anchors = soup.select('h2.product-title a')

        # Extract product URLs and add them to the set
        page_product_urls = [anchor['href'] for anchor in product_anchors]
        new_urls = set(page_product_urls) - all_product_urls
        all_product_urls.update(new_urls)

        # Check if there are no more products
        if not new_urls:
            print("No more new products found. Exiting.")
            break

        print("page: ", page_num)
        page_num += 1

    return list(all_product_urls)




# Test the main function with the main page URL
main_page_url = 'https://www.technopro-online.com/prix-pc-portable-hp-dell-asus-lenovo-acer-Tunisie.html'
result = main(main_page_url)
print(f'Number of products: {len(result)}')
# Print the result
for product_info in result:
    print(product_info)

# Convert the result to a DataFrame
df = pd.DataFrame(result)


# Save the DataFrame to an Excel file
df.to_csv('OXtek1.csv', index=False)
