import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
import unittest
import time
import threading
from datetime import datetime, timedelta
from app import Restaurant, Order, Agent, FDS
from unittest.mock import patch

orig_sleep = time.sleep

def custom_sleep(x):
    if x >= 1:
        orig_sleep(0.1)
    else:
        orig_sleep(x)

class TestFoodDeliverySystem(unittest.TestCase):
    def setUp(self):
        if os.path.exists("fds_state.pkl"):
            try:
                os.remove("fds_state.pkl")
            except PermissionError:
                pass

        self.system = FDS.get_instance()
        self.system.orders = []
        self.system.agents = []
        self.system.restaurants = []

        Restaurant.restaurant_cnt = 1
        Order.order_cnt = 1
        Agent.agent_cnt = 1

        self.restaurant = Restaurant("Test Resto", ["Item1", "Item2", "Item3", "Item4", "Item5"])
        self.system.add_restaurant(self.restaurant)

        agent_names = [f"Agent{i}" for i in range(1, 11)]
        for name in agent_names:
            self.system.add_agent(Agent(name))
    
    def tearDown(self):
        try:
            if os.path.exists("fds_state.pkl"):
                os.remove("fds_state.pkl")
        except PermissionError:
            pass

        FDS._instance = None


    def test_home_delivery_order(self):
        order = self.system.place_order("Saksham", "Home Delivery", ["Item1", "Item2"], self.restaurant)
        self.assertEqual(order.customer_name, "Saksham")
        self.assertEqual(order.order_type, "Home Delivery")
        self.assertEqual(order.items, ["Item1", "Item2"])
        self.assertIsNotNone(order.assigned_agent)
        self.assertEqual(order.status, "Agent Assigned")


    def test_takeaway_order(self):
        order = self.system.place_order("Reddy", "Takeaway", ["Item1"], self.restaurant)
        self.assertEqual(order.customer_name, "Reddy")
        self.assertEqual(order.order_type, "Takeaway")
        self.assertEqual(order.items, ["Item1"])
        self.assertIsNone(order.assigned_agent)
        self.assertEqual(order.status, "Placed")


    @patch('time.sleep', lambda x: None)
    def test_agent_delivery_updates(self):
        order = self.system.place_order("Chahal", "Home Delivery", ["Item1"], self.restaurant)
        start = datetime.now()

        while order.status != "Delivered" and (datetime.now() - start).seconds < 120:
            time.sleep(0.01)

        self.assertEqual(order.status, "Delivered")
        self.assertIn(order.id, order.assigned_agent.delivered_orders)


    def test_manager_dashboard(self):
        order1 = self.system.place_order("Saksham", "Home Delivery", ["Item5"], self.restaurant)
        order2 = self.system.place_order("Sanyam", "Takeaway", ["Item2"], self.restaurant)
        dashboard = self.system.view_dashboard(self.restaurant.id)

        self.assertIn(order1, dashboard)
        self.assertIn(order2, dashboard)

    def test_state_persistence_and_order_count(self):
        order = self.system.place_order("Gaur", "Home Delivery", ["Item4"], self.restaurant)
        self.system.save_state()

        new_system = FDS.get_instance()
        orders = new_system.get_orders()
        self.assertTrue(any(o.id == order.id for o in orders))

        order2 = new_system.place_order("Chugh", "Takeaway", ["Item5"], self.restaurant)
        self.assertEqual(order2.id, order.id + 1)


    @patch('time.sleep', new=custom_sleep)
    def test_multiple_orders_over_agent_limit(self):
        orders = []
        for i in range(11):
            order = self.system.place_order(f"Customer{i}", "Home Delivery", ["Item1"], self.restaurant)
            orders.append(order)

        assigned_orders = [o for o in orders if o.assigned_agent is not None]
        unassigned_orders = [o for o in orders if o.assigned_agent is None]

        self.assertEqual(len(assigned_orders), 10)
        self.assertEqual(len(unassigned_orders), 1)

        time.sleep(0.2)
        all_assigned = [o for o in orders if o.assigned_agent is not None]
        self.assertEqual(len(all_assigned), 11)


    @patch.object(Agent, 'deliver_order', lambda self, order: None)
    def test_tracking_time_left(self):
        order = self.system.place_order("TestCustomer", "Home Delivery", ["Item1"], self.restaurant)
        output = str(order)
        self.assertIn("Time left:", output)


    @patch.object(Agent, 'deliver_order', lambda self, order: None)
    def test_multiple_orders_tracking(self):
        orders = []
        for i in range(5):
            order = self.system.place_order(f"TestCustomer{i}", "Home Delivery", ["Item1"], self.restaurant)
            orders.append(order)
        for order in orders:
            output = str(order)
            self.assertIn("Time left:", output)

if __name__ == '__main__':
    unittest.main()
