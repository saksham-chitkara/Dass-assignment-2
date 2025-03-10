import uuid
import random
import datetime
from pymongo import MongoClient

def main():
    client = MongoClient("mongodb+srv://sakshamchitkara:Saksham@cluster0.fx609kp.mongodb.net/")
    db = client["dollmart_db"]
    products_collection = db["products"]

    categories = ["Electronics", "Groceries", "Clothing", "Home & Kitchen", "Books", "Toys"]
    subcategories = {
        "Electronics": ["Mobile Phones", "Laptops", "Cameras"],
        "Groceries": ["Beverages", "Snacks", "Dairy"],
        "Clothing": ["Men", "Women", "Kids"],
        "Home & Kitchen": ["Furniture", "Appliances", "Decor"],
        "Books": ["Fiction", "Non-Fiction", "Educational"],
        "Toys": ["Action Figures", "Puzzles", "Board Games"]
    }

    product_names = {
        "Electronics": ["Smartphone", "Laptop", "DSLR Camera", "Headphones", "Smartwatch"],
        "Groceries": ["Organic Apple", "Chocolate Bar", "Milk", "Bread", "Cheese"],
        "Clothing": ["T-Shirt", "Jeans", "Jacket", "Dress", "Sneakers"],
        "Home & Kitchen": ["Sofa", "Blender", "Lamp", "Cookware Set", "Curtains"],
        "Books": ["Mystery Novel", "Biography", "Science Textbook", "Cookbook", "Fantasy Novel"],
        "Toys": ["Action Figure", "Puzzle", "Board Game", "Stuffed Animal", "Building Blocks"]
    }
    descriptions = [
        "High quality product.",
        "Best in the market.",
        "Limited edition item.",
        "Affordable and durable.",
        "Customer favorite."
    ]

    num_products = 100  

    product_list = []
    for _ in range(num_products):
        category = random.choice(categories)
        subcat = random.choice(subcategories[category])
        name = random.choice(product_names[category])
        # Append a short UUID segment to ensure product name uniqueness
        full_name = f"{name} {str(uuid.uuid4())[:8]}"
        description = random.choice(descriptions)
        price = round(random.uniform(5.0, 500.0), 2)
        stock_quantity = random.randint(0, 100)
        now = datetime.datetime.now().isoformat()
        product = {
            "product_id": str(uuid.uuid4()),
            "name": full_name,
            "description": description,
            "price": price,
            "category": category,
            "subcategory": subcat,
            "stock_quantity": stock_quantity,
            "created_at": now,
            "updated_at": now
        }
        product_list.append(product)

    result = products_collection.insert_many(product_list)
    print(f"Inserted {len(result.inserted_ids)} products into the database.")

if __name__ == '__main__':
    main()
