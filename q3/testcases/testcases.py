import pytest
import sys
import os
import uuid
import datetime
import pymongo
from unittest.mock import patch, MagicMock
from bson.objectid import ObjectId

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from app import User, IndividualCustomer, RetailStore, Product, ProductCatalog, CartItem, ShoppingCart, Order, Coupon

@pytest.fixture
def mock_db():
    with patch('pymongo.MongoClient') as mock_client:
        mock_db = MagicMock()
        mock_client.return_value.__getitem__.return_value = mock_db
        
        users_mock = MagicMock()
        products_mock = MagicMock()
        orders_mock = MagicMock()
        coupons_mock = MagicMock()
        
        mock_db.__getitem__.side_effect = lambda x: {
            'users': users_mock,
            'products': products_mock,
            'orders': orders_mock,
            'coupons': coupons_mock
        }[x]
        
        return {
            'users': users_mock,
            'products': products_mock,
            'orders': orders_mock,
            'coupons': coupons_mock
        }

@pytest.fixture(autouse=True)
def patch_db_vars(monkeypatch, mock_db):
    monkeypatch.setattr("app.users_collection", mock_db["users"])
    monkeypatch.setattr("app.products_collection", mock_db["products"])
    monkeypatch.setattr("app.orders_collection", mock_db["orders"])
    monkeypatch.setattr("app.coupons_collection", mock_db["coupons"])

class TestUser:
    def test_user_init(self):
        user = User(name="Test User", email="test@example.com", phone="1234567890", 
                   address="123 Test St", password="password123")
        
        assert user.name == "Test User"
        assert user.email == "test@example.com"
        assert user.phone == "1234567890"
        assert user.address == "123 Test St"
        assert user.password == "password123"
        assert len(user.user_id) > 0
    
    def test_user_register_success(self, mock_db):
        mock_db['users'].find_one.return_value = None  
        mock_db['users'].insert_one.return_value = MagicMock()
        
        user = User(name="Test User", email="test@example.com", phone="1234567890", 
                   address="123 Test St", password="password123")
        result = user.register()
        
        assert result is True
        mock_db['users'].find_one.assert_called_once()
        mock_db['users'].insert_one.assert_called_once()
    
    def test_user_register_existing_email(self, mock_db):
        mock_db['users'].find_one.return_value = {"email": "test@example.com"}
        
        user = User(name="Test User", email="test@example.com", phone="1234567890", 
                   address="123 Test St", password="password123")
        result = user.register()
        
        assert result is False
        mock_db['users'].find_one.assert_called_once()
        mock_db['users'].insert_one.assert_not_called()
    
    def test_user_login_success(self, mock_db):
        user_data = {
            "user_id": "test-uuid",
            "name": "Test User",
            "email": "test@example.com",
            "password": "password123",
            "phone": "1234567890",
            "address": "123 Test St"
        }
        mock_db['users'].find_one.return_value = user_data
        
        result = User.login("test@example.com", "password123")
        
        assert result is None  # Regular login should return None because it doesn't match user_type
        mock_db['users'].find_one.assert_called_once()
    
    def test_user_login_individual_customer(self, mock_db):
        user_data = {
            "user_id": "test-uuid",
            "name": "Test Customer",
            "email": "customer@example.com",
            "password": "password123",
            "phone": "1234567890",
            "address": "123 Test St",
            "user_type": "individual",
            "loyalty_pts": 50,
            "purchase_history": [],
            "available_coupons": [],
            "cart_items": []
        }
        mock_db['users'].find_one.return_value = user_data
        
        # Mock the from_db method
        with patch.object(IndividualCustomer, 'from_db', return_value=MagicMock(spec=IndividualCustomer)) as mock_from_db:
            result = User.login("customer@example.com", "password123")
            
            assert result is not None
            mock_db['users'].find_one.assert_called_once()
            mock_from_db.assert_called_once_with(user_data)
    
    def test_user_login_retail_store(self, mock_db):
        user_data = {
            "user_id": "test-uuid",
            "name": "Test Store",
            "email": "store@example.com",
            "password": "password123",
            "phone": "1234567890",
            "address": "123 Test St",
            "user_type": "retail",
            "store_name": "Test Store",
            "bulk_discount_rate": 0.1,
            "purchase_history": [],
            "cart_items": []
        }
        mock_db['users'].find_one.return_value = user_data
        
        with patch.object(RetailStore, 'from_db', return_value=MagicMock(spec=RetailStore)) as mock_from_db:
            result = User.login("store@example.com", "password123")
            
            assert result is not None
            mock_db['users'].find_one.assert_called_once()
            mock_from_db.assert_called_once_with(user_data)
    
    def test_user_login_invalid_credentials(self, mock_db):
        mock_db['users'].find_one.return_value = None  
        
        result = User.login("invalid@example.com", "wrongpassword")
        
        assert result is None
        mock_db['users'].find_one.assert_called_once()

# Individual Customer Tests
class TestIndividualCustomer:
    def test_individual_customer_init(self):
        customer = IndividualCustomer(name="Test Customer", email="customer@example.com", 
                                     phone="1234567890", address="123 Test St", 
                                     password="password123")
        
        assert customer.name == "Test Customer"
        assert customer.email == "customer@example.com"
        assert customer.phone == "1234567890"
        assert customer.address == "123 Test St"
        assert customer.password == "password123"
        assert customer.loyalty_pts == 0
        assert customer.purchase_history == []
        assert customer.available_coupons == []
    
    def test_individual_customer_register_success(self, mock_db):
        mock_db['users'].find_one.return_value = None
        mock_db['users'].insert_one.return_value = MagicMock()
        
        customer = IndividualCustomer(name="Test Customer", email="customer@example.com", 
                                     phone="1234567890", address="123 Test St", 
                                     password="password123")
        result = customer.register()
        
        assert result is True
        mock_db['users'].find_one.assert_called_once()
        mock_db['users'].insert_one.assert_called_once()
    
    def test_individual_customer_from_db(self):
        user_data = {
            "user_id": "test-uuid",
            "name": "Test Customer",
            "email": "customer@example.com",
            "phone": "1234567890",
            "address": "123 Test St",
            "password": "password123",
            "user_type": "individual",
            "loyalty_pts": 50,
            "purchase_history": ["order1", "order2"],
            "available_coupons": ["coupon1"],
            "cart_items": [{"product_id": "product1", "quantity": 2}]
        }
        
        
        customer = IndividualCustomer.from_db(user_data)
        
        assert customer.user_id == "test-uuid"
        assert customer.name == "Test Customer"
        assert customer.email == "customer@example.com"
        assert customer.phone == "1234567890"
        assert customer.address == "123 Test St"
        assert customer.password == "password123"
        assert customer.loyalty_pts == 50
        assert customer.purchase_history == ["order1", "order2"]
        assert customer.available_coupons == ["coupon1"]
        assert customer.cart_items == [{"product_id": "product1", "quantity": 2}]

# Retail Store Tests
class TestRetailStore:
    def test_retail_store_init(self):
        store = RetailStore(name="Store Owner", email="store@example.com", 
                           phone="1234567890", address="123 Store St", 
                           password="password123", store_name="Test Store")
        
        assert store.name == "Store Owner"
        assert store.email == "store@example.com"
        assert store.phone == "1234567890"
        assert store.address == "123 Store St"
        assert store.password == "password123"
        assert store.store_name == "Test Store"
        assert store.bulk_discount_rate == 0.1
        assert store.purchase_history == []
    
    def test_retail_store_register_success(self, mock_db):
        mock_db['users'].find_one.return_value = None  
        mock_db['users'].insert_one.return_value = MagicMock()
        
        store = RetailStore(name="Store Owner", email="store@example.com", 
                           phone="1234567890", address="123 Store St", 
                           password="password123", store_name="Test Store")
        result = store.register()
        
        assert result is True
        mock_db['users'].find_one.assert_called_once()
        mock_db['users'].insert_one.assert_called_once()
    
    def test_retail_store_from_db(self):
        
        user_data = {
            "user_id": "test-uuid",
            "name": "Store Owner",
            "email": "store@example.com",
            "phone": "1234567890",
            "address": "123 Store St",
            "password": "password123",
            "user_type": "retail",
            "store_name": "Test Store",
            "bulk_discount_rate": 0.15,
            "purchase_history": ["order1"],
            "cart_items": [{"product_id": "product1", "quantity": 10}]
        }
        
        store = RetailStore.from_db(user_data)
        
        assert store.user_id == "test-uuid"
        assert store.name == "Store Owner"
        assert store.email == "store@example.com"
        assert store.phone == "1234567890"
        assert store.address == "123 Store St"
        assert store.password == "password123"
        assert store.store_name == "Test Store"
        assert store.bulk_discount_rate == 0.15
        assert store.purchase_history == ["order1"]
        assert store.cart_items == [{"product_id": "product1", "quantity": 10}]

# Product Tests
class TestProduct:
    def test_product_init(self):
        product = Product(name="Test Product", description="Test Description", 
                         price=99.99, category="Test Category", 
                         subcategory="Test Subcategory", stock_quantity=100)
        
        assert product.name == "Test Product"
        assert product.description == "Test Description"
        assert product.price == 99.99
        assert product.category == "Test Category"
        assert product.subcategory == "Test Subcategory"
        assert product.stock_quantity == 100
        assert len(product.product_id) > 0  
    
    def test_product_save_to_db_success(self, mock_db):
        
        mock_db['products'].insert_one.return_value = MagicMock()
        
        product = Product(name="Test Product", description="Test Description", 
                         price=99.99, category="Test Category", 
                         subcategory="Test Subcategory", stock_quantity=100)
        result = product.save_to_db()
        
        assert result is True
        mock_db['products'].insert_one.assert_called_once()
    
    def test_product_get_details(self):
        
        product = Product(name="Test Product", description="Test Description", 
                         price=99.99, category="Test Category", 
                         subcategory="Test Subcategory", stock_quantity=100)
        product.product_id = "test-product-id"
        
        details = product.get_details()
        
        assert details == {
            "product_id": "test-product-id",
            "name": "Test Product",
            "description": "Test Description",
            "price": 99.99,
            "category": "Test Category",
            "subcategory": "Test Subcategory",
            "stock_quantity": 100
        }
    
    def test_product_update_stock_increase(self, mock_db):
        product = Product(name="Test Product", description="Test Description", 
                         price=99.99, category="Test Category", 
                         subcategory="Test Subcategory", stock_quantity=100)
        product.product_id = "test-product-id"
        mock_db['products'].update_one.return_value = MagicMock()
        
        result = product.update_stock(50) 
        
        assert result is True
        assert product.stock_quantity == 150
        mock_db['products'].update_one.assert_called_once()
    
    def test_product_update_stock_decrease_valid(self, mock_db):
        
        product = Product(name="Test Product", description="Test Description", 
                         price=99.99, category="Test Category", 
                         subcategory="Test Subcategory", stock_quantity=100)
        product.product_id = "test-product-id"
        mock_db['products'].update_one.return_value = MagicMock()
        
        result = product.update_stock(-30) 
        
        assert result is True
        assert product.stock_quantity == 70
        mock_db['products'].update_one.assert_called_once()
    
    def test_product_update_stock_decrease_invalid(self, mock_db):
        product = Product(name="Test Product", description="Test Description", 
                         price=99.99, category="Test Category", 
                         subcategory="Test Subcategory", stock_quantity=100)
        product.product_id = "test-product-id"
        
        result = product.update_stock(-150)  #more than available
        
        assert result is False
        assert product.stock_quantity == 100  #remains unchanged
        mock_db['products'].update_one.assert_not_called()
    
    def test_product_from_db(self):
        product_data = {
            "product_id": "test-product-id",
            "name": "Test Product",
            "description": "Test Description",
            "price": 99.99,
            "category": "Test Category",
            "subcategory": "Test Subcategory",
            "stock_quantity": 100
        }
        
        product = Product.from_db(product_data)
        
        assert product.product_id == "test-product-id"
        assert product.name == "Test Product"
        assert product.description == "Test Description"
        assert product.price == 99.99
        assert product.category == "Test Category"
        assert product.subcategory == "Test Subcategory"
        assert product.stock_quantity == 100

# Product Catalog Tests
class TestProductCatalog:
    def test_search_by_name_found(self, mock_db):
        product_data = [
            {
                "product_id": "test-product-1",
                "name": "Test Product 1",
                "description": "Description 1",
                "price": 99.99,
                "category": "Category 1",
                "subcategory": "Subcategory 1",
                "stock_quantity": 100
            },
            {
                "product_id": "test-product-2",
                "name": "Test Product 2",
                "description": "Description 2",
                "price": 199.99,
                "category": "Category 2",
                "subcategory": "Subcategory 2",
                "stock_quantity": 200
            }
        ]
        mock_db['products'].find.return_value = product_data
        
        results = ProductCatalog.search_by_name("Test Product")
        
        assert len(results) == 2
        assert all(isinstance(p, Product) for p in results)
        assert results[0].product_id == "test-product-1"
        assert results[1].product_id == "test-product-2"
    
    def test_search_by_name_not_found(self, mock_db):
        mock_db['products'].find.return_value = []        
        results = ProductCatalog.search_by_name("Nonexistent Product")
        assert results == []
    
    def test_search_by_category_found(self, mock_db):
        product_data = [
            {
                "product_id": "test-product-1",
                "name": "Test Product 1",
                "description": "Description 1",
                "price": 99.99,
                "category": "Electronics",
                "subcategory": "Phones",
                "stock_quantity": 100
            }
        ]
        mock_db['products'].find.return_value = product_data
        
        results = ProductCatalog.search_by_category("Electronics")
                
        assert len(results) == 1
        assert isinstance(results[0], Product)
        assert results[0].product_id == "test-product-1"
        assert results[0].category == "Electronics"
    
    def test_search_by_subcategory(self, mock_db):
        product_data = [
            {
                "product_id": "test-product-1",
                "name": "Test Product 1",
                "description": "Description 1",
                "price": 99.99,
                "category": "Electronics",
                "subcategory": "Phones",
                "stock_quantity": 100
            }
        ]
        mock_db['products'].find.return_value = product_data
        
        results = ProductCatalog.search_by_category("Phones")
        
        assert len(results) == 1
        assert isinstance(results[0], Product)
        assert results[0].product_id == "test-product-1"
        assert results[0].subcategory == "Phones"
    
    def test_get_all_products(self, mock_db):
        product_data = [
            {
                "product_id": "test-product-1",
                "name": "Test Product 1",
                "description": "Description 1",
                "price": 99.99,
                "category": "Category 1",
                "subcategory": "Subcategory 1",
                "stock_quantity": 100
            },
            {
                "product_id": "test-product-2",
                "name": "Test Product 2",
                "description": "Description 2",
                "price": 199.99,
                "category": "Category 2",
                "subcategory": "Subcategory 2",
                "stock_quantity": 200
            }
        ]
        mock_db['products'].find.return_value = product_data
        
        results = ProductCatalog.get_all_products()
        
        assert len(results) == 2
        assert all(isinstance(p, Product) for p in results)
        assert results[0].product_id == "test-product-1"
        assert results[1].product_id == "test-product-2"
    
    def test_get_all_products_empty(self, mock_db):
        mock_db['products'].find.return_value = []
        results = ProductCatalog.get_all_products()        
        assert results == []

# Cart Item Tests
class TestCartItem:
    def test_cart_item_init(self):
        product = Product(name="Test Product", price=99.99, stock_quantity=100)
        product.product_id = "test-product-id"        
        cart_item = CartItem(product, quantity=2)
        
        assert cart_item.product == product
        assert cart_item.quantity == 2
    
    def test_get_subtotal(self):
        product = Product(name="Test Product", price=99.99, stock_quantity=100)
        cart_item = CartItem(product, quantity=2)
        subtotal = cart_item.get_subtotal()        
        assert subtotal == 99.99 * 2
    
    def test_to_dict(self):
        product = Product(name="Test Product", price=99.99, stock_quantity=100)
        product.product_id = "test-product-id"
        cart_item = CartItem(product, quantity=2)

        result = cart_item.to_dict()

        assert result == {
            "product_id": "test-product-id",
            "quantity": 2,
            "price_at_purchase": 99.99
        }

# Shopping Cart Tests
class TestShoppingCart:
    def test_shopping_cart_init_empty(self, mock_db):
        user = MagicMock()
        user.user_id = "test-user-id"
        mock_db['users'].find_one.return_value = {
            "user_id": "test-user-id",
            "cart_items": []
        }
        
        cart = ShoppingCart(user)
        
        assert cart.user == user
        assert cart.items == []
    
    def test_shopping_cart_init_with_items(self, mock_db):
        user = MagicMock()
        user.user_id = "test-user-id"
        
        product_data = {
            "product_id": "test-product-id",
            "name": "Test Product",
            "description": "Test Description",
            "price": 99.99,
            "category": "Test Category",
            "subcategory": "Test Subcategory",
            "stock_quantity": 100
        }
        
        mock_db['users'].find_one.return_value = {
            "user_id": "test-user-id",
            "cart_items": [
                {"product_id": "test-product-id", "quantity": 2}
            ]
        }
        
        mock_db['products'].find_one.return_value = product_data
        
        with patch.object(Product, 'from_db', return_value=Product(name="Test Product", price=99.99)) as mock_from_db:
            cart = ShoppingCart(user)
            
            assert cart.user == user
            assert len(cart.items) == 1
            assert cart.items[0].quantity == 2
            mock_from_db.assert_called_once_with(product_data)
    
    def test_add_item_new(self, mock_db):
        user = MagicMock()
        user.user_id = "test-user-id"
        mock_db['users'].find_one.return_value = {"user_id": "test-user-id", "cart_items": []}
        mock_db['users'].update_one.return_value = MagicMock()
        
        product = Product(name="Test Product", price=99.99, stock_quantity=100)
        product.product_id = "test-product-id"
        
        cart = ShoppingCart(user)
        
        result = cart.add_item(product, quantity=2)
        
        assert result is True
        assert len(cart.items) == 1
        assert cart.items[0].product == product
        assert cart.items[0].quantity == 2
        mock_db['users'].update_one.assert_called_once()
    
    def test_add_item_existing(self, mock_db):
        user = MagicMock()
        user.user_id = "test-user-id"
        
        product = Product(name="Test Product", price=99.99, stock_quantity=100)
        product.product_id = "test-product-id"
        
        cart = ShoppingCart(user)
        cart.items = [CartItem(product, quantity=2)]
        
        mock_db['users'].update_one.return_value = MagicMock()
        
        result = cart.add_item(product, quantity=3)        
        
        assert result is True
        assert len(cart.items) == 1

        assert cart.items[0].quantity == 5  
        mock_db['users'].update_one.assert_called_once()
    
    def test_add_item_exceeds_stock(self, mock_db):
        user = MagicMock()
        user.user_id = "test-user-id"
        
        product = Product(name="Test Product", price=99.99, stock_quantity=10)
        product.product_id = "test-product-id"
                
        cart = ShoppingCart(user)
        result = cart.add_item(product, quantity=15)  #more than stock
        
        assert result is False
        assert len(cart.items) == 0
        mock_db['users'].update_one.assert_not_called()
    
    def test_add_item_existing_exceeds_stock(self, mock_db):
        user = MagicMock()
        user.user_id = "test-user-id"
        
        product = Product(name="Test Product", price=99.99, stock_quantity=10)
        product.product_id = "test-product-id"
        
        cart = ShoppingCart(user)
        cart.items = [CartItem(product, quantity=8)]
        
        result = cart.add_item(product, quantity=5)  
        
        assert result is False
        assert len(cart.items) == 1
        assert cart.items[0].quantity == 8 
        mock_db['users'].update_one.assert_not_called()
    
    def test_remove_item_existing(self, mock_db):
        user = MagicMock()
        user.user_id = "test-user-id"
        
        product = Product(name="Test Product", price=99.99, stock_quantity=100)
        product.product_id = "test-product-id"
        
        cart = ShoppingCart(user)
        cart.items = [CartItem(product, quantity=2)]
        
        mock_db['users'].update_one.return_value = MagicMock()
        
        result = cart.remove_item("test-product-id")


        assert result is True
        assert len(cart.items) == 0
        mock_db['users'].update_one.assert_called_once()
    
    def test_remove_item_not_found(self, mock_db):
        user = MagicMock()
        user.user_id = "test-user-id"
        
        product = Product(name="Test Product", price=99.99, stock_quantity=100)
        product.product_id = "test-product-id"
        
        cart = ShoppingCart(user)
        cart.items = [CartItem(product, quantity=2)]
        
        result = cart.remove_item("nonexistent-id")
        
        assert result is False
        assert len(cart.items) == 1
        mock_db['users'].update_one.assert_called_once()
    
    def test_update_quantity_valid(self, mock_db):
        user = MagicMock()
        user.user_id = "test-user-id"
        
        product = Product(name="Test Product", price=99.99, stock_quantity=100)
        product.product_id = "test-product-id"
        
        cart = ShoppingCart(user)
        cart.items = [CartItem(product, quantity=2)]
        
        mock_db['products'].find_one.return_value = {"product_id": "test-product-id", "stock_quantity": 100}
        mock_db['users'].update_one.return_value = MagicMock()
        
        result = cart.update_quantity("test-product-id", 5)
                
        assert result is True
        assert cart.items[0].quantity == 5
        mock_db['users'].update_one.assert_called_once()

    def test_update_quantity_insufficient_stock(self, mock_db):
        user = MagicMock()
        user.user_id = "test-user-id"
        
        product = Product(name="Test Product", price=99.99, stock_quantity=100)
        product.product_id = "test-product-id"
        
        cart = ShoppingCart(user)
        cart.items = [CartItem(product, quantity=2)]
        
        mock_db['products'].find_one.return_value = {
            "product_id": "test-product-id",
            "stock_quantity": 3
        }
        
        result = cart.update_quantity("test-product-id", 5)
        
        assert result is False
        assert cart.items[0].quantity == 2
        mock_db['users'].update_one.assert_not_called()

    def test_update_quantity_item_not_found(self, mock_db):
        user = MagicMock()
        user.user_id = "test-user-id"
        
        cart = ShoppingCart(user)
        cart.items = []
        
        result = cart.update_quantity("nonexistent_id", 5)
        
        assert result is False
        mock_db['users'].update_one.assert_not_called()

    def test_calculate_total_empty(self, mock_db):
        user = MagicMock()
        user.user_id = "test-user-id"
        
        cart = ShoppingCart(user)
        cart.items = []
        
        total = cart.calculate_total()
        
        assert total == 0.0

    def test_calculate_total_multiple_items(self, mock_db):
        user = MagicMock()
        user.user_id = "test-user-id"
        
        product1 = MagicMock()
        product1.price = 10.0
        product1.product_id = "prod1"
        
        product2 = MagicMock()
        product2.price = 15.0
        product2.product_id = "prod2"
        
        cart = ShoppingCart(user)
        cart.items = [
            CartItem(product1, 2),
            CartItem(product2, 3)
        ]
        
        total = cart.calculate_total()
        
        assert total == 65.0

    def test_clear(self, mock_db):
        user = MagicMock()
        user.user_id = "test-user-id"
        
        product = MagicMock()
        cart = ShoppingCart(user)
        cart.items = [CartItem(product, 2)]
        
        cart.clear()
        
        assert len(cart.items) == 0
        mock_db['users'].update_one.assert_called_once_with(
            {"user_id": "test-user-id"},
            {"$set": {"cart_items": []}}
        )

class TestOrder:
    def test_init(self):
        order = Order()
        assert order.user is None
        assert len(order.items) == 0
        assert order.status == "placed"
        assert isinstance(order.order_date, datetime.datetime)
        assert isinstance(order.estimated_delivery_time, datetime.datetime)
        assert order.total_amount == 0.0
        assert order.final_amount == 0.0
        assert order.discount_applied == 0.0
        assert order.coupon_used is None
    
    def test_calculate_final_price_no_discount(self, mock_db):
        user = MagicMock()
        user.user_id = "test-user-id"
        user.bulk_discount_rate = 0
        
        product1 = MagicMock()
        product1.price = 10.0
        
        product2 = MagicMock()
        product2.price = 15.0
        
        order = Order()
        order.user = user
        order.items = [
            CartItem(product1, 2),
            CartItem(product2, 3)
        ]
        
        final_price = order.calculate_final_price()
        
        assert order.total_amount == 65.0
        assert final_price == 65.0
        assert order.discount_applied == 0.0
    
    def test_calculate_final_price_with_coupon(self, mock_db):
        user = MagicMock()
        user.user_id = "test-user-id"
        user.bulk_discount_rate = 0
        
        product1 = MagicMock()
        product1.price = 10.0
        
        product2 = MagicMock()
        product2.price = 15.0
        
        order = Order()
        order.user = user
        order.items = [
            CartItem(product1, 2),
            CartItem(product2, 3)
        ]
        
        coupon = {
            'coupon_id': 'test_coupon_id',
            'discount_percentage': 10
        }
        
        final_price = order.calculate_final_price(coupon)
        
        assert order.total_amount == 65.0
        assert order.discount_applied == 6.5
        assert final_price == 58.5
        assert order.coupon_used == 'test_coupon_id'
    
    def test_calculate_final_price_with_bulk_discount(self, mock_db):
        user = MagicMock()
        user.user_id = "test-user-id"
        user.user_type = "retail"
        user.bulk_discount_rate = 10
        
        product1 = MagicMock()
        product1.price = 100.0
        
        order = Order()
        order.user = user
        order.items = [CartItem(product1, 5)]
        
        final_price = order.calculate_final_price()
        
        assert order.total_amount == 500.0
        assert order.discount_applied == 50.0
        assert final_price == 450.0
    
    def test_place_order_successful(self, mock_db):
        user = MagicMock(spec=IndividualCustomer)
        user.user_id = "test-user-id"
        
        product1 = MagicMock()
        product1.product_id = "prod1"
        product1.stock_quantity = 10
        
        product2 = MagicMock()
        product2.product_id = "prod2"
        product2.stock_quantity = 15
        
        order = Order()
        order.user = user
        order.items = [
            CartItem(product1, 3),
            CartItem(product2, 5)
        ]
        order.order_id = "test_order_id"
        order.final_amount = 100.0
        
        mock_db['products'].find_one.side_effect = [
            {"product_id": "prod1", "stock_quantity": 10},
            {"product_id": "prod2", "stock_quantity": 15}
        ]
        
        with patch.object(Coupon, 'add_loyalty_points') as mock_add_loyalty:
            result = order.place_order()
            
            assert result is True
            assert mock_db['products'].update_one.call_count == 2
            assert mock_db['orders'].insert_one.call_count == 1
            assert mock_db['users'].update_one.call_count == 1
            
            assert mock_db['users'].update_one.call_args[0][1]["$push"]["purchase_history"] == "test_order_id"
            
            mock_add_loyalty.assert_called_once_with(user, 10)
    
    def test_place_order_insufficient_stock(self, mock_db):
        user = MagicMock()
        user.user_id = "test-user-id"
        
        product = MagicMock()
        product.product_id = "prod1"
        product.name = "Low Stock Product"
        
        order = Order()
        order.user = user
        order.items = [CartItem(product, 10)]
        
        mock_db['products'].find_one.return_value = {
            "product_id": "prod1",
            "stock_quantity": 5
        }
        
        result = order.place_order()
        
        assert result is False
        mock_db['products'].update_one.assert_not_called()
        mock_db['orders'].insert_one.assert_not_called()
        mock_db['users'].update_one.assert_not_called()
    
    def test_cancel_order_successful(self, mock_db):
        product1 = MagicMock()
        product1.product_id = "prod1"
        product1.stock_quantity = 7
        
        product2 = MagicMock()
        product2.product_id = "prod2"
        product2.stock_quantity = 10
        
        order = Order()
        order.order_id = "test_order_id"
        order.items = [
            CartItem(product1, 3),
            CartItem(product2, 5)
        ]
        
        mock_db['orders'].find_one.return_value = {
            "order_id": "test_order_id",
            "status": "placed",
            "items": [
                {"product_id": "prod1", "quantity": 3},
                {"product_id": "prod2", "quantity": 5}
            ]
        }
        
        result = order.cancel_order()
        
        assert result is True
        assert mock_db['orders'].update_one.call_count == 1
        assert mock_db['products'].update_one.call_count == 2
        
        assert order.status == "cancelled"
        
        assert product1.stock_quantity == 10
        assert product2.stock_quantity == 15
    
    def test_cancel_order_already_delivered(self, mock_db):
        order = Order()
        order.order_id = "test_order_id"
        
        mock_db['orders'].find_one.return_value = {
            "order_id": "test_order_id",
            "status": "delivered"
        }
        
        result = order.cancel_order()
        
        assert result is False
        mock_db['orders'].update_one.assert_not_called()
        mock_db['products'].update_one.assert_not_called()
    
    def test_get_order_details(self, mock_db):
        order = Order()
        order.order_id = "test_order_id"
        
        order_date = datetime.datetime.now()
        mock_db['orders'].find_one.return_value = {
            "order_id": "test_order_id",
            "order_date": order_date,
            "items": [
                {"product_id": "prod1", "quantity": 2, "price_at_purchase": 10.0},
                {"product_id": "prod2", "quantity": 3, "price_at_purchase": 15.0}
            ],
            "total_amount": 65.0,
            "discount_applied": 6.5,
            "final_amount": 58.5,
            "status": "placed",
            "estimated_delivery_time": order_date + datetime.timedelta(minutes=20)
        }
        
        mock_db['products'].find_one.side_effect = [
            {"product_id": "prod1", "name": "Product 1"},
            {"product_id": "prod2", "name": "Product 2"}
        ]
        
        details = order.get_order_details()
        
        assert details is not None
        assert details["order_id"] == "test_order_id"
        assert details["order_date"] == order_date
        assert len(details["items"]) == 2
        assert details["items"][0]["product"] == "Product 1"
        assert details["items"][0]["quantity"] == 2
        assert details["items"][1]["product"] == "Product 2"
        assert details["items"][1]["quantity"] == 3
        assert details["total_amount"] == 65.0
        assert details["discount_applied"] == 6.5
        assert details["final_amount"] == 58.5
        assert details["status"] == "placed"
        
    def test_track_order_placed(self, mock_db):
        order = Order()
        order.order_id = "test_order_id"
        
        future_time = datetime.datetime.now() + datetime.timedelta(minutes=10)
        order.estimated_delivery_time = future_time
        
        mock_db['orders'].find_one.return_value = {
            "order_id": "test_order_id",
            "status": "placed",
            "estimated_delivery_time": future_time
        }
        
        status = order.track_order()
        
        assert status == "placed"
        assert order.status == "placed"
        mock_db['orders'].update_one.assert_not_called()
    
    def test_track_order_should_be_delivered(self, mock_db):
        order = Order()
        order.order_id = "test_order_id"
        
        past_time = datetime.datetime.now() - datetime.timedelta(minutes=5)
        order.estimated_delivery_time = past_time
        
        mock_db['orders'].find_one.return_value = {
            "order_id": "test_order_id",
            "status": "placed",
            "estimated_delivery_time": past_time
        }
        
        with patch.object(Order, 'update_status') as mock_update:
            status = order.track_order()
            
            mock_update.assert_called_once_with("delivered")
    
    def test_track_order_cancelled(self, mock_db):
        order = Order()
        order.order_id = "test_order_id"
        
        mock_db['orders'].find_one.return_value = {
            "order_id": "test_order_id",
            "status": "cancelled"
        }
        
        status = order.track_order()
        
        assert status == "cancelled"
        assert order.status == "cancelled"
    
    def test_update_status_valid(self, mock_db):
        order = Order()
        order.order_id = "test_order_id"
        order.status = "placed"
        
        result = order.update_status("delivered")
        
        assert result is True
        assert order.status == "delivered"
        mock_db['orders'].update_one.assert_called_once_with(
            {"order_id": "test_order_id"},
            {"$set": {"status": "delivered"}}
        )
    
    def test_update_status_invalid(self, mock_db):
        order = Order()
        order.order_id = "test_order_id"
        order.status = "placed"
        
        result = order.update_status("shipped")
        
        assert result is False
        assert order.status == "placed"
        mock_db['orders'].update_one.assert_not_called()
    
class TestCoupon:
    def test_generate_coupon_success(self, mock_db):
        mock_user = MagicMock()
        mock_user.user_id = "test_user_id"
        mock_user.loyalty_pts = 200
        
        mock_db['users'].find_one.return_value = {
            'user_id': mock_user.user_id,
            'loyalty_pts': 200
        }
        
        result = Coupon.generate_coupon_for_user(mock_user)
        
        assert result is True
        mock_db['coupons'].insert_one.assert_called_once()
        mock_db['users'].update_one.assert_called_once()
        assert mock_user.loyalty_pts == 100

    def test_generate_coupon_insufficient_points(self, mock_db):
        mock_user = MagicMock()
        mock_user.user_id = "test_user_id"
        mock_user.loyalty_pts = 50
        
        mock_db['users'].find_one.return_value = {
            'user_id': mock_user.user_id,
            'loyalty_pts': 50
        }
        
        result = Coupon.generate_coupon_for_user(mock_user)
        
        assert result is False
        mock_db['coupons'].insert_one.assert_not_called()
        mock_db['users'].update_one.assert_not_called()

    def test_view_coupons_no_coupons(self, mock_db):
        mock_user = MagicMock()
        mock_user.user_id = "test_user_id"
        
        mock_db['users'].find_one.return_value = {
            'user_id': mock_user.user_id,
            'available_coupons': []
        }
        
        coupons = Coupon.view_available_coupons(mock_user)
        
        assert coupons == []
        mock_db['coupons'].find.assert_not_called()

    def test_view_coupons_has_valid_coupons(self, mock_db):
        mock_user = MagicMock()
        mock_user.user_id = "test_user_id"
        
        coupon_ids = [str(uuid.uuid4()) for _ in range(2)]
        mock_db['users'].find_one.return_value = {
            'user_id': mock_user.user_id,
            'available_coupons': coupon_ids
        }
        
        valid_coupons = [
            {
                'coupon_id': coupon_ids[0],
                'code': 'TEST1',
                'discount_percentage': 10,
                'is_active': True,
                'valid_until': (datetime.datetime.now() + datetime.timedelta(days=10)).isoformat()
            },
            {
                'coupon_id': coupon_ids[1],
                'code': 'TEST2',
                'discount_percentage': 15,
                'is_active': True,
                'valid_until': (datetime.datetime.now() + datetime.timedelta(days=5)).isoformat()
            }
        ]
        
        mock_db['coupons'].find.return_value = valid_coupons
        
        coupons = Coupon.view_available_coupons(mock_user)
        
        assert coupons == valid_coupons
        mock_db['coupons'].find.assert_called_once()

    def test_view_coupons_expired(self, mock_db):
        mock_user = MagicMock()
        mock_user.user_id = "test_user_id"
        
        coupon_ids = [str(uuid.uuid4()) for _ in range(2)]
        mock_db['users'].find_one.return_value = {
            'user_id': mock_user.user_id,
            'available_coupons': coupon_ids
        }
        
        mock_db['coupons'].find.return_value = []
        
        coupons = Coupon.view_available_coupons(mock_user)
        assert coupons == []

    def test_apply_valid_coupon(self, mock_db):
        mock_user = MagicMock()
        mock_user.user_id = "test_user_id"
        
        coupon_id = str(uuid.uuid4())
        coupon = {
            'coupon_id': coupon_id,
            'code': 'VALID10',
            'discount_percentage': 10,
            'is_active': True,
            'valid_until': (datetime.datetime.now() + datetime.timedelta(days=10)).isoformat()
        }
        
        mock_db['coupons'].find_one.return_value = coupon
        mock_db['users'].find_one.return_value = {
            'user_id': mock_user.user_id,
            'available_coupons': [coupon_id]
        }
        
        result = Coupon.apply_coupon(mock_user, 'VALID10')
        
        assert result == coupon
        mock_db['users'].update_one.assert_called_once()
        mock_db['coupons'].update_one.assert_called_once()

    def test_apply_invalid_coupon_code(self, mock_db):
        mock_user = MagicMock()
        mock_user.user_id = "test_user_id"
        
        mock_db['coupons'].find_one.return_value = None
        
        result = Coupon.apply_coupon(mock_user, 'INVALID')
        
        assert result is None
        mock_db['users'].update_one.assert_not_called()
        mock_db['coupons'].update_one.assert_not_called()

    def test_apply_coupon_not_assigned_to_user(self, mock_db):
        mock_user = MagicMock()
        mock_user.user_id = "test_user_id"

        coupon_id = str(uuid.uuid4())
        coupon = {
            'coupon_id': coupon_id,
            'code': 'NOTMINE',
            'discount_percentage': 10,
            'is_active': True,
            'valid_until': (datetime.datetime.now() + datetime.timedelta(days=10)).isoformat()
        }
        
        mock_db['coupons'].find_one.return_value = coupon
        mock_db['users'].find_one.return_value = {
            'user_id': mock_user.user_id,
            'available_coupons': [] 
        }
        
        result = Coupon.apply_coupon(mock_user, 'NOTMINE')
        
        assert result is None
        mock_db['users'].update_one.assert_not_called()
        mock_db['coupons'].update_one.assert_not_called()

    def test_add_loyalty_points_success(self, mock_db):
        mock_user = MagicMock()
        mock_user.user_id = "test_user_id"
        mock_user.loyalty_pts = 100
        
        initial_points = mock_user.loyalty_pts
        points_to_add = 50
        
        result = Coupon.add_loyalty_points(mock_user, points_to_add)
        
        assert result is True
        assert mock_user.loyalty_pts == initial_points + points_to_add
        mock_db['users'].update_one.assert_called_once_with(
            {"user_id": mock_user.user_id},
            {"$inc": {"loyalty_pts": points_to_add}}
        )

if __name__ == '__main__':
    pytest.main()
