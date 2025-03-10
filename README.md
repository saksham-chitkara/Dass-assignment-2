# ASSIGNMENT - 2

## Q1

### 1. Software Specifications
The Online Food Delivery System is designed to support both Home Delivery and Takeaway orders. It is built from a business perspective and utilizes MongoDB as its primary persistent storage for all system data (users, orders, restaurants, menu items, and delivery agents). Key features include:
- **Order Types:** Supports Home Delivery and Takeaway.
- **Delivery Fleet Management:** Manages a fleet of delivery agents for home delivery orders.
- **Order Tracking:** Customers can view real-time status and the estimated time remaining for their order.
- **Multiple Orders:** Supports placing and processing multiple orders concurrently.
- **Manager Dashboard:** Provides a comprehensive view of restaurant performance, including order statistics and revenue.
- **Persistent Data Storage:** Uses MongoDB to maintain a consistent and shared state across multiple sessions and instances.
- **User and Admin Authentication:** Secure login and registration for both customers and administrators.
- **Restaurant & Menu Management:** Admins can add and manage restaurants and their menus via a command-line interface (CLI).


### 2. Use Cases

### Use Case Number: UC-01
**Use Case Name:** Place an Order  

**Overview:**  
Allows a customer to place an order by selecting a restaurant, choosing menu items, and specifying the order type (Home Delivery or Takeaway).  

**Actors:**  
- Customer  
- System  
- Restaurant  

**Pre condition:**  
- The customer is logged in and has navigated to the restaurant menu screen.  

**Flow:**  
**Main (Success) Flow:**  
1. The customer selects a restaurant from the list.  
2. The system displays the selected restaurant’s menu (fetched from MongoDB).  
3. The customer selects one or more items and adds them to the cart.  
4. The customer chooses the order type (Home Delivery or Takeaway).  
5. The customer confirms the order.  
6. The system processes the order:  
   - For Home Delivery, it assigns an available delivery agent (or places the order in a pending state if none are available) and sets an estimated delivery time.  
   - For Takeaway, it sets an estimated pickup time.  
7. The order is recorded in the database with a unique Order ID.

**Alternate Flows:**  
- **Invalid Order Details:**  
  - The system prompts the customer to correct missing or invalid details.  
- **No Delivery Agent Available:**  
  - The system places the order in a pending state and notifies the customer that an agent will be assigned once available.  

**Post Condition:**  
- The order is successfully saved in the system with an appropriate status, and the customer receives an Order ID and estimated time information.

---

### Use Case Number: UC-02
**Use Case Name:** Track an Order  

**Overview:**  
Enables a customer to view the current status and estimated time remaining for their order (delivery or pickup).  

**Actors:**  
- Customer  
- System  

**Pre condition:**  
- The customer has placed an order and received an Order ID. 

**Flow:**  
**Main (Success) Flow:**  
1. The customer selects the "Track Order" option and enters the Order ID.  
2. The system retrieves the order details from MongoDB.  
3. The system computes the time remaining using the estimated delivery/pickup time.  
4. The system displays the order status, estimated time, and (if applicable) the assigned delivery agent’s details.

**Alternate Flows:**  
- **Order Not Found:**  
  - The system displays an error message and prompts for re-entry of the Order ID.  

- **Pending Agent Assignment (Home Delivery):**  
  - The system indicates that a delivery agent has not yet been assigned and displays "Not available" for time and agent details.

**Post Condition:**  
- The customer is presented with up-to-date tracking information regarding the order’s status and remaining time.

---

### Use Case Number: UC-03
**Use Case Name:** Manage Delivery Agents  

**Overview:**  
Allows a manager to manage the delivery fleet by viewing existing agents, adding new agents, and monitoring their status.  

**Actors:**  
- Manager  
- System  

**Pre condition:**  
- The manager is logged into the system.  

**Flow:**  
**Main (Success) Flow:**  
1. The manager selects the "Manage Delivery Agents" option from the admin menu.  
2. The system displays a list of all delivery agents (retrieved from MongoDB) with details such as name, contact, and current status.  
3. The manager opts to add a new delivery agent by entering the required information.  
4. The system validates the input and adds the new agent to the database.  
5. The updated list of delivery agents is displayed.  

**Alternate Flows:**  
- **Invalid Agent Details:**  
  - The system prompts the manager to re-enter correct details. 

**Post Condition:**  
- The new delivery agent is added, and the system’s delivery agent list is updated.

---

### Use Case Number: UC-04
**Use Case Name:** View Restaurant Dashboard

**Overview:**  
Provides a dashboard view for managers to monitor restaurant performance, including total orders, pending orders, completed orders, and total revenue. 

**Actors:**  
- Manager  
- System  
- Restaurant  

**Pre condition:**  
- The manager is logged into the system.  
- Restaurant order data exists in MongoDB.  

**Flow:**  
**Main (Success) Flow:**  
1. The manager selects the "Restaurant Dashboard" option.  
2. The system displays a list of restaurants.  
3. The manager selects a restaurant.  
4. The system retrieves and displays key metrics: total orders, pending orders, completed orders, and revenue.  
5. The system also displays a list of recent orders for further insight.  

**Alternate Flows:**  
- **No Order Data:**  
  - The system notifies the manager that no orders exist for the selected restaurant.  

**Post Condition:**  
- The manager is provided with a comprehensive dashboard for the selected restaurant.

---

### Use Case Number: UC-05
**Use Case Name:** Persistent System Instance  
**Overview:**  
Ensures that the system’s state (orders, users, agents, restaurants) is maintained across multiple sessions and instances using MongoDB. 

**Actors:**  
- System Administrator  
- System  

**Pre condition:**  
- The system is installed and connected to a MongoDB database.  

**Flow:**  
**Main (Success) Flow:**  
1. Multiple instances of the application are launched.  
2. Each instance connects to the shared MongoDB database to load current data.  
3. All instances display consistent, up-to-date data reflecting orders, users, restaurants, and agents.  

**Alternate Flows:**  
- **Database Connection Failure:**  
  - The system displays an error message and notifies the administrator of a degraded mode until the issue is resolved.

**Post Condition:**  
- The system state is synchronized across all sessions, ensuring data consistency and continuity.

---

### Use Case Number: UC-06
**Use Case Name:** User Registration and Login  

**Overview:**  
Enables new users to register and existing users to log in to the system.  

**Actors:**  
- Customer  
- System  

**Pre condition:**  
- The user has access to the application’s registration and login interface.  

**Flow:**  
**Main (Success) Flow:**  
1. A new user selects "User Registration" and enters details (name, email, password, phone, address).  
2. The system validates the input and registers the user in MongoDB.  
3. The user is informed of successful registration.  
4. The user then logs in using their email and password.  
5. The system authenticates the user and grants access to the customer interface.  

**Alternate Flows:**  
- **Duplicate Registration:**  
  - If the email or phone number is already registered, the system displays an error and prompts the user to try again.  
- **Authentication Failure:**  
  - If incorrect credentials are provided during login, the system displays an error message. 

**Post Condition:**  
- The user is successfully registered and/or logged in, and the user’s data is stored in MongoDB.

---

### Use Case Number: UC-07
**Use Case Name:** Manage Menu Items  
**Overview:**  
Allows a restaurant manager (via the admin interface) to add, update, or remove menu items for a restaurant. 

**Actors:**  
- Manager  
- System  
- Restaurant  

**Pre condition:**  
- The manager is logged in and has selected a specific restaurant to manage.  

**Flow:**  
**Main (Success) Flow:**  
1. The manager selects the "Manage Menu Items" option for a restaurant.  
2. The system displays the current menu items (from MongoDB).  
3. The manager chooses to add a new menu item by entering details such as name, description, price, and category.  
4. The system validates the input and saves the new menu item to the database.  
5. The system displays the updated menu.  

**Alternate Flows:**  
- **Invalid Menu Data:**  
  - If incorrect data is entered, the system prompts for corrections.  

**Post Condition:**  
- The restaurant’s menu is updated in MongoDB with the new item.

---

### Use Case Number: UC-08
**Use Case Name:** View Order Details  
**Overview:**  
Allows a customer or admin to view detailed information about a specific order, including items ordered, price breakdown, and delivery details.  

**Actors:**  
- Customer, Admin  
- System  
- Restaurant  
- Delivery Agent (for Home Delivery)  

**Pre condition:**  
- The order has been placed and stored in the system.  

**Flow:**  
**Main (Success) Flow:**  
1. The user selects an order from a list of orders.  
2. The system retrieves the order details from MongoDB.  
3. The system displays order information such as restaurant name, customer name, order items, price, order date, and order status.  
4. For Home Delivery orders, if an agent is assigned, the agent’s details and estimated delivery time are also displayed.  

**Alternate Flows:**  
- **Order Not Found:**  
  - If the order ID is invalid, the system informs the user that the order does not exist.  

**Post Condition:**  
- Detailed order information is displayed, enabling the user to review the order’s content and status.

---

# Test Case Documentation

## Overview
This document provides an overview of the test cases written for the system. Each class and its corresponding test cases are explained briefly.

---

## **Classes and Their Purpose**

### **1. Database**
- **Purpose:**  
  The `Database` class is a singleton that manages the connection to MongoDB and ensures a single instance of the database is used throughout the application.

### **2. User**
- **Purpose:**  
  The `User` class handles user-related operations, such as registration, authentication, and retrieval of user details.

### **3. Order**
- **Purpose:**  
  The `Order` class manages order placement, tracking, delivery agent assignment, and order status updates.

### **4. Admin**
- **Purpose:**  
  The `Admin` class provides administrative functionalities such as managing delivery agents, viewing orders, and assigning pending orders to available agents.

### **5. DeliveryAgent**
- **Purpose:**  
  The `DeliveryAgent` class manages delivery agent information, status updates, and tracking of completed deliveries.

### **6. Restaurant**
- **Purpose:**  
  The `Restaurant` class handles operations related to restaurants, including adding new restaurants, managing menu items, and retrieving restaurant details.

---

## **Test Cases**

### **1. Database Test Cases**

#### `test_singleton_pattern`
- **Description:**  
  Ensures that the `Database` class follows the singleton pattern (i.e., multiple instances reference the same object).

#### `test_get_collection`
- **Description:**  
  Verifies that the correct MongoDB collection is retrieved when requested.

#### `test_admin_creation`
- **Description:**  
  Checks if an admin account is created in the database when none exists.

---

### **2. User Test Cases**

#### `test_user_save_success`
- **Description:**  
  Tests successful registration of a user and verifies that a unique ID is assigned.

#### `test_user_save_duplicate`
- **Description:**  
  Ensures that the registration fails if a duplicate email or phone number is used.

#### `test_authenticate_success`
- **Description:**  
  Checks if a user can log in successfully with correct credentials.

#### `test_authenticate_fail`
- **Description:**  
  Verifies that authentication fails when incorrect credentials are provided.

#### `test_get_by_id`
- **Description:**  
  Verifies that a user can be correctly retrieved by their ID.

#### `test_get_by_id_not_found`
- **Description:**  
  Ensures that retrieving a non-existent user by ID returns None.

---

### **3. Order Test Cases**

#### `test_order_save_pickup`
- **Description:**  
  Ensures that takeaway orders are saved successfully with an estimated pickup time.

#### `test_order_save_delivery_with_agent`
- **Description:**  
  Tests that a home delivery order is correctly saved and a delivery agent is assigned when available.

#### `test_order_save_delivery_no_agent`
- **Description:**  
  Ensures that if no delivery agent is available, the order is added to a pending orders list.

#### `test_delivery_process`
- **Description:**  
  Simulates the delivery process by waiting (sleep) and then updating the order status to “delivered”.

#### `test_assign_pending_order_with_pending`
- **Description:**  
  Checks that a pending order is assigned to an available agent when one becomes free.

#### `test_assign_pending_order_no_pending`
- **Description:**  
  Ensures that no assignment occurs if there are no pending orders.

#### `test_update_status_delivered`
- **Description:**  
  Verifies that the order status is updated to “delivered” and that the delivery agent’s record is updated accordingly.

#### `test_mark_order_picked_up`
- **Description:**  
  Tests marking a takeaway order as “picked up.”

#### `test_mark_order_picked_up_fail_delivery`
- **Description:**  
  Ensures that attempting to mark a home delivery order as “picked up” fails.

#### `test_track_order_not_found`
- **Description:**  
  Checks that tracking a non-existent order returns an appropriate message.

#### `test_track_order_home_delivery`
- **Description:**  
  Verifies that tracking details for a home delivery order include status, estimated delivery time, minutes left, and the assigned delivery agent.

#### `test_track_order_takeaway`
- **Description:**  
  Ensures that takeaway orders provide proper tracking information without a delivery agent.

---

### **4. Admin Test Cases**

#### `test_authenticate_success`
- **Description:**  
  Checks if an admin can log in successfully with valid credentials.

#### `test_authenticate_fail`
- **Description:**  
  Verifies that admin authentication fails for invalid credentials.

#### `test_add_delivery_agent_success`
- **Description:**  
  Tests successful addition of a new delivery agent.

#### `test_add_delivery_agent_failure`
- **Description:**  
  Ensures that adding a delivery agent fails when there is a database error.

#### `test_add_restaurant`
- **Description:**  
  Checks if a restaurant is successfully added via the Admin’s add_restaurant function.

#### `test_view_all_agents`
- **Description:**  
  Verifies that the system can retrieve all delivery agents from the database.

#### `test_view_available_agents`
- **Description:**  
  Ensures that only available delivery agents are retrieved.

#### `test_view_all_orders`
- **Description:**  
  Checks if all orders are correctly retrieved and sorted by creation time.

#### `test_view_restaurant_orders`
- **Description:**  
  Verifies that orders for a specific restaurant are correctly retrieved.

#### `test_assign_agents_to_pending_orders_no_available_agents`
- **Description:**  
  Ensures that no orders are assigned when there are no available agents.

#### `test_assign_agents_to_pending_orders_with_pending_orders`
- **Description:**  
  Tests that pending orders are assigned to available agents when possible.

---

### **5. DeliveryAgent Test Cases**

#### `test_get_by_id`
- **Description:**  
  Checks that a delivery agent can be retrieved by their ID.

#### `test_update_status`
- **Description:**  
  Verifies that a delivery agent’s status is updated correctly, with and without an active order.

#### `test_add_delivered_order`
- **Description:**  
  Ensures that when an order is delivered, it is added to the agent’s delivered orders list and the agent’s status is reset to available.

---

### **6. Restaurant Test Cases**

#### `test_restaurant_initialization`
- **Description:**  
  Verifies proper initialization of a restaurant instance with the given parameters.

#### `test_restaurant_save`
- **Description:**  
  Checks that a restaurant is saved successfully and a unique ID is assigned.

#### `test_get_all_restaurants`
- **Description:**  
  Ensures that all restaurants are retrieved from the database.

#### `test_get_restaurant_by_id`
- **Description:**  
  Verifies that a restaurant can be retrieved by its ID.

#### `test_get_restaurant_by_id_not_found`
- **Description:**  
  Checks that attempting to retrieve a non-existent restaurant returns None.

#### `test_add_menu_item`
- **Description:**  
  Tests the addition of a new menu item to a restaurant.

#### `test_get_menu`
- **Description:**  
  Ensures that a restaurant's menu items are retrieved correctly.

#### `test_get_menu_empty`
- **Description:**  
  Verifies that an empty menu is handled correctly.

---



## Q2
# Gobblet Jr. - Pygame Implementation

## Overview
This project implements the **Gobblet Jr.** board game using Python and Pygame. The game adheres to the official rules and allows two players to compete on a 3x3 board using reserve pieces and on-board moves.

## Classes and Their Functions

### Piece Class
- **Purpose:** Represents an individual game piece with a specific size, color, and ownership.
- **Key Function:**
  - `draw(surface, x, y)`: Draws the piece as a circle on the given surface at coordinates (x, y), and updates its rectangle for collision detection.

### Cell Class
- **Purpose:** Represents a cell on the game board that can hold a stack of pieces.
- **Key Functions:**
  - `push(piece)`: Attempts to add a piece to the cell’s stack following the game rules (a piece can only be placed if it is larger than the top piece).
  - `pop()`: Removes and returns the top piece from the cell’s stack.
  - `top()`: Retrieves the top piece in the cell’s stack without removing it.
  - `is_empty()`: Used to check if the stack corresponding to the cell is empty or not

### GobbletGame Class
- **Purpose:** Manages the overall game logic, including board setup, player turns, move validation, rendering, and win detection.
- **Key Functions:**
  - `setup_players()`: Initializes the two players and assigns each their reserve pieces.
  - `draw_board()`: Renders the game board and any pieces that have been placed.
  - `draw_reserve_pieces()`: Draws the reserve pieces for both players on the screen.
  - `get_board_cell(self, pos)`: Return the board cell (row, col) for a give position.
  - `draw_curr_player(self)`: Displays the current player's turn.
  - `draw_game_over(self)`: Displays a game over overlay when the game ends.
  - `draw(self)`: Draws the complete game state.
  - `handle_click(pos)`: Processes mouse clicks to select and move pieces, either from the board or reserve.
  - `check_winner(last_move)`: Checks for a winning condition based on the current board state.
  - `restart()`: Resets the game state for a new match.
  - `run()`: Contains the main game loop that handles events, updates the display, and maintains the game flow.

## Assumptions
- **Feature Exclusions:** The **rewind**, **replay**, and **auto play** options are not implemented. These features are not part of the official rules as provided in the documentation or video resources and are only present in some online versions of the game.

## Running the Game
1. **Install Dependencies:**  
   Ensure that Python and Pygame are installed.  
   ```bash
   pip install pygame
2. To start the game:
    ```bash
    python gobblet.py
## Q3

- As requirements were no concrete, I am assuming that we have to not implement delivery agents for the system.

### System Design
Database Choice: `MongoDB`

MongoDB was chosen for this project for several reasons:

- Document-oriented structure: Ideal for e-commerce data with varying attributes
- Scalability: Can easily handle growing product catalogs and user bases
- Flexibility: Schema-less design allows for easy modifications
- Performance: Fast queries for product searches and filtering

### Class Architecture
The application uses an object-oriented approach with the following key classes:
#### User Classes

- User: Base class for authentication and common user properties
- IndividualCustomer: Extends User with loyalty points and coupon features
- RetailStore: Extends User with bulk discount capabilities

#### Product Classes

- Product: Stores product details and manages inventory
- ProductCatalog: Handles product searching and browsing operations

#### Shopping Classes

- CartItem: Represents individual items in a cart with quantity
- ShoppingCart: Manages the user's collection of items
- Order: Handles order creation, payment processing, and tracking
- Coupon: Manages discount coupon generation and application

#### Interface Class

- DollmartCLI: Command-line interface for user interaction

#### Installation Prerequisites

- Python 3.7 or higher
- MongoDB (local installation or MongoDB Atlas account)
- PyMongo package


#### To Load sample products in the DB:

```bash
python script.py
```


### Database Collections

- users: Stores user profiles, cart data, and purchase history
- products: Contains product details and inventory information
- orders: Tracks all order information and status
- coupons: Manages discount coupon data

## TestCases: 

## User Class 
1. `test_user_init`: Verifies proper initialization of User class with correct property assignment.
2. `test_user_register_success`: Tests successful user registration when email is not already in use.
3. `test_user_register_existing_email`: Ensures users can't register with an email that already exists.
4. `test_user_login_success`: Validates the general user login functionality.
5. `test_user_login_individual_customer`: Tests login functionality specifically for individual customer account type.
6. `test_user_login_retail_store`: Tests login functionality specifically for retail store account type.
7. `test_user_login_invalid_credentials`: Ensures login fails when incorrect credentials are provided.

## IndividualCustomer Class 
1. `test_individual_customer_init`: Verifies proper initialization of IndividualCustomer class with default values.
2. `test_individual_customer_register_success`: Tests successful customer registration in the database.
3. `test_individual_customer_from_db`: Validates correct object creation from database records.

## RetailStore Class 
1. `test_retail_store_init`: Verifies proper initialization of RetailStore class with store-specific fields.
2. `test_retail_store_register_success`: Tests successful registration of retail stores in the database.
3. `test_retail_store_from_db`: Validates correct store object creation from database records.

## Product Class
1. `test_product_init`: Verifies proper initialization of Product class with correct attributes.
2. `test_product_save_to_db_success`: Tests successful saving of product details to the database.
3. `test_product_get_details`: Ensures product details are correctly formatted for display or API.
4. `test_product_update_stock_increase`: Tests increasing product inventory with positive stock values.
5. `test_product_update_stock_decrease_valid`: Tests valid inventory reduction when stock is available.
6. `test_product_update_stock_decrease_invalid`: Ensures inventory can't be reduced below zero.
7. `test_product_from_db`: Validates correct product object creation from database records.

## ProductCatalog Class 
1. `test_search_by_name_found`: Tests finding products by name functionality.
2. `test_search_by_name_not_found`: Validates empty results are returned for non-existent products.
3. `test_search_by_category_found`: Tests finding products by their category.
4. `test_search_by_subcategory`: Tests filtering products by their subcategory.
5. `test_get_all_products`: Ensures all products can be retrieved from the catalog.
6. `test_get_all_products_empty`: Tests handling of empty catalog scenario.

## CartItem Class 
1. `test_cart_item_init`: Verifies proper initialization of CartItem with product and quantity.
2. `test_get_subtotal`: Tests price calculation for items in the cart.
3. `test_to_dict`: Ensures cart items can be properly serialized for database storage.


## ShoppingCart Class

1. `test_shopping_cart_init_empty`: Verifies that a shopping cart initializes empty when user has no items.
2. `test_shopping_cart_init_with_items`: Confirms shopping cart loads with existing items from user's database record.
3. `test_add_item_new`: Tests adding a new item to an empty cart.
4. `test_add_item_existing`: Validates adding more quantity of an existing item in cart.
5. `test_add_item_exceeds_stock`: Ensures items exceeding available stock cannot be added.
6. `test_add_item_existing_exceeds_stock`: Verifies adding more of an existing item fails if it would exceed stock.
7. `test_remove_item_existing`: Confirms successful removal of an item from cart.
8. `test_remove_item_not_found`: Tests behavior when attempting to remove a non-existent item.
9. `test_update_quantity_valid`: Validates updating an item quantity within stock limits.
10. `test_update_quantity_insufficient_stock`: Ensures quantity updates fail if they exceed available stock.
11. `test_update_quantity_item_not_found`: Checks behavior when updating quantity for non-existent item.
12. `test_calculate_total_empty`: Confirms total calculation returns zero for empty cart.
13. `test_calculate_total_multiple_items`: Verifies correct total calculation with multiple items.
14. `test_clear`: Tests complete clearing of all items from cart.

## Order Class 

1. `test_init`: Verifies correct initialization of a new Order with default values.
2. `test_calculate_final_price_no_discount`: Tests calculation of final price without any discounts.
3. `test_calculate_final_price_with_coupon`: Confirms correct price calculation with coupon discount.
4. `test_calculate_final_price_with_bulk_discount`: Validates final price calculation with bulk discount for retail customers.
5. `test_place_order_successful`: Tests successful order placement with sufficient stock.
6. `test_place_order_insufficient_stock`: Verifies order fails when product stock is insufficient.
7. `test_cancel_order_successful`: Confirms successful order cancellation and stock restoration.
8. `test_cancel_order_already_delivered`: Tests that delivered orders cannot be cancelled.
9. `test_get_order_details`: Verifies retrieval of complete order details.
10. `test_track_order_placed`: Tests order tracking for orders in "placed" status.
11. `test_track_order_should_be_delivered`: Confirms order status updates when delivery time has passed.
12. `test_track_order_cancelled`: Tests tracking of cancelled orders.
13. `test_update_status_valid`: Validates successful order status updates.
14. `test_update_status_invalid`: Ensures invalid status changes are rejected.

## Coupon Class 

1. `test_generate_coupon_success`: Tests successful coupon generation for users with sufficient loyalty points.
2. `test_generate_coupon_insufficient_points`: Verifies coupon generation fails for users with insufficient points.
3. `test_view_coupons_no_coupons`: Confirms empty list returned when user has no coupons.
4. `test_view_coupons_has_valid_coupons`: Tests retrieval of all valid coupons for a user.
5. `test_view_coupons_expired`: Verifies handling of expired coupons.
6. `test_apply_valid_coupon`: Tests successful application of a valid coupon.
7. `test_apply_invalid_coupon_code`: Confirms invalid coupon codes are rejected.
8. `test_apply_coupon_not_assigned_to_user`: Ensures coupons not assigned to the user cannot be applied.
9. `test_add_loyalty_points_success`: Tests successful addition of loyalty points to user account.

## Running the Tests

To run these tests, use pytest with the following command:

```bash
pytest test.py