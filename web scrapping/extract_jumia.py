import requests
import csv
import pandas as pd
from bs4 import BeautifulSoup
from scrape_product import*
import sys
sys.stdout.reconfigure(encoding='utf-8')

def get_all_products(base_url, store_name):
    all_products_info = []
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
            # Handle the error or break out of the loop
            break

        # Parse the HTML content with BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        # Find all elements containing product information
        product_elements = soup.find_all('a', class_='core')

        # If there are no product elements, break out of the loop
        if not product_elements:
            break

        # Iterate over each product element on the current page
        for product_element in product_elements:
            try:
                # Extract product information using the scrape_product_info function
                product_url1 = product_element['href']
                product_url=f'{base_url}{product_url1}'
                product_info = scrape_product_info(product_url,store_name)

                # Extract technical information using the extract_technical_info function
                technical_info = extract_technical_info(product_url)

                # Merge the two dictionaries
                merged_dict = {**flatten_dict(technical_info), **product_info }

                # Add the product dictionary to the list
                all_products_info.append(merged_dict)
            except Exception as e:
                print(f"Error extracting product information: {e}")

        # Check for the presence of the "Next Page" link
        pagination = soup.find('div', class_='pg-w')
        next_page_link = pagination.find('a', class_='pg', string=str(page_num + 1))

        # If there's no "Next Page" link, break out of the loop
        if not next_page_link:
            break
        print(page_num)
        # Move to the next page
        page_num += 1

    return all_products_info, page_num

# Example usage:
base_url = 'https://www.jumia.com.tn/mlp-informatique/pc-portables/'
store_name = 'jumia'
result, page_num = get_all_products(base_url, store_name)

if not result:
    print('No products found.')
else:
    print(f'Number of products: {len(result)}')
    print(f'Number of pages: {page_num}')

    # Convert the list of dictionaries to a DataFrame
    df = pd.DataFrame(result)
    print(df)

    # Assuming df is your DataFrame
    df.to_excel('jumia.xlsx', index=False)



