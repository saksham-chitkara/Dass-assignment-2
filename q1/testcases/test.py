import unittest
from unittest.mock import patch, MagicMock, Mock
import pymongo
import datetime
import time
import threading
from bson.objectid import ObjectId
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from app import Database, User, Order, Admin, DeliveryAgent, Restaurant

class TestDatabase(unittest.TestCase):
    @patch('pymongo.MongoClient')
    def test_singleton_pattern(self, mock_client):
        """Test that Database follows singleton pattern"""
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.__getitem__.return_value = mock_instance
        mock_instance.count_documents.return_value = 1
        
        db1 = Database()
        db2 = Database()
        self.assertIs(db1, db2, "Database instances should be the same object")
        
class TestUser(unittest.TestCase):
    def setUp(self):
        self.user = User(
            name="Test User",
            email="test@example.com",
            password="password123",
            phone="1234567890",
            address="123 Test St"
        )
        
        self.patcher = patch('app3.Database.get_collection')
        self.mock_get_collection = self.patcher.start()
        self.mock_users_collection = MagicMock()
        self.mock_get_collection.return_value = self.mock_users_collection
    
    def tearDown(self):
        self.patcher.stop()
    
    def test_user_save_success(self):
        """Test successfully saving a user"""
        
        mock_result = MagicMock()
        mock_result.inserted_id = ObjectId("123456789012345678901234")
        self.mock_users_collection.insert_one.return_value = mock_result
        
        
        result = self.user.save()
        
        
        self.assertTrue(result)
        self.assertEqual(self.user.user_id, ObjectId("123456789012345678901234"))
        self.mock_users_collection.insert_one.assert_called_once()
    
    def test_user_save_duplicate(self):
        """Test saving a user with duplicate email or phone"""
        self.mock_users_collection.insert_one.side_effect = pymongo.errors.DuplicateKeyError("Duplicate key error")
        result = self.user.save()
        self.assertFalse(result)
    
    def test_authenticate_success(self):
        """Test successful user authentication"""
        
        mock_user = {
            "_id": ObjectId("123456789012345678901234"),
            "name": "Test User",
            "email": "test@example.com"
        }
        self.mock_users_collection.find_one.return_value = mock_user
        
        # Test authenticate
        user = User.authenticate("test@example.com", "password123")
        
        
        self.assertEqual(user, mock_user)
        self.mock_users_collection.find_one.assert_called_with(
            {"email": "test@example.com", "password": "password123"}
        )
    
    def test_authenticate_fail(self):
        """Test failed user authentication"""
        
        self.mock_users_collection.find_one.return_value = None
        
        # Test authenticate
        user = User.authenticate("test@example.com", "wrong_password")
        
        
        self.assertIsNone(user)
    
    def test_get_by_id(self):
        """Test getting a user by ID"""
        
        mock_user = {
            "_id": ObjectId("123456789012345678901234"),
            "name": "Test User",
            "email": "test@example.com"
        }
        self.mock_users_collection.find_one.return_value = mock_user
        
        # Test get_by_id
        user = User.get_by_id("123456789012345678901234")
        
        
        self.assertEqual(user, mock_user)
        self.mock_users_collection.find_one.assert_called_with(
            {"_id": ObjectId("123456789012345678901234")}
        )
    
    def test_get_by_id_not_found(self):
        """Test getting a non-existent user by ID"""
        
        self.mock_users_collection.find_one.return_value = None
        
        # Test get_by_id
        user = User.get_by_id("123456789012345678901234")
        
        
        self.assertIsNone(user)


class TestOrder(unittest.TestCase):
    def setUp(self):
        # Create test data
        self.user_id = "123456789012345678901234"
        self.restaurant_id = "234567890123456789012345"
        self.items = [
            {"item_id": "345678901234567890123456", "name": "Pizza", "price": 10.99, "quantity": 1}
        ]
        self.total_amount = 10.99
        
        # Create a test order for pickup
        self.pickup_order = Order(self.user_id, self.restaurant_id, self.items, "takeaway", self.total_amount)
        
        self.delivery_order = Order(self.user_id, self.restaurant_id, self.items, "home_delivery", self.total_amount)
        
        self.patcher = patch('app3.Database.get_collection')
        self.mock_get_collection = self.patcher.start()
        
        self.mock_orders_collection = MagicMock()
        self.mock_agents_collection = MagicMock()
        
        def get_collection_side_effect(collection_name):
            if collection_name == "orders":
                return self.mock_orders_collection
            elif collection_name == "delivery_agents":
                return self.mock_agents_collection
            return MagicMock()
        
        self.mock_get_collection.side_effect = get_collection_side_effect
        
        self.thread_patcher = patch('threading.Thread')
        self.mock_thread = self.thread_patcher.start()
        
        self.lock_patcher = patch('app3.app_lock')
        self.mock_lock = self.lock_patcher.start()
        
        self.orders_lock_patcher = patch('app3.Order.orders_lock')
        self.mock_orders_lock = self.orders_lock_patcher.start()
        
        Order.pending_orders = []
    
    def tearDown(self):
        self.patcher.stop()
        self.thread_patcher.stop()
        self.lock_patcher.stop()
        self.orders_lock_patcher.stop()
    
    def test_order_save_pickup(self):
        """Test saving a pickup order"""
        
        inserted_id = ObjectId("456789012345678901234567")
        self.mock_orders_collection.insert_one.return_value = MagicMock(inserted_id=inserted_id)
        
        order_id = self.pickup_order.save()
        
        
        self.assertEqual(order_id, inserted_id)
        self.mock_agents_collection.find_one.assert_not_called()
        update_call_args = self.mock_orders_collection.update_one.call_args[0]
        self.assertEqual(update_call_args[0], {"_id": inserted_id})
        self.assertIn("estimated_delivery_time", update_call_args[1]["$set"])
    
    def test_order_save_delivery_with_agent(self):
        """Test saving a delivery order with available agent"""
        
        inserted_id = ObjectId("456789012345678901234567")
        self.mock_orders_collection.insert_one.return_value = MagicMock(inserted_id=inserted_id)
        
        agent_id = ObjectId("567890123456789012345678")
        self.mock_agents_collection.find_one.return_value = {"_id": agent_id, "name": "Test Agent"}
        
        order_id = self.delivery_order.save()
        
        
        self.assertEqual(order_id, inserted_id)
        self.mock_agents_collection.find_one.assert_called_with({"status": "available"})
        update_call_args = self.mock_orders_collection.update_one.call_args[0]
        self.assertEqual(update_call_args[0], {"_id": inserted_id})
        self.assertEqual(update_call_args[1]["$set"]["delivery_agent_id"], agent_id)
        self.assertEqual(update_call_args[1]["$set"]["status"], "agent_assigned")
        self.mock_thread.assert_called_once()
    
    def test_order_save_delivery_no_agent(self):
        """Test saving a delivery order with no available agent"""
        inserted_id = ObjectId("456789012345678901234567")
        self.mock_orders_collection.insert_one.return_value = MagicMock(inserted_id=inserted_id)
        
        self.mock_agents_collection.find_one.return_value = None
        
        original_length = len(Order.pending_orders)
        order_id = self.delivery_order.save()
        
        self.assertEqual(order_id, inserted_id)
        self.mock_agents_collection.find_one.assert_called_with({"status": "available"})
        self.assertEqual(len(Order.pending_orders), original_length + 1)
        self.mock_thread.assert_not_called()
    
    @patch('time.sleep')
    @patch('app3.Order.update_status')
    @patch('app3.Order._assign_pending_order')
    def test_delivery_process(self, mock_assign_pending, mock_update_status, mock_sleep):
        """Test the delivery process"""
        order_id = ObjectId("456789012345678901234567")
        agent_id = ObjectId("567890123456789012345678")
        
        Order._delivery_process(order_id, agent_id)
        
        
        mock_sleep.assert_called_once_with(120)
        mock_update_status.assert_called_once_with(order_id, "delivered")
        mock_assign_pending.assert_called_once_with(agent_id)
    
    def test_assign_pending_order_with_pending(self):
        """Test assigning a pending order when one exists"""
        pending_order_id = ObjectId("456789012345678901234567")
        Order.pending_orders = [pending_order_id]
        
        agent_id = ObjectId("567890123456789012345678")
        
        Order._assign_pending_order(agent_id)
                
        self.assertEqual(Order.pending_orders, [])
        update_call_args = self.mock_orders_collection.update_one.call_args[0]
        self.assertEqual(update_call_args[0], {"_id": pending_order_id})
        self.assertEqual(update_call_args[1]["$set"]["delivery_agent_id"], agent_id)
        self.assertEqual(update_call_args[1]["$set"]["status"], "agent_assigned")
    
    def test_assign_pending_order_no_pending(self):
        """Test assigning a pending order when none exist"""
        Order.pending_orders = []
        agent_id = ObjectId("567890123456789012345678")
        
        # Test assign pending order
        Order._assign_pending_order(agent_id)
        
        self.mock_orders_collection.update_one.assert_not_called()
    
    def test_get_by_id(self):
        """Test getting an order by ID"""
        order_id = "456789012345678901234567"
        mock_order = {"_id": ObjectId(order_id), "status": "placed"}
        self.mock_orders_collection.find_one.return_value = mock_order
        
        # Test get_by_id
        order = Order.get_by_id(order_id)
        
        
        self.assertEqual(order, mock_order)
        self.mock_orders_collection.find_one.assert_called_with({"_id": ObjectId(order_id)})
    
    def test_get_user_orders(self):
        """Test getting all orders for a user"""
        user_id = "123456789012345678901234"
        mock_orders = [
            {"_id": ObjectId("456789012345678901234567"), "status": "placed"},
            {"_id": ObjectId("567890123456789012345678"), "status": "delivered"}
        ]
        
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_orders
        self.mock_orders_collection.find.return_value = mock_cursor
        
        # Test get_user_orders
        orders = Order.get_user_orders(user_id)
        
        
        self.assertEqual(orders, mock_orders)
        self.mock_orders_collection.find.assert_called_with({"user_id": ObjectId(user_id)})
    
    def test_update_status_simple(self):
        """Test updating order status without delivery completion"""
        order_id = "456789012345678901234567"
        
        # Mock order not delivered
        self.mock_orders_collection.find_one.return_value = None
        
        # Test update_status
        Order.update_status(order_id, "agent_assigned")
        
        
        self.mock_orders_collection.update_one.assert_called_with(
            {"_id": ObjectId(order_id)},
            {"$set": {"status": "agent_assigned"}}
        )
    
    def test_update_status_delivered(self):
        """Test updating order status to delivered"""
        order_id = "456789012345678901234567"
        agent_id = ObjectId("567890123456789012345678")
        
        mock_order = {
            "_id": ObjectId(order_id),
            "status": "agent_assigned",
            "delivery_agent_id": agent_id
        }
        self.mock_orders_collection.find_one.return_value = mock_order
        
        # Expecting the order_id to be passed as a string in the current code.
        with patch('app3.DeliveryAgent.add_delivered_order') as mock_add_delivered:
            Order.update_status(order_id, "delivered")
            
            self.mock_orders_collection.update_one.assert_called_with(
                {"_id": ObjectId(order_id)},
                {"$set": {"status": "delivered"}}
            )
            # Now expect order_id as string
            mock_add_delivered.assert_called_with(agent_id, order_id)
    
    def test_mark_order_picked_up_success(self):
        """Test marking a takeaway order as picked up"""
        order_id = "456789012345678901234567"
        
        # Mock takeaway order
        mock_order = {
            "_id": ObjectId(order_id),
            "status": "placed",
            "delivery_type": "takeaway"
        }
        self.mock_orders_collection.find_one.return_value = mock_order
        
        # Test mark_order_picked_up
        result = Order.mark_order_picked_up(order_id)
        
        
        self.assertTrue(result)
        self.mock_orders_collection.update_one.assert_called_with(
            {"_id": ObjectId(order_id)},
            {"$set": {"status": "picked_up"}}
        )
    
    def test_mark_order_picked_up_fail_delivery(self):
        """Test marking a delivery order as picked up (should fail)"""
        order_id = "456789012345678901234567"
        
        # Mock delivery order
        mock_order = {
            "_id": ObjectId(order_id),
            "status": "agent_assigned",
            "delivery_type": "home_delivery"
        }
        self.mock_orders_collection.find_one.return_value = mock_order
        
        # Test mark_order_picked_up
        result = Order.mark_order_picked_up(order_id)
        
        self.assertFalse(result)
        self.mock_orders_collection.update_one.assert_not_called()
    
    def test_track_order_not_found(self):
        """Test tracking a non-existent order"""
        order_id = "456789012345678901234567"
        
        # Mock order not found
        with patch('app3.Order.get_by_id', return_value=None):
            # Test track_order
            result = Order.track_order(order_id)
            
            
            self.assertEqual(result, "Order not found")
    
    def test_track_order_home_delivery(self):
        """Test tracking a home delivery order"""
        order_id = "456789012345678901234567"
        agent_id = ObjectId("567890123456789012345678")
        
        # Mock delivery order
        mock_order = {
            "_id": ObjectId(order_id),
            "status": "agent_assigned",
            "delivery_type": "home_delivery",
            "delivery_agent_id": agent_id,
            "estimated_delivery_time": datetime.datetime.now() + datetime.timedelta(minutes=10)
        }
        
        # Mock agent
        mock_agent = {
            "_id": agent_id,
            "name": "Test Agent"
        }
        
        with patch('app3.Order.get_by_id', return_value=mock_order):
            with patch('app3.DeliveryAgent.get_by_id', return_value=mock_agent):
                # Test track_order
                tracking_info = Order.track_order(order_id)
                
                
                self.assertEqual(tracking_info["order_id"], str(order_id))
                self.assertEqual(tracking_info["status"], "agent_assigned")
                self.assertEqual(tracking_info["delivery_type"], "home_delivery")
                self.assertIn("estimated_delivery_time", tracking_info)
                self.assertIn("minutes_left", tracking_info)
                self.assertEqual(tracking_info["delivery_agent"], "Test Agent")
    
    def test_track_order_takeaway(self):
        """Test tracking a takeaway order"""
        order_id = "456789012345678901234567"
        
        # Mock takeaway order
        mock_order = {
            "_id": ObjectId(order_id),
            "status": "placed",
            "delivery_type": "takeaway",
            "delivery_agent_id": None,
            "estimated_delivery_time": datetime.datetime.now() + datetime.timedelta(minutes=3)
        }
        
        with patch('app3.Order.get_by_id', return_value=mock_order):
            # Test track_order
            tracking_info = Order.track_order(order_id)
            
            
            self.assertEqual(tracking_info["order_id"], str(order_id))
            self.assertEqual(tracking_info["status"], "placed")
            self.assertEqual(tracking_info["delivery_type"], "takeaway")
            self.assertIn("estimated_delivery_time", tracking_info)
            self.assertIn("minutes_left", tracking_info)
            self.assertNotIn("delivery_agent", tracking_info)


class TestAdmin(unittest.TestCase):
    
    def setUp(self):
         
        self.db_patcher = patch('app3.Database')
        self.mock_db = self.db_patcher.start()
        
        
        self.mock_admins_collection = MagicMock()
        self.mock_agents_collection = MagicMock()
        self.mock_orders_collection = MagicMock()
        self.mock_restaurants_collection = MagicMock()
        
       
        self.mock_db_instance = self.mock_db.return_value
        self.mock_db_instance.get_collection.side_effect = lambda name: {
            'admins': self.mock_admins_collection,
            'delivery_agents': self.mock_agents_collection,
            'orders': self.mock_orders_collection,
            'restaurants': self.mock_restaurants_collection
        }.get(name, MagicMock())
        
        # Create object IDs for testing
        self.valid_agent_id = ObjectId()
        self.valid_restaurant_id = ObjectId()
        self.valid_order_id = ObjectId()
        
    def tearDown(self):
        self.db_patcher.stop()
    
    def test_authenticate_valid_admin(self):
        
        self.mock_admins_collection.find_one.return_value = {
            'username': 'admin',
            'password': 'admin123',
            'name': 'System Administrator'
        }
        
        
        result = Admin.authenticate('admin', 'admin123')
        
        
        self.mock_admins_collection.find_one.assert_called_once_with(
            {'username': 'admin', 'password': 'admin123'}
        )
        self.assertIsNotNone(result)
        self.assertEqual(result['username'], 'admin')
    
    def test_authenticate_invalid_admin(self):
        
        self.mock_admins_collection.find_one.return_value = None
        
        
        result = Admin.authenticate('wrong', 'wrong123')
        
        
        self.mock_admins_collection.find_one.assert_called_once_with(
            {'username': 'wrong', 'password': 'wrong123'}
        )
        self.assertIsNone(result)
    
    def test_add_delivery_agent_success(self):
        
        self.mock_agents_collection.insert_one.return_value = MagicMock(inserted_id=ObjectId())
        
        
        result = Admin.add_delivery_agent('John Doe', '1234567890', 'john@example.com')
        
        
        self.assertTrue(result)
        self.mock_agents_collection.insert_one.assert_called_once()
        
        call_args = self.mock_agents_collection.insert_one.call_args[0][0]
        self.assertEqual(call_args['name'], 'John Doe')
        self.assertEqual(call_args['phone'], '1234567890')
        self.assertEqual(call_args['email'], 'john@example.com')
        self.assertEqual(call_args['status'], 'available')
        self.assertEqual(call_args['delivered_orders'], [])
        self.assertIsNone(call_args['current_order'])
        self.assertIsInstance(call_args['created_at'], datetime.datetime)
    
    def test_add_delivery_agent_failure(self):
        
        self.mock_agents_collection.insert_one.side_effect = Exception("Database error")
        
        
        result = Admin.add_delivery_agent('John Doe', '1234567890', 'john@example.com')
        
        
        self.assertFalse(result)
    
    def test_add_restaurant_success(self):
        # Mock the Restaurant class
        with patch('app3.Restaurant') as mock_restaurant_class:
            mock_restaurant_instance = mock_restaurant_class.return_value
            mock_restaurant_instance.save.return_value = ObjectId()
            
            
            result = Admin.add_restaurant('Pizza Place', '123 Main St', 'Italian')
            
            
            self.assertTrue(result)
            mock_restaurant_class.assert_called_once_with('Pizza Place', '123 Main St', 'Italian')
            mock_restaurant_instance.save.assert_called_once()
    
    def test_add_restaurant_failure(self):
        # Mock the Restaurant class
        with patch('app3.Restaurant') as mock_restaurant_class:
            mock_restaurant_instance = mock_restaurant_class.return_value
            mock_restaurant_instance.save.return_value = None
            
            
            result = Admin.add_restaurant('Pizza Place', '123 Main St', 'Italian')
            
            
            self.assertFalse(result)
    
    def test_view_all_agents(self):
        
        expected_agents = [
            {'_id': ObjectId(), 'name': 'Agent 1'},
            {'_id': ObjectId(), 'name': 'Agent 2'}
        ]
        self.mock_agents_collection.find.return_value = expected_agents
        
        
        result = Admin.view_all_agents()
        
        
        self.assertEqual(result, expected_agents)
        self.mock_agents_collection.find.assert_called_once()
    
    def test_view_available_agents(self):
        
        expected_agents = [
            {'_id': ObjectId(), 'name': 'Agent 1', 'status': 'available'},
            {'_id': ObjectId(), 'name': 'Agent 2', 'status': 'available'}
        ]
        self.mock_agents_collection.find.return_value = expected_agents
        
        
        result = Admin.view_available_agents()
        
        
        self.assertEqual(result, expected_agents)
        self.mock_agents_collection.find.assert_called_once_with({'status': 'available'})
    
    def test_view_all_orders(self):
        
        expected_orders = [
            {'_id': ObjectId(), 'status': 'placed'},
            {'_id': ObjectId(), 'status': 'delivered'}
        ]
        self.mock_orders_collection.find.return_value.sort.return_value = expected_orders
        
        
        result = Admin.view_all_orders()
        
        
        self.assertEqual(result, expected_orders)
        self.mock_orders_collection.find.assert_called_once()
        self.mock_orders_collection.find.return_value.sort.assert_called_once_with('created_at', pymongo.DESCENDING)
    
    def test_view_restaurant_orders(self):
        
        restaurant_id = ObjectId()
        expected_orders = [
            {'_id': ObjectId(), 'restaurant_id': restaurant_id, 'status': 'placed'},
            {'_id': ObjectId(), 'restaurant_id': restaurant_id, 'status': 'delivered'}
        ]
        self.mock_orders_collection.find.return_value.sort.return_value = expected_orders
        
        
        result = Admin.view_restaurant_orders(restaurant_id)
        
        
        self.assertEqual(result, expected_orders)
        self.mock_orders_collection.find.assert_called_once_with({'restaurant_id': restaurant_id})
        self.mock_orders_collection.find.return_value.sort.assert_called_once_with('created_at', pymongo.DESCENDING)
    
    @patch('app3.Order')
    def test_assign_agents_to_pending_orders_no_available_agents(self, mock_order):
        
        self.mock_agents_collection.find.return_value = []
        
        
        Admin.assign_agents_to_pending_orders()
        
        
        self.mock_agents_collection.find.assert_called_once_with({'status': 'available'})
        mock_order._start_delivery_thread.assert_not_called()
    
    @patch('app3.Order')
    @patch('app3.DeliveryAgent')
    @patch('app3.app_lock')
    def test_assign_agents_to_pending_orders_with_agents_and_orders(self, mock_lock, mock_delivery_agent, mock_order):
        
        available_agent = {'_id': ObjectId(), 'name': 'Agent 1', 'status': 'available'}
        self.mock_agents_collection.find.return_value = [available_agent]
        
        pending_order_id = ObjectId()
        mock_order.pending_orders = [pending_order_id]
        mock_order.orders_lock = threading.Lock()
        
        with patch('datetime.datetime') as mock_datetime:
            mock_now = datetime.datetime(2025, 3, 10, 12, 0, 0)
            mock_datetime.now.return_value = mock_now
            estimated_time = mock_now + datetime.timedelta(minutes=2)
                        
            Admin.assign_agents_to_pending_orders()
            
            self.mock_agents_collection.find.assert_called_once_with({'status': 'available'})
            
            self.mock_orders_collection.update_one.assert_called_once_with(
                {'_id': pending_order_id},
                {'$set': {
                    'delivery_agent_id': available_agent['_id'],
                    'status': 'agent_assigned',
                    'estimated_delivery_time': estimated_time
                }}
            )
            
            mock_delivery_agent.update_status.assert_called_once_with(
                available_agent['_id'], 'busy', pending_order_id
            )
            
            mock_order._start_delivery_thread.assert_called_once_with(
                pending_order_id, available_agent['_id']
            )


class TestRestaurant(unittest.TestCase):
    
    def setUp(self):
        
        self.db_patcher = patch('app3.Database')
        self.mock_db = self.db_patcher.start()
        
        
        self.mock_restaurants_collection = MagicMock()
        self.mock_menu_items_collection = MagicMock()
        
       
        self.mock_db_instance = self.mock_db.return_value
        self.mock_db_instance.get_collection.side_effect = lambda name: {
            'restaurants': self.mock_restaurants_collection,
            'menu_items': self.mock_menu_items_collection
        }.get(name, MagicMock())
        
        
        self.restaurant_id = ObjectId()
        self.restaurant_data = {
            '_id': self.restaurant_id,
            'name': 'Test Restaurant',
            'address': '123 Test St',
            'cuisine_type': 'Test Cuisine'
        }
        
    def tearDown(self):
        self.db_patcher.stop()
    
    def test_restaurant_initialization(self):
        
        restaurant = Restaurant('Test Restaurant', '123 Test St', 'Test Cuisine')
        
        
        self.assertEqual(restaurant.name, 'Test Restaurant')
        self.assertEqual(restaurant.address, '123 Test St')
        self.assertEqual(restaurant.cuisine_type, 'Test Cuisine')
        self.assertIsNone(restaurant.restaurant_id)
    
    def test_restaurant_save(self):
        
        self.mock_restaurants_collection.insert_one.return_value = MagicMock(inserted_id=self.restaurant_id)
        
        
        restaurant = Restaurant('Test Restaurant', '123 Test St', 'Test Cuisine')
        result = restaurant.save()
        
        
        self.assertEqual(result, self.restaurant_id)
        self.assertEqual(restaurant.restaurant_id, self.restaurant_id)
        
         
        call_args = self.mock_restaurants_collection.insert_one.call_args[0][0]
        self.assertEqual(call_args['name'], 'Test Restaurant')
        self.assertEqual(call_args['address'], '123 Test St')
        self.assertEqual(call_args['cuisine_type'], 'Test Cuisine')
        self.assertIsInstance(call_args['created_at'], datetime.datetime)
    
    def test_get_all_restaurants(self):
        
        expected_restaurants = [
            {'_id': ObjectId(), 'name': 'Restaurant 1'},
            {'_id': ObjectId(), 'name': 'Restaurant 2'}
        ]
        self.mock_restaurants_collection.find.return_value = expected_restaurants
        
        
        result = Restaurant.get_all()
        
        
        self.assertEqual(result, expected_restaurants)
        self.mock_restaurants_collection.find.assert_called_once()
    
    def test_get_restaurant_by_id(self):
        
        self.mock_restaurants_collection.find_one.return_value = self.restaurant_data
        
        
        result = Restaurant.get_by_id(self.restaurant_id)
        
        
        self.assertEqual(result, self.restaurant_data)
        self.mock_restaurants_collection.find_one.assert_called_once_with({'_id': self.restaurant_id})
    
    def test_get_restaurant_by_id_not_found(self):
        
        self.mock_restaurants_collection.find_one.return_value = None
        
        
        result = Restaurant.get_by_id(ObjectId())
        
        
        self.assertIsNone(result)
    
    def test_add_menu_item(self):
        
        menu_item_id = ObjectId()
        self.mock_menu_items_collection.insert_one.return_value = MagicMock(inserted_id=menu_item_id)
        
        
        result = Restaurant.add_menu_item(
            self.restaurant_id,
            'Test Item',
            'A delicious test item',
            9.99,
            'Appetizer'
        )
        
        
        self.assertEqual(result, menu_item_id)
        
         
        call_args = self.mock_menu_items_collection.insert_one.call_args[0][0]
        self.assertEqual(call_args['restaurant_id'], self.restaurant_id)
        self.assertEqual(call_args['name'], 'Test Item')
        self.assertEqual(call_args['description'], 'A delicious test item')
        self.assertEqual(call_args['price'], 9.99)
        self.assertEqual(call_args['category'], 'Appetizer')
        self.assertIsInstance(call_args['created_at'], datetime.datetime)
    
    def test_get_menu(self):
        
        expected_menu_items = [
            {'_id': ObjectId(), 'name': 'Item 1', 'restaurant_id': self.restaurant_id},
            {'_id': ObjectId(), 'name': 'Item 2', 'restaurant_id': self.restaurant_id}
        ]
        self.mock_menu_items_collection.find.return_value = expected_menu_items
        
        
        result = Restaurant.get_menu(self.restaurant_id)
        
  
        self.assertEqual(result, expected_menu_items)
        self.mock_menu_items_collection.find.assert_called_once_with({'restaurant_id': self.restaurant_id})
    
    def test_get_menu_empty(self):
        self.mock_menu_items_collection.find.return_value = []
        
        result = Restaurant.get_menu(self.restaurant_id)

        self.assertEqual(result, [])


class TestDeliveryAgent(unittest.TestCase):
    
    def setUp(self):
        self.db_patcher = patch('app3.Database')
        self.mock_db = self.db_patcher.start()
        
        self.mock_agents_collection = MagicMock()
        
        self.mock_db_instance = self.mock_db.return_value
        self.mock_db_instance.get_collection.side_effect = lambda name: {
            'delivery_agents': self.mock_agents_collection
        }.get(name, MagicMock())
        
        self.agent_id = ObjectId()
        self.agent_data = {
            '_id': self.agent_id,
            'name': 'Test Agent',
            'phone': '1234567890',
            'email': 'test@example.com',
            'status': 'available',
            'delivered_orders': [],
            'current_order': None
        }
        
        self.order_id = ObjectId()
        
    def tearDown(self):
        self.db_patcher.stop()
    
    def test_get_agent_by_id(self):
        self.mock_agents_collection.find_one.return_value = self.agent_data
        
        result = DeliveryAgent.get_by_id(self.agent_id)
        
        self.assertEqual(result, self.agent_data)
        self.mock_agents_collection.find_one.assert_called_once_with({'_id': self.agent_id})
    
    def test_get_agent_by_id_not_found(self):
        self.mock_agents_collection.find_one.return_value = None
        
        result = DeliveryAgent.get_by_id(ObjectId())
        
        self.assertIsNone(result)
    
    def test_update_status_without_order(self):
        DeliveryAgent.update_status(self.agent_id, 'busy')
        
        self.mock_agents_collection.update_one.assert_called_once_with(
            {'_id': self.agent_id},
            {'$set': {'status': 'busy'}}
        )
    
    def test_update_status_with_order(self):
        DeliveryAgent.update_status(self.agent_id, 'busy', self.order_id)
        
        self.mock_agents_collection.update_one.assert_called_once_with(
            {'_id': self.agent_id},
            {'$set': {'status': 'busy', 'current_order': self.order_id}}
        )
    
    @patch('app3.Admin')
    def test_add_delivered_order(self, mock_admin):
        DeliveryAgent.add_delivered_order(self.agent_id, self.order_id)
        
        self.mock_agents_collection.update_one.assert_called_once_with(
            {'_id': self.agent_id},
            {
                '$push': {'delivered_orders': self.order_id},
                '$set': {'status': 'available', 'current_order': None}
            }
        )
        mock_admin.assign_agents_to_pending_orders.assert_called_once()
    
    @patch('app3.Admin')
    def test_add_delivered_order_invalid_agent(self, mock_admin):
        
        invalid_agent_id = ObjectId()
        
        
        DeliveryAgent.add_delivered_order(invalid_agent_id, self.order_id)
        
        # Although the agent might not exist, the method still tries to update and assign pending orders
        self.mock_agents_collection.update_one.assert_called_once()
        mock_admin.assign_agents_to_pending_orders.assert_called_once()


class TestEdgeCases(unittest.TestCase):
    
    def setUp(self):
        self.db_patcher = patch('app3.Database')
        self.mock_db = self.db_patcher.start()
        
        self.mock_admins_collection = MagicMock()
        self.mock_agents_collection = MagicMock()
        self.mock_orders_collection = MagicMock()
        self.mock_restaurants_collection = MagicMock()
        self.mock_menu_items_collection = MagicMock()
        
        self.mock_db_instance = self.mock_db.return_value
        self.mock_db_instance.get_collection.side_effect = lambda name: {
            'admins': self.mock_admins_collection,
            'delivery_agents': self.mock_agents_collection,
            'orders': self.mock_orders_collection,
            'restaurants': self.mock_restaurants_collection,
            'menu_items': self.mock_menu_items_collection
        }.get(name, MagicMock())
        
    def tearDown(self):
        self.db_patcher.stop()
    
    def test_admin_add_restaurant_with_empty_name(self):
        with patch('app3.Restaurant') as mock_restaurant_class:
            result = Admin.add_restaurant('', '123 Main St', 'Italian')
            
            mock_restaurant_class.assert_called_once_with('', '123 Main St', 'Italian')
    
    def test_admin_add_delivery_agent_with_invalid_email(self):
        self.mock_agents_collection.insert_one.return_value = MagicMock(inserted_id=ObjectId())
        
        result = Admin.add_delivery_agent('John Doe', '1234567890', 'not-an-email')
        
        self.assertTrue(result)
        
        call_args = self.mock_agents_collection.insert_one.call_args[0][0]
        self.assertEqual(call_args['email'], 'not-an-email')
    
    def test_restaurant_add_menu_item_with_negative_price(self):
        menu_item_id = ObjectId()
        self.mock_menu_items_collection.insert_one.return_value = MagicMock(inserted_id=menu_item_id)
        
        result = Restaurant.add_menu_item(
            ObjectId(),
            'Negative Item',
            'An item with negative price',
            -9.99,
            'Special'
        )
        
        self.assertEqual(result, menu_item_id)
        
        call_args = self.mock_menu_items_collection.insert_one.call_args[0][0]
        self.assertEqual(call_args['price'], -9.99)
    
    @patch('app3.Admin')
    def test_delivery_agent_add_delivered_order_with_none_order_id(self, mock_admin):
        agent_id = ObjectId()
        
        DeliveryAgent.add_delivered_order(agent_id, None)
        
        self.mock_agents_collection.update_one.assert_called_once_with(
            {'_id': agent_id},
            {
                '$push': {'delivered_orders': None},
                '$set': {'status': 'available', 'current_order': None}
            }
        )
    
    def test_restaurant_get_menu_with_invalid_id_string(self):
        invalid_id = "not-an-object-id"
        
        with self.assertRaises(Exception):
            Restaurant.get_menu(invalid_id)
    
    
    def test_validate_restaurant_without_required_fields(self):
        incomplete_restaurant = Restaurant("", "", "")
        self.mock_restaurants_collection.insert_one.return_value = MagicMock(inserted_id=ObjectId())
        
        result = incomplete_restaurant.save()        
        self.assertIsNotNone(result)
        self.mock_restaurants_collection.insert_one.assert_called_once()
    
    @patch('app3.Order')
    def test_concurrent_assign_agents_to_pending_orders(self, mock_order):        
        available_agent = {'_id': ObjectId(), 'name': 'Agent 1', 'status': 'available'}
        self.mock_agents_collection.find.return_value = [available_agent]
        
        pending_order_id = ObjectId()
        mock_order.pending_orders = [pending_order_id]
        mock_order.orders_lock = threading.Lock()
        
        def side_effect(*args, **kwargs):
            self.mock_agents_collection.find.return_value = []
            return MagicMock()
            
        self.mock_orders_collection.update_one.side_effect = side_effect
        
        thread = threading.Thread(target=Admin.assign_agents_to_pending_orders)
        thread.start()
        thread.join()
        
        Admin.assign_agents_to_pending_orders()        
        self.assertEqual(self.mock_orders_collection.update_one.call_count, 1)
    
if __name__ == '__main__':
    unittest.main()