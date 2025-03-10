import pymongo
import threading
import datetime
import time
import os
import getpass
import uuid
import re
from bson.objectid import ObjectId

app_lock = threading.Lock()

class Database:
    """Singleton Database connection class"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance.client = pymongo.MongoClient("mongodb+srv://sakshamchitkara:Saksham@cluster0.fx609kp.mongodb.net/")
            cls._instance.db = cls._instance.client["food_delivery_db"]
            
            cls._instance.db["users"].create_index([("email", pymongo.ASCENDING)], unique=True)
            cls._instance.db["users"].create_index([("phone", pymongo.ASCENDING)], unique=True)
            
            if cls._instance.db["admins"].count_documents({}) == 0:
                cls._instance.db["admins"].insert_one({
                    "username": "admin",
                    "password": "admin123", 
                    "name": "System Administrator"
                })
                print("Admin account created with username: 'admin' and password: 'admin123'")
            
        return cls._instance
    
    def get_collection(self, collection_name):
        return self.db[collection_name]


class User:
    def __init__(self, name, email, password, phone, address):
        self.name = name
        self.email = email
        self.password = password 
        self.phone = phone
        self.address = address
        self.user_id = None
    
    def save(self):
        db = Database()
        users_collection = db.get_collection("users")
        
        user_data = {
            "name": self.name,
            "email": self.email,
            "password": self.password,
            "phone": self.phone,
            "address": self.address,
            "created_at": datetime.datetime.now()
        }
        
        try:
            result = users_collection.insert_one(user_data)
            self.user_id = result.inserted_id
            return True
        
        except pymongo.errors.DuplicateKeyError:
            print("Error: Email or phone number already exists")
            return False
    
    @staticmethod
    def authenticate(email, password):
        db = Database()
        users_collection = db.get_collection("users")
        
        user = users_collection.find_one({"email": email, "password": password})
        if user:
            return user
        return None
    
    @staticmethod
    def get_by_id(user_id):
        db = Database()
        users_collection = db.get_collection("users")
        
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        return user


class Order:
    delivery_threads = {}  # Class variable to store all delivery threads
    pending_orders = []    # Class variable to store orders waiting for agents
    orders_lock = threading.Lock()  # Lock for thread-safe operations on pending orders
    
    def __init__(self, user_id, restaurant_id, items, delivery_type, total_amount):
        self.user_id = user_id
        self.restaurant_id = restaurant_id
        self.items = items  
        self.delivery_type = delivery_type  
        self.total_amount = total_amount
        self.order_id = None
    
    def save(self):
        db = Database()
        orders_collection = db.get_collection("orders")
        
        created_at = datetime.datetime.now()
        
        order_data = {
            "user_id": ObjectId(self.user_id),
            "restaurant_id": ObjectId(self.restaurant_id),
            "items": self.items,
            "delivery_type": self.delivery_type,
            "total_amount": self.total_amount,
            "status": "placed",
            "created_at": created_at,
            "estimated_delivery_time": None,
            "delivery_agent_id": None
        }
        
        result = orders_collection.insert_one(order_data)
        self.order_id = result.inserted_id
        
        if self.delivery_type == "home_delivery":
            self._assign_delivery_agent()
        else:
            self.estimated_delivery_time = datetime.datetime.now() + datetime.timedelta(minutes=3)
            estimated_delivery_time = datetime.datetime.now() + datetime.timedelta(minutes=3)
                
            orders_collection.update_one(
                {"_id": self.order_id},
                {
                    "$set": {
                        "estimated_delivery_time": estimated_delivery_time
                    }
                }
            )
        
        return self.order_id
    
    def _assign_delivery_agent(self):
        db = Database()
        agents_collection = db.get_collection("delivery_agents")
        orders_collection = db.get_collection("orders")
        
        with app_lock:
            available_agent = agents_collection.find_one({"status": "available"})
            
            if available_agent:

                estimated_delivery_time = datetime.datetime.now() + datetime.timedelta(minutes=2)
                
                orders_collection.update_one(
                    {"_id": self.order_id},
                    {
                        "$set": {
                            "delivery_agent_id": available_agent["_id"],
                            "status": "agent_assigned",
                            "estimated_delivery_time": estimated_delivery_time
                        }
                    }
                )
                
                DeliveryAgent.update_status(
                    available_agent["_id"], 
                    "busy", 
                    self.order_id
                )
                
                self._start_delivery_thread(self.order_id, available_agent["_id"])
            else:
                with Order.orders_lock:
                    Order.pending_orders.append(self.order_id)
    
    @classmethod
    def _start_delivery_thread(cls, order_id, agent_id):
        delivery_thread = threading.Thread(
            target=cls._delivery_process, 
            args=(order_id, agent_id),
            daemon=True
        )
        delivery_thread.start()
        cls.delivery_threads[str(order_id)] = delivery_thread
    
    @classmethod
    def _delivery_process(cls, order_id, agent_id):
        time.sleep(120)  # 2 minutes delivery time
        
        cls.update_status(order_id, "delivered")
        
        cls._assign_pending_order(agent_id)
    
    @classmethod
    def _assign_pending_order(cls, agent_id):
        db = Database()
        orders_collection = db.get_collection("orders")
        
        pending_order_id = None
        
        with cls.orders_lock:
            if cls.pending_orders:
                pending_order_id = cls.pending_orders.pop(0)
        
        if pending_order_id:
            estimated_delivery_time = datetime.datetime.now() + datetime.timedelta(minutes=2)
            
            orders_collection.update_one(
                {"_id": pending_order_id},
                {
                    "$set": {
                        "delivery_agent_id": agent_id,
                        "status": "agent_assigned",
                        "estimated_delivery_time": estimated_delivery_time
                    }
                }
            )
            
            DeliveryAgent.update_status(agent_id, "busy", pending_order_id)
            
            cls._start_delivery_thread(pending_order_id, agent_id)
    
    @staticmethod
    def get_by_id(order_id):
        db = Database()
        orders_collection = db.get_collection("orders")
        order = orders_collection.find_one({"_id": ObjectId(order_id)})
        return order
    
    @staticmethod
    def get_user_orders(user_id):
        db = Database()
        orders_collection = db.get_collection("orders")
        return list(orders_collection.find({"user_id": ObjectId(user_id)}).sort("created_at", pymongo.DESCENDING))
    
    @staticmethod
    def update_status(order_id, status):
        db = Database()
        orders_collection = db.get_collection("orders")
        orders_collection.update_one(
            {"_id": ObjectId(order_id)},
            {"$set": {"status": status}}
        )
        if status == "delivered":
            order = orders_collection.find_one({"_id": ObjectId(order_id)})
            if order and order["delivery_agent_id"]:
                DeliveryAgent.add_delivered_order(order["delivery_agent_id"], order_id)
    
    @staticmethod
    def mark_order_picked_up(order_id):
        db = Database()
        orders_collection = db.get_collection("orders")
        order = Order.get_by_id(order_id)
        if order and order["delivery_type"] == "takeaway":
            orders_collection.update_one(
                {"_id": ObjectId(order_id)},
                {"$set": {"status": "picked_up"}}
            )
            return True
        return False
    
    @staticmethod
    def track_order(order_id):
        order = Order.get_by_id(order_id) 
        if not order:
            return "Order not found"
        
        current_time = datetime.datetime.now()
        
        if order["delivery_type"] == "home_delivery":
            status_message = {
                "placed": "Order placed. Waiting for delivery agent assignment.",
                "agent_assigned": "Delivery agent assigned and on the way.",
                "delivered": "Order has been delivered."
            }
        else: 
            status_message = {
                "placed": "Order placed and ready for pickup.",
                "picked_up": "Order has been picked up."
            }
        
        tracking_info = {
            "order_id": str(order["_id"]),
            "status": order["status"],
            "status_message": status_message.get(order["status"], "Unknown status"),
            "delivery_type": order["delivery_type"]
        }
        
        if order["estimated_delivery_time"]:
            estimated_time = order["estimated_delivery_time"]
            tracking_info["estimated_delivery_time"] = estimated_time.strftime("%H:%M:%S")
            if order["status"] != "delivered" and order["status"] != "picked_up":
                time_left = estimated_time - current_time
                minutes_left = max(0, time_left.total_seconds() // 60)
                tracking_info["minutes_left"] = int(minutes_left)
        else:
            tracking_info["estimated_delivery_time"] = "Not available yet"
            tracking_info["minutes_left"] = "Not available"
        
        if order["delivery_agent_id"] and order["delivery_type"] == "home_delivery":
            agent = DeliveryAgent.get_by_id(order["delivery_agent_id"])
            if agent:
                tracking_info["delivery_agent"] = agent["name"]
        else:
            if order["delivery_type"] == "home_delivery":
                tracking_info["delivery_agent"] = "No agent assigned"
        
        return tracking_info


class Admin:
    @staticmethod
    def authenticate(username, password):
        db = Database()
        admins_collection = db.get_collection("admins")
        admin = admins_collection.find_one({"username": username, "password": password})
        if admin:
            return admin
        return None
    
    @staticmethod
    def add_delivery_agent(name, phone, email):
        db = Database()
        agents_collection = db.get_collection("delivery_agents")
        agent_data = {
            "name": name,
            "phone": phone,
            "email": email,
            "status": "available",
            "delivered_orders": [],
            "current_order": None,
            "created_at": datetime.datetime.now()
        }
        try:
            result = agents_collection.insert_one(agent_data)
            return True
        except Exception as e:
            print(f"Error adding delivery agent: {e}")
            return False
    
    @staticmethod
    def add_restaurant(name, address, cuisine_type):
        restaurant = Restaurant(name, address, cuisine_type)
        restaurant_id = restaurant.save()
        if restaurant_id:
            return True
        return False
    
    @staticmethod
    def view_all_agents():
        db = Database()
        agents_collection = db.get_collection("delivery_agents")
        return list(agents_collection.find())
    
    @staticmethod
    def view_available_agents():
        db = Database()
        agents_collection = db.get_collection("delivery_agents")
        return list(agents_collection.find({"status": "available"}))
    
    @staticmethod
    def view_all_orders():
        db = Database()
        orders_collection = db.get_collection("orders")
        return list(orders_collection.find().sort("created_at", pymongo.DESCENDING))
    
    @staticmethod
    def view_restaurant_orders(restaurant_id):
        db = Database()
        orders_collection = db.get_collection("orders")
        return list(orders_collection.find({"restaurant_id": ObjectId(restaurant_id)}).sort("created_at", pymongo.DESCENDING))
    
    @staticmethod
    def assign_agents_to_pending_orders():
        db = Database()
        orders_collection = db.get_collection("orders")
        agents_collection = db.get_collection("delivery_agents")
        with app_lock:
            available_agents = list(agents_collection.find({"status": "available"}))
            if not available_agents:
                return
            with Order.orders_lock:
                if not Order.pending_orders:
                    pending_db_orders = list(orders_collection.find({
                        "delivery_type": "home_delivery", 
                        "delivery_agent_id": None,
                        "status": "placed"
                    }).sort("created_at", pymongo.ASCENDING))
                    for order in pending_db_orders:
                        Order.pending_orders.append(order["_id"])
                for agent in available_agents:
                    if not Order.pending_orders:
                        break
                    order_id = Order.pending_orders.pop(0)
                    estimated_delivery_time = datetime.datetime.now() + datetime.timedelta(minutes=2)
                    orders_collection.update_one(
                        {"_id": order_id},
                        {
                            "$set": {
                                "delivery_agent_id": agent["_id"],
                                "status": "agent_assigned",
                                "estimated_delivery_time": estimated_delivery_time
                            }
                        }
                    )
                    DeliveryAgent.update_status(agent["_id"], "busy", order_id)
                    Order._start_delivery_thread(order_id, agent["_id"])


class DeliveryAgent:
    @staticmethod
    def get_by_id(agent_id):
        db = Database()
        agents_collection = db.get_collection("delivery_agents")
        return agents_collection.find_one({"_id": ObjectId(agent_id)})
    
    @staticmethod
    def update_status(agent_id, status, current_order=None):
        db = Database()
        agents_collection = db.get_collection("delivery_agents")
        update_data = {"status": status}
        if current_order is not None:
            update_data["current_order"] = current_order
        agents_collection.update_one(
            {"_id": ObjectId(agent_id)},
            {"$set": update_data}
        )
    
    @staticmethod
    def add_delivered_order(agent_id, order_id):
        db = Database()
        agents_collection = db.get_collection("delivery_agents")
        agents_collection.update_one(
            {"_id": ObjectId(agent_id)},
            {
                "$push": {"delivered_orders": order_id},
                "$set": {"status": "available", "current_order": None}
            }
        )
        Admin.assign_agents_to_pending_orders()


class Restaurant:
    def __init__(self, name, address, cuisine_type):
        self.name = name
        self.address = address
        self.cuisine_type = cuisine_type
        self.restaurant_id = None
    
    def save(self):
        db = Database()
        restaurants_collection = db.get_collection("restaurants")
        restaurant_data = {
            "name": self.name,
            "address": self.address,
            "cuisine_type": self.cuisine_type,
            "created_at": datetime.datetime.now()
        }
        result = restaurants_collection.insert_one(restaurant_data)
        self.restaurant_id = result.inserted_id
        return self.restaurant_id
    
    @staticmethod
    def get_all():
        db = Database()
        restaurants_collection = db.get_collection("restaurants")
        return list(restaurants_collection.find())
    
    @staticmethod
    def get_by_id(restaurant_id):
        db = Database()
        restaurants_collection = db.get_collection("restaurants")
        return restaurants_collection.find_one({"_id": ObjectId(restaurant_id)})
    
    @staticmethod
    def add_menu_item(restaurant_id, name, description, price, category):
        db = Database()
        menu_items_collection = db.get_collection("menu_items")
        menu_item = {
            "restaurant_id": ObjectId(restaurant_id),
            "name": name,
            "description": description,
            "price": price,
            "category": category,
            "created_at": datetime.datetime.now()
        }
        result = menu_items_collection.insert_one(menu_item)
        return result.inserted_id
    
    @staticmethod
    def get_menu(restaurant_id):
        db = Database()
        menu_items_collection = db.get_collection("menu_items")
        return list(menu_items_collection.find({"restaurant_id": ObjectId(restaurant_id)}))

class FoodDeliveryApp:
    def __init__(self):
        self.db = Database()
        self.current_user = None
        self.current_admin = None
        self.initialize_data()
    
    def initialize_data(self):
        """Initialize some sample data if database is empty"""
        restaurants_collection = self.db.get_collection("restaurants")
        
        if restaurants_collection.count_documents({}) == 0:
            restaurant1 = Restaurant("Tasty Bites", "123 Main St", "Italian")
            r1_id = restaurant1.save()
            
            restaurant2 = Restaurant("Spice Garden", "456 Oak Ave", "Indian")
            r2_id = restaurant2.save()
            
            Restaurant.add_menu_item(r1_id, "Margherita Pizza", "Classic cheese and tomato pizza", 12.99, "Main")
            Restaurant.add_menu_item(r1_id, "Spaghetti Carbonara", "Creamy pasta with bacon", 14.99, "Main")
            Restaurant.add_menu_item(r1_id, "Tiramisu", "Coffee-flavored Italian dessert", 6.99, "Dessert")
            
            Restaurant.add_menu_item(r2_id, "Butter Chicken", "Creamy tomato chicken curry", 15.99, "Main")
            Restaurant.add_menu_item(r2_id, "Vegetable Biryani", "Fragrant rice dish with vegetables", 13.99, "Main")
            Restaurant.add_menu_item(r2_id, "Gulab Jamun", "Sweet milk solids balls soaked in sugar syrup", 5.99, "Dessert")
            
            print("Sample restaurants and menu items added")
    
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def display_main_menu(self):
        self.clear_screen()
        print("\n===== FOOD DELIVERY SYSTEM =====")
        print("1. User Login")
        print("2. User Registration")
        print("3. Admin Login")
        print("4. Exit")
        choice = input("Enter your choice (1-4): ")
        
        if choice == "1":
            self.user_login()
        elif choice == "2":
            self.user_registration()
        elif choice == "3":
            self.admin_login()
        elif choice == "4":
            print("Thank you for using our service. Goodbye!")
            exit()
        else:
            print("Invalid choice. Please try again.")
            input("Press Enter to continue...")
            self.display_main_menu()
    
    def validate_email(self, email):
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None
    
    def validate_phone(self, phone):
        pattern = r"^\d{10}$"
        return re.match(pattern, phone) is not None
    
    def user_registration(self):
        self.clear_screen()
        print("\n===== USER REGISTRATION =====")
        
        name = input("Enter your full name: ")
        
        while True:
            email = input("Enter your email: ")
            if self.validate_email(email):
                break
            print("Invalid email format. Please try again.")
        
        password = getpass.getpass("Enter your password: ")
        confirm_password = getpass.getpass("Confirm your password: ")
        
        if password != confirm_password:
            print("Passwords don't match. Please try again.")
            input("Press Enter to continue...")
            self.user_registration()
            return
        
        while True:
            phone = input("Enter your phone number (10 digits): ")
            if self.validate_phone(phone):
                break
            print("Invalid phone number. Please enter a 10-digit number.")
        
        address = input("Enter your address: ")
        
        user = User(name, email, password, phone, address)
        if user.save():
            print("Registration successful! You can now login.")
        else:
            print("Registration failed. Please try again.")
        
        input("Press Enter to continue...")
        self.display_main_menu()
    
    def user_login(self):
        self.clear_screen()
        print("\n===== USER LOGIN =====")
        
        email = input("Enter your email: ")
        password = getpass.getpass("Enter your password: ")
        
        user = User.authenticate(email, password)
        if user:
            self.current_user = user
            print(f"Welcome back, {user['name']}!")
            input("Press Enter to continue...")
            self.display_user_menu()
        else:
            print("Invalid email or password.")
            input("Press Enter to continue...")
            self.display_main_menu()
    
    def admin_login(self):
        self.clear_screen()
        print("\n===== ADMIN LOGIN =====")
        
        username = input("Enter admin username: ")
        password = getpass.getpass("Enter admin password: ")
        
        admin = Admin.authenticate(username, password)
        if admin:
            self.current_admin = admin
            print(f"Welcome, Administrator {admin['name']}!")
            input("Press Enter to continue...")
            self.display_admin_menu()
        else:
            print("Invalid admin credentials.")
            input("Press Enter to continue...")
            self.display_main_menu()
    
    def display_user_menu(self):
        self.clear_screen()
        print(f"\n===== USER MENU ({self.current_user['name']}) =====")
        print("1. View Restaurants")
        print("2. My Orders")
        print("3. Track Order")
        print("4. Logout")
        choice = input("Enter your choice (1-4): ")
        
        if choice == "1":
            self.view_restaurants()
        elif choice == "2":
            self.view_user_orders()
        elif choice == "3":
            self.track_user_order()
        elif choice == "4":
            self.current_user = None
            print("Logged out successfully.")
            input("Press Enter to continue...")
            self.display_main_menu()
        else:
            print("Invalid choice. Please try again.")
            input("Press Enter to continue...")
            self.display_user_menu()
    
    def view_restaurants(self):
        self.clear_screen()
        print("\n===== RESTAURANTS =====")
        
        restaurants = Restaurant.get_all()
        if not restaurants:
            print("No restaurants available at the moment.")
            input("Press Enter to continue...")
            self.display_user_menu()
            return
        
        for i, restaurant in enumerate(restaurants, 1):
            print(f"{i}. {restaurant['name']} - {restaurant['cuisine_type']}")
        
        print("\n5. Back to User Menu")
        choice = input("Select a restaurant to view menu (or 5 to go back): ")
        
        if choice == "5":
            self.display_user_menu()
            return
        
        try:
            restaurant_index = int(choice) - 1
            if 0 <= restaurant_index < len(restaurants):
                self.view_restaurant_menu(restaurants[restaurant_index])
            else:
                print("Invalid selection.")
                input("Press Enter to continue...")
                self.view_restaurants()
        except ValueError:
            print("Invalid input. Please enter a number.")
            input("Press Enter to continue...")
            self.view_restaurants()
    
    def view_restaurant_menu(self, restaurant):
        self.clear_screen()
        print(f"\n===== {restaurant['name']} MENU =====")
        print(f"Cuisine: {restaurant['cuisine_type']}")
        print(f"Address: {restaurant['address']}")
        print("\n--- MENU ITEMS ---")
        
        menu_items = Restaurant.get_menu(restaurant["_id"])
        if not menu_items:
            print("No menu items available for this restaurant.")
            input("Press Enter to continue...")
            self.view_restaurants()
            return
        
        menu_by_category = {}
        for item in menu_items:
            category = item.get("category", "Other")
            if category not in menu_by_category:
                menu_by_category[category] = []
            menu_by_category[category].append(item)
        
        item_index_map = {} 
        index_counter = 1
        
        for category, items in menu_by_category.items():
            print(f"\n{category}:")
            for item in items:
                print(f"{index_counter}. {item['name']} - ${item['price']:.2f}")
                print(f"   {item['description']}")
                item_index_map[index_counter] = item
                index_counter += 1
        
        print("\nOptions:")
        print("1. Place an order")
        print("2. Back to restaurants")
        
        choice = input("Enter your choice (1-2): ")
        
        if choice == "2":
            self.view_restaurants()
        elif choice == "1":
            self.place_order(restaurant, menu_items, item_index_map)
        else:
            print("Invalid choice.")
            input("Press Enter to continue...")
            self.view_restaurant_menu(restaurant)
    
    def place_order(self, restaurant, menu_items, item_index_map):
        self.clear_screen()
        print(f"\n===== PLACE ORDER - {restaurant['name']} =====")
        
        cart = {} 
        total_amount = 0.0
        
        while True:
            print("\nCurrent Cart:")
            if not cart:
                print("Your cart is empty.")
            else:
                for item_id, quantity in cart.items():
                    menu_item = next((item for item in menu_items if str(item["_id"]) == item_id), None)
                    if menu_item:
                        item_total = menu_item["price"] * quantity
                        print(f"{menu_item['name']} x{quantity} - ${item_total:.2f}")
                
                print(f"\nTotal Amount: ${total_amount:.2f}")
            
            print("\nOptions:")
            print("1. Add an item to cart")
            print("2. Remove an item from cart")
            print("3. Proceed to checkout")
            print("4. Cancel order and go back")
            
            choice = input("Enter your choice (1-4): ")
            
            if choice == "4":
                self.view_restaurant_menu(restaurant)
                return
            elif choice == "1":
                self.clear_screen()
                print("Available Menu Items:")
                for index, item in item_index_map.items():
                    print(f"{index}. {item['name']} - ${item['price']:.2f}")
                
                item_choice = input("Enter the item number to add (or 5 to cancel): ")
                if item_choice == "5":
                    continue
                
                try:
                    item_index = int(item_choice)
                    if item_index in item_index_map:
                        selected_item = item_index_map[item_index]
                        quantity = input(f"How many {selected_item['name']} would you like to add? ")
                        try:
                            quantity = int(quantity)
                            if quantity <= 0:
                                print("Please enter a positive quantity.")
                                continue
                                
                            item_id = str(selected_item["_id"])
                            if item_id in cart:
                                cart[item_id] += quantity
                            else:
                                cart[item_id] = quantity
                            
                            total_amount += selected_item["price"] * quantity
                            print(f"Added {quantity} x {selected_item['name']} to cart.")
                        except ValueError:
                            print("Invalid quantity. Please enter a number.")
                    else:
                        print("Invalid item number.")
                except ValueError:
                    print("Invalid input. Please enter a number.")
            
            elif choice == "2":
                if not cart:
                    print("Your cart is empty.")
                    continue
                
                self.clear_screen()
                print("Items in Cart:")
                cart_items = list(cart.items())
                for i, (item_id, quantity) in enumerate(cart_items, 1):
                    menu_item = next((item for item in menu_items if str(item["_id"]) == item_id), None)
                    if menu_item:
                        print(f"{i}. {menu_item['name']} x{quantity}")
                
                remove_choice = input("Enter the number of the item to remove (or 5 to cancel): ")
                if remove_choice == "5":
                    continue
                
                try:
                    remove_index = int(remove_choice) - 1
                    if 0 <= remove_index < len(cart_items):
                        item_id, quantity = cart_items[remove_index]
                        menu_item = next((item for item in menu_items if str(item["_id"]) == item_id), None)
                        if menu_item:
                            remove_qty = input(f"How many {menu_item['name']} would you like to remove? (current: {quantity}): ")
                            try:
                                remove_qty = int(remove_qty)
                                if remove_qty <= 0:
                                    print("Please enter a positive quantity.")
                                    continue
                                
                                if remove_qty >= quantity:
                                    total_amount -= menu_item["price"] * quantity
                                    del cart[item_id]
                                    print(f"Removed {menu_item['name']} from cart.")
                                else:
                                    cart[item_id] -= remove_qty
                                    total_amount -= menu_item["price"] * remove_qty
                                    print(f"Reduced {menu_item['name']} quantity by {remove_qty}.")
                            except ValueError:
                                print("Invalid quantity. Please enter a number.")
                    else:
                        print("Invalid item number.")
                except ValueError:
                    print("Invalid input. Please enter a number.")
            
            elif choice == "3":
                if not cart:
                    print("Your cart is empty. Please add items before checkout.")
                    continue
                
                self.checkout(restaurant, cart, total_amount)
                return
    
    def checkout(self, restaurant, cart, total_amount):
        self.clear_screen()
        print(f"\n===== CHECKOUT - {restaurant['name']} =====")
        print(f"Total Amount: ${total_amount:.2f}")
        
        print("\nDelivery Options:")
        print("1. Home Delivery (Estimated Time: 2 minutes)")
        print("2. Takeaway (Estimated Time: 3 minutes)")
        
        delivery_choice = input("Select delivery option (1-2): ")
        
        if delivery_choice not in ["1", "2"]:
            print("Invalid choice.")
            input("Press Enter to continue...")
            self.checkout(restaurant, cart, total_amount)
            return
        
        delivery_type = "home_delivery" if delivery_choice == "1" else "takeaway"

        order_items = [{"item_id": item_id, "quantity": quantity} for item_id, quantity in cart.items()]
        
        order = Order(
            self.current_user["_id"],
            restaurant["_id"],
            order_items,
            delivery_type,
            total_amount
        )
        
        order_id = order.save()
        
        print("\nOrder placed successfully!")
        print(f"Order ID: {order_id}")
        # print(f"Estimated delivery time: {datetime.datetime.now() + datetime.timedelta(minutes=2 if delivery_type == 'home_delivery' else 15)}")
        
        input("Press Enter to continue...")
        self.display_user_menu()
    
    def view_user_orders(self):
        self.clear_screen()
        print("\n===== MY ORDERS =====")
        
        orders = Order.get_user_orders(self.current_user["_id"])
        
        if not orders:
            print("You have no orders yet.")
            input("Press Enter to continue...")
            self.display_user_menu()
            return
        
        for i, order in enumerate(orders, 1):
            restaurant = Restaurant.get_by_id(order["restaurant_id"])
            restaurant_name = restaurant["name"] if restaurant else "Unknown Restaurant"
            
            order_time = order["created_at"].strftime("%Y-%m-%d %H:%M")
            delivery_type = "Home Delivery" if order["delivery_type"] == "home_delivery" else "Takeaway"
            
            print(f"{i}. Order #{str(order['_id'])[-6:]} - {restaurant_name}")
            print(f"   Date: {order_time} | Status: {order['status'].capitalize()} | Type: {delivery_type}")
            print(f"   Total: ${order['total_amount']:.2f}")
        
        print("\nOptions:")
        print("1. View order details")
        print("2. Track an order")
        print("3. Back to User Menu")
        
        choice = input("Enter your choice (1-3): ")
        
        if choice == "3":
            self.display_user_menu()
        elif choice == "1":
            order_index = input("Enter the order number to view details: ")
            try:
                order_index = int(order_index)
                if 1 <= order_index <= len(orders):
                    self.view_order_details(orders[order_index - 1])
                else:
                    print("Invalid order number.")
                    input("Press Enter to continue...")
                    self.view_user_orders()
            except ValueError:
                print("Invalid input. Please enter a number.")
                input("Press Enter to continue...")
                self.view_user_orders()
        elif choice == "2":
            self.track_user_order()
        else:
            print("Invalid choice. Please try again.")
            input("Press Enter to continue...")
            self.view_user_orders()
    
    def view_order_details(self, order):
        self.clear_screen()
        print(f"\n===== ORDER DETAILS #{str(order['_id'])[-6:]} =====")
        
        restaurant = Restaurant.get_by_id(order["restaurant_id"])
        restaurant_name = restaurant["name"] if restaurant else "Unknown Restaurant"
        
        print(f"Restaurant: {restaurant_name}")
        print(f"Order Date: {order['created_at'].strftime('%Y-%m-%d %H:%M')}")
        print(f"Status: {order['status'].capitalize()}")
        print(f"Delivery Type: {'Home Delivery' if order['delivery_type'] == 'home_delivery' else 'Takeaway'}")
        
        if order["delivery_type"] == "home_delivery" and order["delivery_agent_id"]:
            agent = DeliveryAgent.get_by_id(order["delivery_agent_id"])
            if agent:
                print(f"Delivery Agent: {agent['name']}")
                print(f"Estimated Delivery: {order['estimated_delivery_time'].strftime('%H:%M:%S')}")
        
        print("\n--- ORDER ITEMS ---")
        db = Database()
        menu_items_collection = db.get_collection("menu_items")
        
        total = 0.0
        for item_entry in order["items"]:
            item_id = item_entry["item_id"]
            quantity = item_entry["quantity"]
            
            menu_item = menu_items_collection.find_one({"_id": ObjectId(item_id)})
            if menu_item:
                item_total = menu_item["price"] * quantity
                total += item_total
                print(f"{menu_item['name']} x{quantity} - ${item_total:.2f}")
        
        print(f"\nTotal Amount: ${order['total_amount']:.2f}")
        
        print("\nOptions:")
        print("1. Track this order")
        print("2. Back to My Orders")
        
        choice = input("Enter your choice (1-2): ")
        
        if choice == "2":
            self.view_user_orders()
        elif choice == "1":
            self.track_specific_order(order["_id"])
        else:
            print("Invalid choice.")
            input("Press Enter to continue...")
            self.view_order_details(order)
    
    def track_user_order(self):
        self.clear_screen()
        print("\n===== TRACK ORDER =====")
        
        orders = Order.get_user_orders(self.current_user["_id"])
        active_orders = [order for order in orders if order["status"] != "delivered"]
        
        if not active_orders:
            print("You have no active orders to track.")
            input("Press Enter to continue...")
            self.display_user_menu()
            return
        
        print("Your Active Orders:")
        for i, order in enumerate(active_orders, 1):
            restaurant = Restaurant.get_by_id(order["restaurant_id"])
            restaurant_name = restaurant["name"] if restaurant else "Unknown Restaurant"
            order_time = order["created_at"].strftime("%Y-%m-%d %H:%M")
            
            print(f"{i}. Order #{str(order['_id'])[-6:]} - {restaurant_name}")
            print(f"   Date: {order_time} | Status: {order['status'].capitalize()}")
        
        print("\n5. Back to User Menu")
        choice = input("Select an order to track (or 5 to go back): ")
        
        if choice == "5":
            self.display_user_menu()
            return
        
        try:
            order_index = int(choice) - 1
            if 0 <= order_index < len(active_orders):
                self.track_specific_order(active_orders[order_index]["_id"])
            else:
                print("Invalid selection.")
                input("Press Enter to continue...")
                self.track_user_order()
        except ValueError:
            print("Invalid input. Please enter a number.")
            input("Press Enter to continue...")
            self.track_user_order()
    
    def track_specific_order(self, order_id):
        self.clear_screen()
        print(f"\n===== TRACKING ORDER #{str(order_id)[-6:]} =====")
        
        tracking_info = Order.track_order(order_id)
        
        if isinstance(tracking_info, str):
            print(tracking_info) 
            input("Press Enter to continue...")
            self.track_user_order()
            return
        
        print(f"Status: {tracking_info['status'].capitalize()}")
        print(f"Status Message: {tracking_info['status_message']}")

        if(tracking_info['estimated_delivery_time']):
            print(f"Estimated Delivery Time: {tracking_info['estimated_delivery_time']}")
            
            if tracking_info['status'] != "delivered":
                print(f"Time Left: {tracking_info['minutes_left']} minutes")
            
            if "delivery_agent" in tracking_info:
                print(f"Delivery Agent: {tracking_info['delivery_agent']}")
        
        print("\nOptions:")
        print("1. Refresh tracking")
        print("2. Back to orders")
        
        choice = input("Enter your choice (1-2): ")
        
        if choice == "2":
            self.track_user_order()
        elif choice == "1":
            self.track_specific_order(order_id)
        else:
            print("Invalid choice.")
            input("Press Enter to continue...")
            self.track_specific_order(order_id)
    
    def display_admin_menu(self):
        self.clear_screen()
        print(f"\n===== ADMIN MENU ({self.current_admin['name']}) =====")
        print("1. Manage Delivery Agents")
        print("2. View All Orders")
        print("3. Restaurant Dashboard")
        print("4. Add Restaurant")
        print("5. Logout")
        choice = input("Enter your choice (1-5): ")
        
        if choice == "1":
            self.manage_delivery_agents()
        elif choice == "2":
            self.view_all_orders()
        elif choice == "3":
            self.restaurant_dashboard()
        elif choice == "4":
            self.add_restaurant()
        elif choice == "5":
            self.current_admin = None
            print("Logged out successfully.")
            input("Press Enter to continue...")
            self.display_main_menu()
        else:
            print("Invalid choice. Please try again.")
            input("Press Enter to continue...")
            self.display_admin_menu()

    def add_restaurant(self):
        self.clear_screen()
        print("\n===== ADD RESTAURANT =====")
        name = input("Enter restaurant name: ").strip()
        address = input("Enter restaurant address: ").strip()
        cuisine_type = input("Enter cuisine type: ").strip()
        if Admin.add_restaurant(name, address, cuisine_type):
            print("Restaurant added successfully!")
        else:
            print("Failed to add restaurant.")
        input("Press Enter to continue...")
        self.display_admin_menu()

    def manage_delivery_agents(self):
        self.clear_screen()
        print("\n===== MANAGE DELIVERY AGENTS =====")
        print("1. View All Delivery Agents")
        print("2. View Available Agents")
        print("3. Add New Delivery Agent")
        print("4. Back to Admin Menu")
        
        choice = input("Enter your choice (1-4): ")
        
        if choice == "4":
            self.display_admin_menu()
        elif choice == "1":
            self.view_all_agents()
        elif choice == "2":
            self.view_available_agents()
        elif choice == "3":
            self.add_delivery_agent()
        else:
            print("Invalid choice. Please try again.")
            input("Press Enter to continue...")
            self.manage_delivery_agents()
    
    def view_all_agents(self):
        self.clear_screen()
        print("\n===== ALL DELIVERY AGENTS =====")
        
        agents = Admin.view_all_agents()
        
        if not agents:
            print("No delivery agents in the system.")
            input("Press Enter to continue...")
            self.manage_delivery_agents()
            return
        
        print(f"Total Agents: {len(agents)}")
        print("\nID | Name | Status | Phone | Email | Delivered Orders")
        print("-" * 80)
        
        for agent in agents:
            agent_id = str(agent["_id"])[-6:]
            status = agent["status"].capitalize()
            delivered_count = len(agent["delivered_orders"])
            
            print(f"{agent_id} | {agent['name']} | {status} | {agent['phone']} | {agent['email']} | {delivered_count}")
        
        print("\n1. View Agent Details")
        print("2. Back to Manage Delivery Agents")
        
        choice = input("Enter your choice (1-2): ")
        
        if choice == "2":
            self.manage_delivery_agents()
        elif choice == "1":
            agent_id = input("Enter the agent ID to view details: ")
            
            selected_agent = next((a for a in agents if str(a["_id"])[-6:] == agent_id), None)
            
            if selected_agent:
                self.view_agent_details(selected_agent)
            else:
                print("Agent not found.")
                input("Press Enter to continue...")
                self.view_all_agents()
        else:
            print("Invalid choice.")
            input("Press Enter to continue...")
            self.view_all_agents()
    
    def view_agent_details(self, agent):
        self.clear_screen()
        print(f"\n===== AGENT DETAILS: {agent['name']} =====")
        print(f"ID: {str(agent['_id'])[-6:]}")
        print(f"Status: {agent['status'].capitalize()}")
        print(f"Phone: {agent['phone']}")
        print(f"Email: {agent['email']}")
        print(f"Joined: {agent['created_at'].strftime('%Y-%m-%d')}")
        
        if agent["current_order"]:
            order = Order.get_by_id(agent["current_order"])
            if order:
                print("\nCurrent Assignment:")
                print(f"Order #{str(order['_id'])[-6:]}")
                restaurant = Restaurant.get_by_id(order["restaurant_id"])
                if restaurant:
                    print(f"Restaurant: {restaurant['name']}")
                user = User.get_by_id(order["user_id"])
                if user:
                    print(f"Customer: {user['name']}")
                print(f"Status: {order['status'].capitalize()}")
        
        print("\nDelivered Orders:")
        if not agent["delivered_orders"]:
            print("No orders delivered yet.")
        else:
            for i, order_id in enumerate(agent["delivered_orders"][-5:], 1):  # Show last 5 orders
                order = Order.get_by_id(order_id)
                if order:
                    restaurant = Restaurant.get_by_id(order["restaurant_id"])
                    restaurant_name = restaurant["name"] if restaurant else "Unknown"
                    delivery_time = order.get("delivery_time", order["created_at"]).strftime("%Y-%m-%d %H:%M")
                    print(f"{i}. Order #{str(order['_id'])[-6:]} - {restaurant_name} - {delivery_time}")
        
        print("\n1. Back to All Agents")
        choice = input("Enter 1 to go back: ")
        self.view_all_agents()
    
    def view_available_agents(self):
        self.clear_screen()
        print("\n===== AVAILABLE DELIVERY AGENTS =====")
        
        agents = Admin.view_available_agents()
        
        if not agents:
            print("No available delivery agents at the moment.")
            input("Press Enter to continue...")
            self.manage_delivery_agents()
            return
        
        print(f"Available Agents: {len(agents)}")
        print("\nID | Name | Phone | Email | Delivered Orders")
        print("-" * 70)
        
        for agent in agents:
            agent_id = str(agent["_id"])[-6:]
            delivered_count = len(agent["delivered_orders"])
            
            print(f"{agent_id} | {agent['name']} | {agent['phone']} | {agent['email']} | {delivered_count}")
        
        input("\nPress Enter to continue...")
        self.manage_delivery_agents()
    
    def add_delivery_agent(self):
        self.clear_screen()
        print("\n===== ADD NEW DELIVERY AGENT =====")
        
        name = input("Enter agent's full name: ")
        
        while True:
            phone = input("Enter agent's phone number (10 digits): ")
            if self.validate_phone(phone):
                break
            print("Invalid phone number. Please enter a 10-digit number.")
        
        while True:
            email = input("Enter agent's email: ")
            if self.validate_email(email):
                break
            print("Invalid email format. Please try again.")
        
        if Admin.add_delivery_agent(name, phone, email):
            print("Delivery agent added successfully!")
        else:
            print("Failed to add delivery agent.")
        
        input("Press Enter to continue...")
        self.manage_delivery_agents()
    
    def view_all_orders(self):
        self.clear_screen()
        print("\n===== ALL ORDERS =====")
        
        orders = Admin.view_all_orders()
        
        if not orders:
            print("No orders in the system.")
            input("Press Enter to continue...")
            self.display_admin_menu()
            return
        
        print(f"Total Orders: {len(orders)}")
        print("\nOrder ID | Restaurant | Status | Type | Date | Amount")
        print("-" * 80)
        
        for order in orders:
            order_id = str(order["_id"])[-6:]
            restaurant = Restaurant.get_by_id(order["restaurant_id"])
            restaurant_name = restaurant["name"] if restaurant else "Unknown"
            status = order["status"].capitalize()
            order_type = "Delivery" if order["delivery_type"] == "home_delivery" else "Takeaway"
            date = order["created_at"].strftime("%Y-%m-%d %H:%M")
            amount = f"${order['total_amount']:.2f}"
            
            print(f"{order_id} | {restaurant_name} | {status} | {order_type} | {date} | {amount}")
        
        print("\n1. View Order Details")
        print("2. Back to Admin Menu")
        
        choice = input("Enter your choice (1-2): ")
        
        if choice == "2":
            self.display_admin_menu()
        elif choice == "1":
            order_id = input("Enter the order ID to view details: ")
            
            selected_order = next((o for o in orders if str(o["_id"])[-6:] == order_id), None)
            
            if selected_order:
                self.admin_view_order_details(selected_order)
            else:
                print("Order not found.")
                input("Press Enter to continue...")
                self.view_all_orders()
        else:
            print("Invalid choice.")
            input("Press Enter to continue...")
            self.view_all_orders()
    
    def admin_view_order_details(self, order):
        self.clear_screen()
        print(f"\n===== ORDER DETAILS #{str(order['_id'])[-6:]} =====")
        
        restaurant = Restaurant.get_by_id(order["restaurant_id"])
        restaurant_name = restaurant["name"] if restaurant else "Unknown Restaurant"
        
        user = User.get_by_id(order["user_id"])
        user_name = user["name"] if user else "Unknown User"
        
        print(f"Restaurant: {restaurant_name}")
        print(f"Customer: {user_name}")
        print(f"Order Date: {order['created_at'].strftime('%Y-%m-%d %H:%M')}")
        print(f"Status: {order['status'].capitalize()}")
        print(f"Delivery Type: {'Home Delivery' if order['delivery_type'] == 'home_delivery' else 'Takeaway'}")
        
        if order["delivery_type"] == "home_delivery" and order["delivery_agent_id"]:
            agent = DeliveryAgent.get_by_id(order["delivery_agent_id"])
            if agent:
                print(f"Delivery Agent: {agent['name']}")
        
        print(f"Estimated Delivery: {order['estimated_delivery_time'].strftime('%H:%M:%S')}")
        
        print("\n--- ORDER ITEMS ---")
        db = Database()
        menu_items_collection = db.get_collection("menu_items")
        
        total = 0.0
        for item_entry in order["items"]:
            item_id = item_entry["item_id"]
            quantity = item_entry["quantity"]
            
            menu_item = menu_items_collection.find_one({"_id": ObjectId(item_id)})
            if menu_item:
                item_total = menu_item["price"] * quantity
                total += item_total
                print(f"{menu_item['name']} x{quantity} - ${item_total:.2f}")
        
        print(f"\nTotal Amount: ${order['total_amount']:.2f}")
        
        print("\n1. Back to All Orders")
        
        choice = input("Enter 1 to go back: ")
        
        if choice == "1":
            self.view_all_orders()
        else:
            print("Invalid choice.")
            input("Press Enter to continue...")
            self.admin_view_order_details(order)
    
    def restaurant_dashboard(self):
        self.clear_screen()
        print("\n===== RESTAURANT DASHBOARD =====")
        
        restaurants = Restaurant.get_all()
        
        if not restaurants:
            print("No restaurants available.")
            input("Press Enter to continue...")
            self.display_admin_menu()
            return
        
        print("Select a restaurant to view:")
        for i, restaurant in enumerate(restaurants, 1):
            print(f"{i}. {restaurant['name']}")
        
        print(f"{len(restaurants) + 1}. Back to Admin Menu")
        choice = input("Enter your choice: ")
        
        if choice == str(len(restaurants) + 1):
            self.display_admin_menu()
            return
        
        try:
            restaurant_index = int(choice) - 1
            if 0 <= restaurant_index < len(restaurants):
                self.view_restaurant_dashboard(restaurants[restaurant_index])
            else:
                print("Invalid selection.")
                input("Press Enter to continue...")
                self.restaurant_dashboard()
        except ValueError:
            print("Invalid input. Please enter a number.")
            input("Press Enter to continue...")
            self.restaurant_dashboard()
    
    def view_restaurant_dashboard(self, restaurant):
        self.clear_screen()
        print(f"\n===== {restaurant['name']} DASHBOARD =====")
        
        orders = Admin.view_restaurant_orders(restaurant["_id"])
        
        total_orders = len(orders)
        pending_orders = sum(1 for order in orders if order["status"] != "delivered")
        delivered_orders = total_orders - pending_orders
        
        total_revenue = sum(order["total_amount"] for order in orders)
        
        print(f"Total Orders: {total_orders}")
        print(f"Pending Orders: {pending_orders}")
        print(f"Completed Orders: {delivered_orders}")
        print(f"Total Revenue: ${total_revenue:.2f}")
        
        print("\n--- RECENT ORDERS ---")
        recent_orders = orders[:10]  # Show last 10 orders
        
        if not recent_orders:
            print("No orders for this restaurant.")
        else:
            for i, order in enumerate(recent_orders, 1):
                order_id = str(order["_id"])[-6:]
                status = order["status"].capitalize()
                order_type = "Delivery" if order["delivery_type"] == "home_delivery" else "Takeaway"
                date = order["created_at"].strftime("%Y-%m-%d %H:%M")
                amount = f"${order['total_amount']:.2f}"
                
                print(f"{i}. Order #{order_id} | {status} | {order_type} | {date} | {amount}")
        
        print("\nOptions:")
        print("1. View Menu Items")
        print("2. Add Menu Item")
        print("3. View All Orders")
        print("4. Back to Restaurant Selection")
        
        choice = input("Enter your choice (1-4): ")
        
        if choice == "4":
            self.restaurant_dashboard()
        elif choice == "1":
            self.view_restaurant_menu_admin(restaurant)
        elif choice == "2":
            self.add_menu_item(restaurant)
        elif choice == "3":
            self.view_restaurant_orders(restaurant)
        else:
            print("Invalid choice.")
            input("Press Enter to continue...")
            self.view_restaurant_dashboard(restaurant)
    
    def view_restaurant_menu_admin(self, restaurant):
        self.clear_screen()
        print(f"\n===== {restaurant['name']} MENU =====")
        
        menu_items = Restaurant.get_menu(restaurant["_id"])
        
        if not menu_items:
            print("No menu items available for this restaurant.")
            input("Press Enter to continue...")
            self.view_restaurant_dashboard(restaurant)
            return
        
        menu_by_category = {}
        for item in menu_items:
            category = item.get("category", "Other")
            if category not in menu_by_category:
                menu_by_category[category] = []
            menu_by_category[category].append(item)
        
        for category, items in menu_by_category.items():
            print(f"\n{category}:")
            for i, item in enumerate(items, 1):
                print(f"{i}. {item['name']} - ${item['price']:.2f}")
                print(f"   {item['description']}")
        
        input("\nPress Enter to continue...")
        self.view_restaurant_dashboard(restaurant)
    
    def add_menu_item(self, restaurant):
        self.clear_screen()
        print(f"\n===== ADD MENU ITEM TO {restaurant['name']} =====")
        
        name = input("Enter item name: ")
        description = input("Enter item description: ")
        
        price = input("Enter item price: $")
        try:
            price = float(price)
            if price <= 0:
                raise ValueError
        except ValueError:
            print("Invalid price. Please enter a positive number.")
            input("Press Enter to continue...")
            self.add_menu_item(restaurant)
            return
        
        category = input("Enter item category (e.g., Appetizer, Main, Dessert): ")
        
        Restaurant.add_menu_item(restaurant["_id"], name, description, price, category)
        print("Menu item added successfully!")
        
        input("Press Enter to continue...")
        self.view_restaurant_dashboard(restaurant)
    
    def view_restaurant_orders(self, restaurant):
        self.clear_screen()
        print(f"\n===== {restaurant['name']} ORDERS =====")
        
        orders = Admin.view_restaurant_orders(restaurant["_id"])
        
        if not orders:
            print("No orders for this restaurant.")
            input("Press Enter to continue...")
            self.view_restaurant_dashboard(restaurant)
            return
        
        print("Order ID | Status | Type | Date | Amount")
        print("-" * 70)
        
        for order in orders:
            order_id = str(order["_id"])[-6:]
            status = order["status"].capitalize()
            order_type = "Delivery" if order["delivery_type"] == "home_delivery" else "Takeaway"
            date = order["created_at"].strftime("%Y-%m-%d %H:%M")
            amount = f"${order['total_amount']:.2f}"
            
            print(f"{order_id} | {status} | {order_type} | {date} | {amount}")
        
        print("\n1. View Order Details")
        print("2. Back to Restaurant Dashboard")
        
        choice = input("Enter your choice (1-2): ")
        
        if choice == "2":
            self.view_restaurant_dashboard(restaurant)
        elif choice == "1":
            order_id = input("Enter the order ID to view details: ")
            
            selected_order = next((o for o in orders if str(o["_id"])[-6:] == order_id), None)
            
            if selected_order:
                self.admin_view_order_details(selected_order)
            else:
                print("Order not found.")
                input("Press Enter to continue...")
                self.view_restaurant_orders(restaurant)
        else:
            print("Invalid choice.")
            input("Press Enter to continue...")
            self.view_restaurant_orders(restaurant)


def main():
    app = FoodDeliveryApp()
    app.display_main_menu()


if __name__ == "__main__":
    main()