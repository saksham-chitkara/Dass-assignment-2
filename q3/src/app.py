import os
import sys
import uuid
import datetime
import pymongo
from getpass import getpass
from pymongo import MongoClient
from bson.objectid import ObjectId
import threading
import time

try:
    client = MongoClient('mongodb+srv://sakshamchitkara:Saksham@cluster0.fx609kp.mongodb.net/')
    db = client['dollmart_db']
    
    users_collection = db['users']
    products_collection = db['products']
    orders_collection = db['orders']
    coupons_collection = db['coupons']
    
    users_collection.create_index([('email', pymongo.ASCENDING)], unique=True)
    users_collection.create_index([('user_id', pymongo.ASCENDING)], unique=True)
    products_collection.create_index([('product_id', pymongo.ASCENDING)], unique=True)
    products_collection.create_index([('name', pymongo.TEXT)])
    orders_collection.create_index([('order_id', pymongo.ASCENDING)], unique=True)
    coupons_collection.create_index([('code', pymongo.ASCENDING)], unique=True)
    
    print("Connected to MongoDB successfully!")
    
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    sys.exit(1)

class User:
    def __init__(self, name="", email="", phone="", address="", password=""):
        self.user_id = str(uuid.uuid4())
        self.name = name
        self.email = email
        self.phone = phone
        self.address = address
        self.password = password  
    
    def register(self):
        try:
            if users_collection.find_one({"email": self.email}):
                print("Email already registered!")
                return False
            
            user_data = {
                "user_id": self.user_id,
                "name": self.name,
                "email": self.email,
                "phone": self.phone,
                "address": self.address,
                "password": self.password,
                "cart_items": []  
            }

            users_collection.insert_one(user_data)
            print(f"User {self.name} registered successfully!")
            return True
        
        except Exception as e:
            print(f"Error registering user: {e}")
            return False
    
    @staticmethod
    def login(email, password):
        try:
            user = users_collection.find_one({"email": email, "password": password})
            if user:
                print(f"Welcome back, {user['name']}!")
                if user.get('user_type') == 'individual':
                    return IndividualCustomer.from_db(user)
                
                elif user.get('user_type') == 'retail':
                    return RetailStore.from_db(user)
                
                else:
                    return None
                
            else:
                print("Invalid email or password!")
                return None
            
        except Exception as e:
            print(f"Error during login: {e}")
            return None
        
class IndividualCustomer(User):    
    def __init__(self, name="", email="", phone="", address="", password=""):
        super().__init__(name, email, phone, address, password)
        self.loyalty_pts = 0
        self.purchase_history = []
        self.available_coupons = []
    
    def register(self):
        try:
            if users_collection.find_one({"email": self.email}):
                print("Email already registered!")
                return False
            
            user_data = {
                "user_id": self.user_id,
                "name": self.name,
                "email": self.email,
                "phone": self.phone,
                "address": self.address,
                "password": self.password,
                "user_type": "individual",
                "loyalty_pts": self.loyalty_pts,
                "purchase_history": self.purchase_history,
                "available_coupons": self.available_coupons,
                "cart_items": []  
            }

            users_collection.insert_one(user_data)
            print(f"Individual customer {self.name} registered successfully!")
            return True
        
        except Exception as e:
            print(f"Error registering individual customer: {e}")
            return False
    
    @staticmethod
    def from_db(user_data):
        customer = IndividualCustomer()
        customer.user_id = user_data.get('user_id')
        customer.name = user_data.get('name')
        customer.email = user_data.get('email')
        customer.phone = user_data.get('phone')
        customer.address = user_data.get('address')
        customer.password = user_data.get('password')
        customer.loyalty_pts = user_data.get('loyalty_pts', 0)
        customer.purchase_history = user_data.get('purchase_history', [])
        customer.available_coupons = user_data.get('available_coupons', [])
        customer.cart_items = user_data.get('cart_items', [])  
        return customer
    
class RetailStore(User):
    def __init__(self, name="", email="", phone="", address="", password="", store_name=""):
        super().__init__(name, email, phone, address, password)
        self.store_name = store_name
        self.bulk_discount_rate = 0.1
        self.purchase_history = []
    
    def register(self):
        try:
            if users_collection.find_one({"email": self.email}):
                print("Email already registered!")
                return False
            
            user_data = {
                "user_id": self.user_id,
                "name": self.name,
                "email": self.email,
                "phone": self.phone,
                "address": self.address,
                "password": self.password,
                "user_type": "retail",
                "store_name": self.store_name,
                "bulk_discount_rate": self.bulk_discount_rate,
                "purchase_history": self.purchase_history,
                "cart_items": []  # [CHANGE] Added cart_items field for retail store
            }

            users_collection.insert_one(user_data)
            print(f"Retail store {self.store_name} registered successfully!")
            return True
        
        except Exception as e:
            print(f"Error registering retail store: {e}")
            return False
    
    @staticmethod
    def from_db(user_data):
        store = RetailStore()
        store.user_id = user_data.get('user_id')
        store.name = user_data.get('name')
        store.email = user_data.get('email')
        store.phone = user_data.get('phone')
        store.address = user_data.get('address')
        store.password = user_data.get('password')
        store.store_name = user_data.get('store_name', '')
        store.bulk_discount_rate = user_data.get('bulk_discount_rate', 0.1)
        store.purchase_history = user_data.get('purchase_history', [])
        store.cart_items = user_data.get('cart_items', [])
        return store

class Product:
    def __init__(self, name="", description="", price=0.0, category="", subcategory="", stock_quantity=0):
        self.product_id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.price = price
        self.category = category
        self.subcategory = subcategory
        self.stock_quantity = stock_quantity
    
    def save_to_db(self):
        try:
            product_data = {
                "product_id": self.product_id,
                "name": self.name,
                "description": self.description,
                "price": self.price,
                "category": self.category,
                "subcategory": self.subcategory,
                "stock_quantity": self.stock_quantity,
            }

            products_collection.insert_one(product_data)
            print(f"Product '{self.name}' added successfully!")
            return True
        except Exception as e:
            print(f"Error adding product: {e}")
            return False
    
    def get_details(self):
        return {
            "product_id": self.product_id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "category": self.category,
            "subcategory": self.subcategory,
            "stock_quantity": self.stock_quantity
        }
    
    def update_stock(self, quantity):
        try:
            if quantity < 0 and abs(quantity) > self.stock_quantity:
                print("Not enough stock available!")
                return False
            
            self.stock_quantity += quantity
            products_collection.update_one(
                {"product_id": self.product_id},
                {"$set": {"stock_quantity": self.stock_quantity}}
            )

            print(f"Stock updated. New quantity: {self.stock_quantity}")
            return True
        
        except Exception as e:
            print(f"Error updating stock: {e}")
            return False
    
    @staticmethod
    def from_db(product_data):
        product = Product()
        product.product_id = product_data.get('product_id')
        product.name = product_data.get('name')
        product.description = product_data.get('description')
        product.price = product_data.get('price')
        product.category = product_data.get('category')
        product.subcategory = product_data.get('subcategory')
        product.stock_quantity = product_data.get('stock_quantity')
        return product

class ProductCatalog:
    @staticmethod
    def search_by_name(name):
        try:
            products = list(products_collection.find(
                {"name": {"$regex": name, "$options": "i"}}
            ))

            if not products:
                print(f"No products found matching '{name}'.")
                return []
            
            product_objects = [Product.from_db(p) for p in products]
            return product_objects
        
        except Exception as e:
            print(f"Error searching products: {e}")
            return []
    
    @staticmethod
    def search_by_category(category):
        try:
            products = list(products_collection.find(
                {"$or": [
                    {"category": {"$regex": category, "$options": "i"}},
                    {"subcategory": {"$regex": category, "$options": "i"}}
                ]}
            ))

            if not products:
                print(f"No products found in category '{category}'.")
                return []
            
            product_objects = [Product.from_db(p) for p in products]
            return product_objects
        
        except Exception as e:
            print(f"Error searching products by category: {e}")
            return []
    
    @staticmethod
    def get_all_products():
        try:
            products = list(products_collection.find())
            if not products:
                print("No products found in the catalog.")
                return []
            
            product_objects = [Product.from_db(p) for p in products]
            return product_objects
        
        except Exception as e:
            print(f"Error retrieving products: {e}")
            return []

class CartItem:
    def __init__(self, product, quantity=1):
        self.product = product
        self.quantity = quantity
    
    def get_subtotal(self):
        return self.product.price * self.quantity
    
    def to_dict(self):
        return {
            "product_id": self.product.product_id,
            "quantity": self.quantity,
            "price_at_purchase": self.product.price
        }

class ShoppingCart:
    def __init__(self, user):
        self.user = user
        self.items = []
        user_doc = users_collection.find_one({"user_id": self.user.user_id})

        if user_doc and "cart_items" in user_doc:
            for ci in user_doc["cart_items"]:
                prod_doc = products_collection.find_one({"product_id": ci["product_id"]})

                if prod_doc:
                    product = Product.from_db(prod_doc)
                    self.items.append(CartItem(product, ci["quantity"]))
    
    def add_item(self, product, quantity=1):
        try:
            if product.stock_quantity < quantity:
                print(f"Not enough stock available. Only {product.stock_quantity} units available.")
                return False
            
            for item in self.items:
                if item.product.product_id == product.product_id:
                    if item.quantity + quantity <= product.stock_quantity:
                        item.quantity += quantity

                        print(f"Added {quantity} more units of '{product.name}' to cart.")

                        users_collection.update_one(
                            {"user_id": self.user.user_id},
                            {"$set": {"cart_items": [ci.to_dict() for ci in self.items]}}
                        )  
                        return True
                    
                    else:
                        print(f"Not enough stock available. Only {product.stock_quantity - item.quantity} units more are available.")
                        return False
                    
            self.items.append(CartItem(product, quantity))
            users_collection.update_one(
                {"user_id": self.user.user_id},
                {"$set": {"cart_items": [ci.to_dict() for ci in self.items]}}
            )  

            print(f"Added '{product.name}' to cart.")
            return True
        except Exception as e:
            print(f"Error adding item to cart: {e}")
            return False
    
    def remove_item(self, product_id):
        try:
            initial_count = len(self.items)
            self.items = [item for item in self.items if item.product.product_id != product_id]

            users_collection.update_one(
                {"user_id": self.user.user_id},
                {"$set": {"cart_items": [ci.to_dict() for ci in self.items]}}
            ) 

            if len(self.items) < initial_count:
                print("Item removed from cart.")
                return True
            
            else:
                print("Item not found in cart.")
                return False
            
        except Exception as e:
            print(f"Error removing item from cart: {e}")
            return False
    
    def update_quantity(self, product_id, quantity):
        try:
            for item in self.items:
                if item.product.product_id == product_id:
                    db_product = products_collection.find_one({"product_id": product_id})

                    if db_product['stock_quantity'] < quantity:
                        print(f"Not enough stock available. Only {db_product['stock_quantity']} units available.")
                        return False
                    
                    item.quantity = quantity

                    users_collection.update_one(
                        {"user_id": self.user.user_id},
                        {"$set": {"cart_items": [ci.to_dict() for ci in self.items]}}
                    )  
                    print(f"Updated quantity to {quantity}.")
                    return True
                
            print("Item not found in cart.")
            return False
        
        except Exception as e:
            print(f"Error updating quantity: {e}")
            return False
    
    def calculate_total(self):
        return sum(item.get_subtotal() for item in self.items)
    
    def clear(self):
        self.items = []
        users_collection.update_one(
            {"user_id": self.user.user_id},
            {"$set": {"cart_items": []}}
        )  
        print("Cart cleared.")
    
    def display(self):
        if not self.items:
            print("Your cart is empty.")
            return
        
        print("\nShopping Cart:")
        print("-" * 60)
        print(f"{'Product':<30} {'Price':<10} {'Qty':<5} {'Subtotal':<10}")
        print("-" * 60)

        for i, item in enumerate(self.items, 1):
            print(f"{item.product.name:<30} ${item.product.price:<9.2f} {item.quantity:<5} ${item.get_subtotal():<9.2f}")

        print("-" * 60)
        print(f"Total: ${self.calculate_total():.2f}")

class Order:
    def __init__(self):
        self.order_id = str(uuid.uuid4())
        self.user = None
        self.items = []
        self.order_date = datetime.datetime.now()
        self.total_amount = 0.0
        self.final_amount = 0.0
        self.discount_applied = 0.0
        self.coupon_used = None
        self.status = "placed"
        self.delivery_address = ""
        self.estimated_delivery_time = datetime.datetime.now() + datetime.timedelta(minutes=20)
    
    def calculate_final_price(self, coupon=None):
        self.total_amount = sum(item.get_subtotal() for item in self.items)
        self.final_amount = self.total_amount

        if coupon:
            discount = self.total_amount * (coupon['discount_percentage'] / 100)
            self.final_amount -= discount
            self.discount_applied = discount
            self.coupon_used = coupon['coupon_id']

        elif hasattr(self.user, 'bulk_discount_rate') and self.user.bulk_discount_rate > 0:
            discount = self.total_amount * (self.user.bulk_discount_rate / 100)
            self.final_amount -= discount
            self.discount_applied = discount
        return self.final_amount
    
    def place_order(self):
        try:
            for item in self.items:
                db_product = products_collection.find_one({"product_id": item.product.product_id})
                if db_product['stock_quantity'] < item.quantity:
                    print(f"Not enough stock for '{item.product.name}'. Order cannot be placed.")
                    return False
                
            for item in self.items:
                products_collection.update_one(
                    {"product_id": item.product.product_id},
                    {"$inc": {"stock_quantity": -item.quantity}}
                )
                item.product.stock_quantity -= item.quantity  

            order_data = {
                "order_id": self.order_id,
                "user_id": self.user.user_id,
                "items": [item.to_dict() for item in self.items],
                "order_date": self.order_date,
                "total_amount": self.total_amount,
                "final_amount": self.final_amount,
                "discount_applied": self.discount_applied,
                "coupon_used": self.coupon_used,
                "status": self.status,
                "delivery_address": self.delivery_address,
                "estimated_delivery_time": self.estimated_delivery_time
            }

            orders_collection.insert_one(order_data)
            users_collection.update_one(
                {"user_id": self.user.user_id},
                {"$push": {"purchase_history": self.order_id}}
            )

            if isinstance(self.user, IndividualCustomer):
                pts_earned = int(self.final_amount / 10)
                Coupon.add_loyalty_points(self.user, pts_earned)

            print(f"Order placed successfully! Order ID: {self.order_id}")
            print("Estimated time for delivery = 20 mins")
            return True
        
        except Exception as e:
            print(f"Error placing order: {e}")
            return False
    
    def cancel_order(self):
        try:
            order = orders_collection.find_one({"order_id": self.order_id})
            if order['status'] == "delivered":
                print("This order cannot be cancelled as it has already been delivered.")
                return False
            
            orders_collection.update_one(
                {"order_id": self.order_id},
                {"$set": {"status": "cancelled"}}
            )
            self.status = "cancelled"

            for item in order['items']:
                products_collection.update_one(
                    {"product_id": item['product_id']},
                    {"$inc": {"stock_quantity": item['quantity']}}
                )

            for item in self.items:
                item.product.stock_quantity += item.quantity  

            print(f"Order {self.order_id} has been cancelled.")
            return True
        
        except Exception as e:
            print(f"Error cancelling order: {e}")
            return False
    
    def get_order_details(self):
        try:
            order = orders_collection.find_one({"order_id": self.order_id})
            if not order:
                print("Order not found.")
                return None
            
            items = []
            for item in order['items']:
                product = products_collection.find_one({"product_id": item['product_id']})
                if product:
                    items.append({
                        "product": product['name'],
                        "quantity": item['quantity'],
                        "price_at_purchase": item['price_at_purchase'],
                        "subtotal": item['price_at_purchase'] * item['quantity']
                    })

            order_details = {
                "order_id": order['order_id'],
                "order_date": order['order_date'],
                "items": items,
                "total_amount": order['total_amount'],
                "discount_applied": order['discount_applied'],
                "final_amount": order['final_amount'],
                "status": order['status'],
                "estimated_delivery_time": order.get("estimated_delivery_time", "unknown")
            }

            return order_details
        
        except Exception as e:
            print(f"Error getting order details: {e}")
            return None
    
    def track_order(self):
        try:
            order = orders_collection.find_one({"order_id": self.order_id})
            if order:
                self.status = order.get("status", self.status)
                self.estimated_delivery_time = order.get("estimated_delivery_time", self.estimated_delivery_time)

            if self.status == "cancelled":
                print("Order was cancelled.")
                return "cancelled"
            
            now = datetime.datetime.now()
            if self.status == "placed" and now >= self.estimated_delivery_time:
                self.update_status("delivered")

            if self.status == "placed":
                time_left = self.estimated_delivery_time - now
                minutes, seconds = divmod(int(time_left.total_seconds()), 60)
                time_left_str = f"{minutes} minutes and {seconds} seconds"
                print(f"Order Status: {self.status}")
                print(f"Time left for delivery: {time_left_str}")

            else:
                print("Order has been delivered.")

            return self.status
        
        except Exception as e:
            print(f"Error tracking order: {e}")
            return "unknown"
    
    def update_status(self, status):
        try:
            if status not in ["placed", "delivered", "cancelled"]:
                print("Invalid status. Allowed values: 'placed', 'delivered', 'cancelled'.")
                return False
            self.status = status

            orders_collection.update_one(
                {"order_id": self.order_id},
                {"$set": {"status": status}}
            )

            print(f"Order status updated to '{status}'.")
            return True
        
        except Exception as e:
            print(f"Error updating order status: {e}")
            return False

# -------- Coupon Class --------------
class Coupon: 
    def __init__(self, coupon_id, code, discount_percentage, valid_until, is_active=True, used=False):
        self.coupon_id = coupon_id
        self.code = code
        self.discount_percentage = discount_percentage
        self.valid_until = valid_until
        self.is_active = is_active
        self.used = used
    
    @staticmethod
    def generate_coupon_for_user(user, discount_percentage=10):
        try:
            updated_user = users_collection.find_one({"user_id": user.user_id})
            loyalty_pts = updated_user.get('loyalty_pts', 0)
            if loyalty_pts < 100:
                print(f"Not enough loyalty pts. Current: {loyalty_pts}, Required: 100")
                return False
            
            code = f"DMART{user.user_id[:5]}{str(uuid.uuid4())[:5]}".upper()
            valid_days = 30 

            coupon_data = {
                "coupon_id": str(uuid.uuid4()),
                "code": code,
                "discount_percentage": discount_percentage,
                "is_active": True,
                "valid_until": (datetime.datetime.now() + datetime.timedelta(days=valid_days)).isoformat(),
                "used": False
            }

            coupons_collection.insert_one(coupon_data)
            users_collection.update_one(
                {"user_id": user.user_id},
                {
                    "$push": {"available_coupons": coupon_data["coupon_id"]},
                    "$inc": {"loyalty_pts": -100}
                }
            )

            user.loyalty_pts -= 100
            print(f"Congratulations! You've earned a {discount_percentage}% discount coupon: {code}")
            print(f"Valid for {valid_days} days. 100 loyalty pts have been deducted.")
            return True
        
        except Exception as e:
            print(f"Error generating coupon: {e}")
            return False
    
    @staticmethod
    def view_available_coupons(user):
        try:
            user_doc = users_collection.find_one({"user_id": user.user_id})
            coupon_ids = user_doc.get('available_coupons', [])
            if not coupon_ids:
                print("You don't have any coupons available.")
                return []
            
            coupons = list(coupons_collection.find({
                "coupon_id": {"$in": coupon_ids},
                "is_active": True,
                "valid_until": {"$gte": datetime.datetime.now().isoformat()}
            }))

            if not coupons:
                print("You don't have any valid coupons at the moment.")
                return []
            
            print("\nYour Available Coupons:")
            for i, coupon in enumerate(coupons, 1):
                print(f"{i}. Code: {coupon['code']} - {coupon['discount_percentage']}% off - Valid until: {coupon['valid_until']}")
            return coupons
        
        except Exception as e:
            print(f"Error retrieving coupons: {e}")
            return []
    
    @staticmethod
    def apply_coupon(user, coupon_code):
        try:
            coupon = coupons_collection.find_one({
                "code": coupon_code,
                "is_active": True,
                "valid_until": {"$gte": datetime.datetime.now().isoformat()}
            })

            if not coupon:
                print("Invalid or expired coupon code!")
                return None
            
            user_doc = users_collection.find_one({"user_id": user.user_id})
            if coupon['coupon_id'] not in user_doc.get('available_coupons', []):
                print("This coupon is not assigned to your account!")
                return None
            
            print(f"Coupon applied! You get {coupon['discount_percentage']}% off.")
            users_collection.update_one(
                {"user_id": user.user_id},
                {"$pull": {"available_coupons": coupon["coupon_id"]}}
            )

            coupons_collection.update_one(
                {"coupon_id": coupon["coupon_id"]},
                {"$set": {"is_active": False}}
            )

            return coupon
        
        except Exception as e:
            print(f"Error applying coupon: {e}")
            return None
    
    @staticmethod
    def add_loyalty_points(user, pts):
        try:
            users_collection.update_one(
                {"user_id": user.user_id},
                {"$inc": {"loyalty_pts": pts}}
            )
            user.loyalty_pts += pts
            print(f"Added {pts} loyalty pts. Your new total: {user.loyalty_pts}")
            return True
        except Exception as e:
            print(f"Error adding loyalty points: {e}")
            return False

# ----- CLI Classes -----
class DollmartCLI:
    def __init__(self):
        self.current_user = None
        self.shopping_cart = None
    
    def start(self):

        print("\n" + "=" * 60)
        print("Welcome to Dollmart E-Market!".center(60))
        print("=" * 60)
        
        while True:
            self.show_main_menu()
            choice = input("Enter your choice (1-3): ")
            
            if choice == "1":
                self.login()
            elif choice == "2":
                self.register()
            elif choice == "3":
                print("\nThank you for visiting Dollmart. Goodbye!")
                break
            else:
                print("Invalid choice. Please try again.")
    
    def show_main_menu(self):
        print("\nMain Menu:")
        print("1. Login")
        print("2. Register")
        print("3. Exit")
    
    def login(self):
        print("\n----- Login -----")
        email = input("Email: ")
        password = getpass("Password: ")
        
        self.current_user = User.login(email, password)
        
        if self.current_user:
            self.shopping_cart = ShoppingCart(self.current_user)
            if isinstance(self.current_user, IndividualCustomer):
                self.individual_customer_menu()

            elif isinstance(self.current_user, RetailStore):
                self.retail_store_menu()
    
    def register(self):
        import re  
        print("\n----- Registration -----")
        print("Select user type:")
        print("1. Individual Customer")
        print("2. Retail Store")
        
        choice = input("Enter your choice (1-2): ")
        
        name = input("Name: ")
        email = input("Email: ")
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):  
            print("Invalid email format!")
            return
        
        phone = input("Phone: ")
        if not (phone.isdigit() and len(phone) == 10): 
            print("Invalid phone number. It must be 10 digits.")
            return
        
        address = input("Address: ")
        password = getpass("Password: ")
        
        if choice == "1":
            self.current_user = IndividualCustomer(name, email, phone, address, password)
            success = self.current_user.register()
            
            if success:
                print("Registration successful! You can now login.")
                self.shopping_cart = ShoppingCart(self.current_user)
                self.individual_customer_menu()
        
        elif choice == "2":
            store_name = input("Store Name: ")
            self.current_user = RetailStore(name, email, phone, address, password, store_name)
            success = self.current_user.register()
            
            if success:
                print("Registration successful! You can now login.")
                self.shopping_cart = ShoppingCart(self.current_user)
                self.retail_store_menu()
        
        else:
            print("Invalid choice.")

    
    def individual_customer_menu(self):
        while True:
            print("\n----- Individual Customer Menu -----")
            print(f"Welcome, {self.current_user.name}!")
            print(f"Loyalty pts: {self.current_user.loyalty_pts}")
            print("\n1. Browse Products")
            print("2. Search Products")
            print("3. View Shopping Cart")
            print("4. View Available Coupons")
            print("5. View Order History")
            print("6. Logout")
            
            choice = input("Enter your choice (1-6): ")
            
            if choice == "1":
                self.browse_products()
            elif choice == "2":
                self.search_products()
            elif choice == "3":
                self.view_cart()
            elif choice == "4":
                self.view_coupons()
            elif choice == "5":
                self.view_order_history()
            elif choice == "6":
                self.current_user = None
                self.shopping_cart = None
                break
            else:
                print("Invalid choice. Please try again.")
    
    def retail_store_menu(self):
        while True:
            print("\n----- Retail Store Menu -----")
            print(f"Welcome, {self.current_user.store_name}!")
            print(f"Bulk Discount Rate: {self.current_user.bulk_discount_rate * 100}%")
            
            print("\n1. Browse Products")
            print("2. Search Products")
            print("3. View Shopping Cart")
            print("4. View Order History")
            print("5. Logout")
            
            choice = input("Enter your choice (1-5): ")
            
            if choice == "1":
                self.browse_products()
            elif choice == "2":
                self.search_products()
            elif choice == "3":
                self.view_cart()
            elif choice == "4":
                self.view_order_history()
            elif choice == "5":
                self.current_user = None
                self.shopping_cart = None
                break
            else:
                print("Invalid choice. Please try again.")
    
    def browse_products(self):
        print("\n----- Browse Products -----")
        print("1. All Products")
        print("2. By Category")
        
        choice = input("Enter your choice (1-2): ")
        
        if choice == "1":
            products = ProductCatalog.get_all_products()
        elif choice == "2":
            category = input("Enter category or subcategory: ")
            products = ProductCatalog.search_by_category(category)
        else:
            print("Invalid choice.")
            return
        
        self.display_products(products)
    
    def search_products(self):
        name = input("\nEnter product name to search: ")
        products = ProductCatalog.search_by_name(name)
        self.display_products(products)
    
    def display_products(self, products):
        if not products:
            return
        
        print("\n----- Products -----")
        print(f"{'ID':<5} {'Name':<30} {'Category':<15} {'Price':<10} {'Stock':<10}")
        print("-" * 70)
        
        for i, product in enumerate(products, 1):
            print(f"{i:<5} {product.name[:28]:<30} {product.category[:13]:<15} ${product.price:<9.2f} {product.stock_quantity:<10}")
        
        while True:
            print("\n1. Add item to cart")
            print("2. View product details")
            print("3. Go back")
            
            choice = input("Enter your choice (1-3): ")
            
            if choice == "1":
                try:
                    idx = int(input("Enter product ID: ")) - 1
                    if 0 <= idx < len(products):
                        quantity = int(input("Enter quantity: "))
                        if quantity > 0:
                            self.shopping_cart.add_item(products[idx], quantity)
                        else:
                            print("Quantity must be greater than 0.")

                    else:
                        print("Invalid product ID.")

                except ValueError:
                    print("Please enter valid numeric values.")
            
            elif choice == "2":
                try:
                    idx = int(input("Enter product ID: ")) - 1
                    if 0 <= idx < len(products):
                        product = products[idx]
                        print("\n----- Product Details -----")
                        print(f"Name: {product.name}")
                        print(f"Category: {product.category}")
                        print(f"Subcategory: {product.subcategory}")
                        print(f"Price: ${product.price:.2f}")
                        print(f"Stock: {product.stock_quantity}")
                        print(f"Description: {product.description}")
                    else:
                        print("Invalid product ID.")

                except ValueError:
                    print("Please enter a valid product ID.")
            
            elif choice == "3":
                break
            
            else:
                print("Invalid choice.")
    
    def view_cart(self):
        if not self.shopping_cart or not self.shopping_cart.items:
            print("\nYour cart is empty.")
            return
        
        self.shopping_cart.display()
        
        while True:
            print("\n1. Update quantity")
            print("2. Remove item")
            print("3. Clear cart")
            print("4. Checkout")
            print("5. Go back")
            
            choice = input("Enter your choice (1-5): ")
            
            if choice == "1":
                try:
                    idx = int(input("Enter item number: ")) - 1
                    if 0 <= idx < len(self.shopping_cart.items):
                        quantity = int(input("Enter new quantity: "))
                        if quantity > 0:
                            self.shopping_cart.update_quantity(self.shopping_cart.items[idx].product.product_id, quantity)
                            self.shopping_cart.display()
                        else:
                            print("Quantity must be greater than 0.")

                    else:
                        print("Invalid item number.")

                except ValueError:
                    print("Please enter valid numeric values.")
            
            elif choice == "2":
                try:
                    idx = int(input("Enter item number: ")) - 1
                    if 0 <= idx < len(self.shopping_cart.items):
                        self.shopping_cart.remove_item(self.shopping_cart.items[idx].product.product_id)
                        self.shopping_cart.display()

                    else:
                        print("Invalid item number.")

                except ValueError:
                    print("Please enter a valid item number.")
            
            elif choice == "3":
                confirm = input("Are you sure you want to clear your cart? (y/n): ")
                if confirm.lower() == 'y':
                    self.shopping_cart.clear()
                    break
            
            elif choice == "4":
                self.checkout()
                break
            
            elif choice == "5":
                break
            
            else:
                print("Invalid choice.")
    
    def checkout(self):
        if not self.shopping_cart or not self.shopping_cart.items:
            print("\nYour cart is empty. Nothing to checkout.")
            return
        
        cart_total = self.shopping_cart.calculate_total()
        
        print("\n----- Checkout -----")
        print(f"Cart Total: ${cart_total:.2f}")
        
        if isinstance(self.current_user, IndividualCustomer):
            apply_coupon = input("Do you want to apply a coupon? (y/n): ")
            coupon = None
            
            if apply_coupon.lower() == 'y':
                coupons = Coupon.view_available_coupons(self.current_user)  
                if coupons:
                    coupon_code = input("Enter coupon code: ")
                    coupon = Coupon.apply_coupon(self.current_user, coupon_code) 
            
            order = Order()
            order.user = self.current_user
            order.items = self.shopping_cart.items
            order.delivery_address = self.current_user.address
            
            final_amount = order.calculate_final_price(coupon)
            print(f"Final Amount: ${order.final_amount:.2f}")
            
            if order.discount_applied > 0:
                print(f"You saved: ${order.discount_applied:.2f}")
            
            confirm = input("Confirm order? (y/n): ")
            if confirm.lower() == 'y':
                success = order.place_order()
                if success:
                    self.shopping_cart.clear()
        
        elif isinstance(self.current_user, RetailStore):
            discount = cart_total * self.current_user.bulk_discount_rate
            final_amount = cart_total - discount
            
            print(f"Bulk Discount ({self.current_user.bulk_discount_rate * 100}%): ${discount:.2f}")
            print(f"Final Amount: ${final_amount:.2f}")
            
            confirm = input("Confirm bulk order? (y/n): ")
            if confirm.lower() == 'y':
                success = self.current_user.request_bulk_order(self.shopping_cart)
                if success:
                    self.shopping_cart.clear()
    
    def view_coupons(self):
        if isinstance(self.current_user, IndividualCustomer):
            Coupon.view_available_coupons(self.current_user) 
            if self.current_user.loyalty_pts >= 100:
                print(f"\nYou have {self.current_user.loyalty_pts} loyalty pts.")
                print("You can generate a discount coupon (costs 100 pts).")
                
                gen = input("Generate a coupon? (y/n): ")
                if gen.lower() == 'y':
                    Coupon.generate_coupon_for_user(self.current_user)  
        else:
            print("This feature is only available for individual customers.")
    
    def view_order_history(self):
        try:
            user = users_collection.find_one({"user_id": self.current_user.user_id})
            order_ids = user.get('purchase_history', [])
            
            if not order_ids:
                print("\nYou haven't placed any orders yet.")
                return
            
            print("\n----- Order History -----")
            print(f"{'#':<3} {'Order ID':<15} {'Date':<20} {'Amount':<12} {'Status':<15}")
            print("-" * 65)
            
            for i, order_id in enumerate(order_ids, 1):
                order_data = orders_collection.find_one({"order_id": order_id})
                if order_data:

                    now = datetime.datetime.now()
                    if order_data.get('status') == "placed" and now >= order_data.get('estimated_delivery_time'):
                        orders_collection.update_one({"order_id": order_id}, {"$set": {"status": "delivered"}})
                        order_data["status"] = "delivered"

                    date = order_data.get('order_date').strftime('%Y-%m-%d %H:%M') if isinstance(order_data.get('order_date'), datetime.datetime) else str(order_data.get('order_date'))
                    print(f"{i:<3} {order_id[:13]:<15} {date:<20} ${order_data.get('final_amount', 0):<11.2f} {order_data.get('status', 'unknown'):<15}")
            
            while True:
                print("\n1. View order details")
                print("2. Track order")
                print("3. Cancel order")
                print("4. Go back")
                
                choice = input("Enter your choice (1-4): ")
                
                if choice == "1":
                    try:
                        idx = int(input("Enter order number: ")) - 1
                        if 0 <= idx < len(order_ids):
                            order = Order()
                            order.order_id = order_ids[idx]
                            details = order.get_order_details()
                            
                            if details:
                                print("\n----- Order Details -----")
                                print(f"Order ID: {details['order_id']}")
                                print(f"Date: {details['order_date']}")
                                print(f"Status: {details['status']}")
                                print(f"Estimated Delivery: {details['estimated_delivery_time']}")
                                
                                print("\nItems:")
                                for item in details['items']:
                                    print(f"- {item['product']} x{item['quantity']} @ ${item['price_at_purchase']:.2f} = ${item['subtotal']:.2f}")
                                
                                print(f"\nTotal: ${details['total_amount']:.2f}")
                                
                                if details['discount_applied'] > 0:
                                    print(f"Discount: ${details['discount_applied']:.2f}")
                                
                                print(f"Final Amount: ${details['final_amount']:.2f}")
                        else:
                            print("Invalid order number.")
                    except ValueError:
                        print("Please enter a valid order number.")
                
                elif choice == "2":
                    try:
                        idx = int(input("Enter order number: ")) - 1
                        if 0 <= idx < len(order_ids):
                            order = Order()
                            order.order_id = order_ids[idx]
                            order.track_order()

                        else:
                            print("Invalid order number.")
                    except ValueError:
                        print("Please enter a valid order number.")
                
                elif choice == "3":
                    try:
                        idx = int(input("Enter order number: ")) - 1
                        if 0 <= idx < len(order_ids):
                            order = Order()
                            order.order_id = order_ids[idx]
                            order.cancel_order()
                        else:
                            print("Invalid order number.")
                    except ValueError:
                        print("Please enter a valid order number.")
                
                elif choice == "4":
                    break
                
                else:
                    print("Invalid choice.")
            
        except Exception as e:
            print(f"Error retrieving order history: {e}")

if __name__ == "__main__":
    dollmart = DollmartCLI()
    dollmart.start()
