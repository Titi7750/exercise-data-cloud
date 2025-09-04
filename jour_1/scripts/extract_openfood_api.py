import requests
import pandas as pd

produits = []
url = f"https://world.openfoodfacts.org/api/v2/search?fields=code,product_name,brands,nutriscore_grade,energy_100g,fat_100g,sugars_100g,salt_100g&page_size=1000&page=1"
response = requests.get(url)
if response.status_code == 200:
    data = response.json()
    for prod in data["products"]:
        produits.append({
            "brands": prod.get("brands", ""),
            "code": prod.get("code", ""),
            "energy_100g": prod.get("nutriments", {}).get("energy_100g", None),
            "fat_100g": prod.get("nutriments", {}).get("fat_100g", None),
            "nutriscore_grade": prod.get("nutriscore_grade", ""),
            "product_name": prod.get("product_name", ""),
            "salt_100g": prod.get("nutriments", {}).get("salt_100g", None),
            "sugars_100g": prod.get("nutriments", {}).get("sugars_100g", None),
        })

df = pd.DataFrame(produits) 
df.to_csv("jour_1/data/openfoodfacts_sample.csv", index=False) 

print("CSV exporté avec succès !")
