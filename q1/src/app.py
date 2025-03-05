import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
import time
import threading
from datetime import datetime, timedelta
import pickle
import os

class Restaurant:
    restaurant_cnt = 1

    def __init__(self, name, menu):
        self.id = Restaurant.restaurant_cnt
        Restaurant.restaurant_cnt += 1
        self.name = name
        self.menu = menu 

    def __str__(self):
        return f"{self.id}. {self.name}"

class Order:
    order_cnt = 1  

    def __init__(self, customer_name, order_type, items, restaurant):
        self.id = Order.order_cnt
        Order.order_cnt += 1

        self.customer_name = customer_name
        self.order_type = order_type 

        self.items = items
        self.restaurant = restaurant 

        self.order_time = datetime.now()

        if order_type == "Home Delivery":
            self.estimated_delivery_time = self.order_time + timedelta(minutes=2)
            self.estimated_preparation_time = None
        else:  
            self.estimated_preparation_time = self.order_time + timedelta(minutes=1)
            self.estimated_delivery_time = None

        self.status = "Placed"
        self.assigned_agent = None

    def update_status_based_on_time(self):
        now = datetime.now()
        
        if self.order_type == "Home Delivery":
            if self.assigned_agent and now >= self.estimated_delivery_time:
                self.status = "Delivered"
        elif self.order_type == "Takeaway":
            if now >= self.estimated_preparation_time:
                self.status = "Delivered"

    def __str__(self):
        self.update_status_based_on_time()
        str = (f"Order #{self.id} | Restaurant: {self.restaurant.name} | Customer: {self.customer_name} | "
                f"Type: {self.order_type} | Items: {self.items} | Status: {self.status}")
        
        if self.assigned_agent:
            str += f" | Assigned Agent: {self.assigned_agent.name}"

        now = datetime.now()
        if self.order_type == "Home Delivery":
            if self.assigned_agent:
                if now < self.estimated_delivery_time:
                    rem = self.estimated_delivery_time - now
                    if rem.seconds // 60 > 0:
                        minutes = rem.seconds // 60
                        str += f" | Time left: {minutes} minutes and {rem.seconds - 60 * minutes} seconds"
                    else:
                        seconds = rem.seconds
                        str += f" | Time left: {seconds} seconds"

        elif self.order_type == "Takeaway":
            if now < self.estimated_preparation_time:
                rem = self.estimated_preparation_time - now
                if rem.seconds // 60 > 0:
                    minutes = rem.seconds // 60
                    str += f" | Time left: {minutes} minutes and {rem.seconds - 60 * minutes} seconds"
                else:
                    seconds = rem.seconds
                    str += f" | Time left for preparation: {seconds} seconds"
        return str

class Agent:
    agent_cnt = 1

    def __init__(self, name):
        self.id = Agent.agent_cnt
        Agent.agent_cnt += 1
        self.name = name
        self.available = True
        self.current_order = None
        self.delivered_orders = []

    def assign_order(self, order):
        self.available = False
        self.current_order = order

        order.assigned_agent = self
        order.estimated_delivery_time = datetime.now() + timedelta(minutes=2)
        order.status = "Agent Assigned"
        
        t = threading.Thread(target=self.deliver_order, args=(order,))
        t.daemon = True
        t.start()

    def deliver_order(self, order):
        time.sleep(120)
        system = FDS.get_instance()
        for order_s in system.orders:
            if order_s.id == order.id:
                order_s.status = "Delivered"
                break

        agent_s = None

        for agent in system.agents:
            if agent.id == self.id:
                agent_s = agent
                agent.delivered_orders.append(order.id)
                agent.current_order = None
                agent.available = True

        system.save_state()

        for pending in system.orders:
            if pending.order_type == "Home Delivery" and pending.status == "Placed":
                agent.available = False
                agent.current_order = pending

                pending.assigned_agent = self
                pending.status = "Agent Assigned"

                pending.estimated_delivery_time = datetime.now() + timedelta(minutes=2)
                t = threading.Thread(target=self.deliver_order, args=(pending,))
                t.daemon = True
                t.start()

                system.save_state()
                break

    def __str__(self):
        if self.available == False:
            return f"ID: {self.id} | Name: {self.name} | Assigned Order ID: {self.current_order.id} | Delivered Orders: {self.delivered_orders}"
        else:
            return f"ID: {self.id} | Name: {self.name} | Available: {self.available} | Delivered Orders: {self.delivered_orders}"

class FDS:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self.orders = []
        self.agents = []
        self.restaurants = []

    @classmethod
    def get_instance(cls):
        if os.path.exists("fds_state.pkl"):
            with open("fds_state.pkl", "rb") as f:
                try:
                    instance = pickle.load(f)
                except EOFError:
                    instance = None

            if instance is not None:
                if instance.orders:
                    max_order = max(order.id for order in instance.orders)
                    Order.order_cnt = max_order + 1
                else:
                    Order.order_cnt = 1
                if instance.agents:
                    max_agent = max(agent.id for agent in instance.agents)
                    Agent.agent_cnt = max_agent + 1
                else:
                    Agent.agent_cnt = 1
                cls._instance = instance

        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = FDS()
        return cls._instance

    def save_state(self):
        with open("fds_state.pkl", "wb") as f:
            pickle.dump(self, f)

    def add_agent(self, agent):
        self.agents.append(agent)

    def add_restaurant(self, restaurant):
        self.restaurants.append(restaurant)

    def get_restaurant_by_id(self, rid):
        for restaurant in self.restaurants:
            if restaurant.id == rid:
                return restaurant
        return None

    def place_order(self, customer_name, order_type, items, restaurant):
        order = Order(customer_name, order_type, items, restaurant)
        self.orders.append(order)
        if order_type == "Home Delivery":
            self.assign_agent(order)
        return order

    def assign_agent(self, order):
        available_agents = [agent for agent in self.agents if agent.available]
        if available_agents:
            available_agents[0].assign_order(order)

    def get_orders(self):
        return self.orders

    def view_dashboard(self, restaurant_id):
        filtered_orders = [order for order in self.orders if order.restaurant.id == restaurant_id]
        return filtered_orders

def display_opt():
    print("1. Place an Order")
    print("2. Track an Order")
    print("3. Manager Dashboard")
    print("4. List Delivery Agents")
    print("5. Exit")

def place_order(system):
    system = FDS.get_instance()
    customer_name = input("Enter your name: ").strip()
    print("\nAvailable Restaurants:")

    for r in system.restaurants:
        print(r)

    try:
        restaurant_choice = int(input("Enter restaurant number: ").strip())
    except ValueError:
        print("Invalid input. Please enter a number.\n")
        return
    

    restaurant = system.get_restaurant_by_id(restaurant_choice)
    if not restaurant:
        print("Restaurant not found. Please try again.\n")
        return
    
    print(f"\nMenu for {restaurant.name}:")
    for idx, item in enumerate(restaurant.menu, start=1):
        print(f"{idx}. {item}")


    item_input = input("Enter item numbers (comma-separated, choose numbers 1-5): ").strip()


    try:
        chosen_numbers = [int(num.strip()) for num in item_input.split(",") if num.strip()]
        if not chosen_numbers or any(num < 1 or num > 5 for num in chosen_numbers):
            print("Error: Please enter valid numbers between 1 and 5.\n")
            return
    except ValueError:
        print("Error: Invalid input. Please enter numbers separated by commas.\n")
        return
    
    items = [restaurant.menu[num - 1] for num in chosen_numbers]
    print("\nSelect order type:")
    print("1. Home Delivery")
    print("2. Takeaway")

    order_type_choice = input("Enter 1 or 2: ").strip()
    if order_type_choice == "1":
        order_type = "Home Delivery"
    elif order_type_choice == "2":
        order_type = "Takeaway"
    else:
        print("Invalid order type selection.\n")
        return
    
    order = system.place_order(customer_name, order_type, items, restaurant)
    system.save_state()
    print(f"\nOrder placed successfully:\n{order}\n")

def track_order(system):
    try:
        order_id = int(input("Enter Order ID to track: ").strip())
    except ValueError:
        print("Invalid input. Please enter a valid number.\n")
        return
    
    system = FDS.get_instance()
    orders = system.get_orders()

    order = next((o for o in orders if o.id == order_id), None)
    if order:
        print(order)
        print("\n")
    else:
        print("Order not found.\n")

def manager_dashboard(system):
    system = FDS.get_instance()
    print("\nManager Dashboard\n")
    print("Restaurants:")
    for restaurant in system.restaurants:
        print(restaurant)

    try:
        rid = int(input("Enter restaurant number to view its orders: ").strip())
    except ValueError:
        print("Invalid input. Please enter a number.\n")
        return
    
    restaurant = system.get_restaurant_by_id(rid)
    if not restaurant:
        print("Restaurant not found.\n")
        return
    
    orders = system.view_dashboard(rid)
    if not orders:
        print(f"No orders found for {restaurant.name}.")
    else:
        print(f"\nOrders for {restaurant.name}:")
        for order in orders:
            print(order)

    print("\n")

def list_agents(system):
    system = FDS.get_instance()
    print("\nDelivery Agents\n")
    for agent in system.agents:
        print(agent)
    print("\n")

def main():
    system = FDS.get_instance()
    restaurants = [
        Restaurant("Taj Palace", ["Butter Chicken", "Paneer Tikka", "Naan", "Biryani", "Gulab Jamun"]),
        Restaurant("Spice Junction", ["Chicken Curry", "Dal Makhani", "Roti", "Samosa", "Kheer"]),
        Restaurant("Biryani House", ["Mutton Biryani", "Veg Biryani", "Raita", "Papad", "Lassi"]),
        Restaurant("Curry Delight", ["Chole Bhature", "Aloo Gobi", "Paratha", "Rasgulla", "Jeera Rice"]),
        Restaurant("Royal Tadka", ["Tandoori Chicken", "Mixed Veg", "Pulao", "Raita", "Mysore Pak"])
    ]

    for r in restaurants:
        system.add_restaurant(r)

    agent_names = ["Amit" , "Rahul", "Sanjay", "Vikram", "Rohan", "Arjun", "Karan", "Siddharth", "Manoj", "Pranav"]
    
    for name in agent_names:
        system.add_agent(Agent(name))
    
    while True:
        display_opt()
        opt = input("Enter your choice: ").strip()

        if opt == "1":
            place_order(system)
        elif opt == "2":
            track_order(system)
        elif opt == "3":
            manager_dashboard(system)
        elif opt == "4":
            list_agents(system)
        elif opt == "5":
            print("Exiting the system!\n")
            system = FDS.get_instance()
            system.save_state()
            break
        else:
            print("Invalid choice. Please try again.\n")

if __name__ == "__main__":
    main()
