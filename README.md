# ASSIGNMENT - 2

## Q1

# Software Requirements Specification (SRS) 
## 1. Introduction

### 1.1 Purpose
This SRS document defines the requirements for the Online Food Delivery System. It outlines the system’s functional and non-functional requirements, software specifications, and detailed use cases. The system is intended to serve both end customers and administrators by facilitating online ordering (Home Delivery and Takeaway), order tracking, and restaurant as well as delivery agent management.

### 1.2 Scope
The system enables customers to register, log in, place orders, and track their orders in real time. Administrators can manage delivery agents, add new restaurants and menu items, and view aggregated order data through a dashboard. The system uses MongoDB for persistent storage and is implemented in Python as a command-line interface (CLI) application.

### 1.3 Definitions, Acronyms, and Abbreviations
- **Home Delivery:** Orders delivered to the customer by a delivery agent.
- **Takeaway:** Orders prepared for customer pickup at the restaurant.
- **Delivery Agent:** Personnel responsible for delivering orders.
- **MongoDB:** NoSQL database used for persistent storage.
- **CLI:** Command-Line Interface.
- **SRS:** Software Requirements Specification.


### 1.4 Overview of Document
This document is organized into the following sections: Introduction, Overall Description, Software Specifications, Specific Requirements (including detailed use cases), and Appendices (Glossary and Index).

---

## 2. Overall Description

### 2.1 Product Perspective
The Online Food Delivery System is a stand-alone CLI application that interacts with a MongoDB database to persist data. It supports end-to-end online food ordering from registration to order tracking and administrative management.

### 2.2 Product Functions
- **User Management:** Registration, login, and profile management.
- **Order Management:** Placing orders, tracking order status, and managing order details.
- **Delivery Management:** Automatic assignment of available delivery agents to Home Delivery orders; queuing of orders when no agents are available.
- **Restaurant & Menu Management:** Adding and managing restaurant details and menu items.
- **Administration & Dashboard:** Viewing aggregated restaurant data (orders, revenue, etc.) and managing delivery agents.
- **Persistent Data Storage:** Uses MongoDB to store all system data consistently.

### 2.3 User Classes and Characteristics
- **Customers:** End users who place orders and track their status.
- **Delivery Agents:** Staff responsible for delivering home orders.
- **Administrators/Managers:** Users with elevated privileges to manage the system (agents, restaurants, orders).

### 2.4 Operating Environment
- **Software:** Python 3.x, MongoDB (hosted on MongoDB Atlas), and a command-line interface.
- **Hardware:** Standard desktop or laptop with internet connectivity.

### 2.5 Design and Implementation Constraints
- Must be implemented in Python.
- Uses MongoDB for persistent storage.
- Operates via a command-line interface.
- Security practices (e.g., password hashing) should be implemented in a production environment.

### 2.6 Assumptions and Dependencies
- A stable internet connection is available to connect to MongoDB Atlas.
- The system uses a dedicated pool of delivery agents for Home Delivery orders.
- Data integrity is maintained through MongoDB.
- The system’s user interface is CLI-based.

---

## 3. Software Specifications

### 3.1 Technology Stack
- **Programming Language:** Python 3.x
- **Database:** MongoDB (using MongoDB Atlas for cloud storage)
- **Concurrency:** Python threading for simulating asynchronous delivery processes
- **Interface:** Command-Line Interface (CLI)

### 3.2 Architecture
- **Modular Design:** The system is divided into distinct modules: Database connection, User Management, Order Processing, Delivery Agent Management, Restaurant & Menu Management, and Admin functionalities.
- **Singleton Pattern:** The Database module uses a singleton pattern to ensure a single MongoDB connection.
- **Persistent Storage:** All data is stored in MongoDB, ensuring a persistent and shared state across multiple sessions.
- **Concurrency Management:** Order deliveries are handled using Python threads, which simulate the passage of time and update order statuses asynchronously.

### 3.3 Design Constraints
- The system must maintain a responsive CLI.
- Real-time order tracking is simulated using thread sleep and status updates.
- The system should be easily extendable for future integration with graphical interfaces or additional features.

---

## 4. Specific Requirements

### 4.1 Functional Requirements
- **FR1:** Customers can register and log in.
- **FR2:** Customers can place orders (Home Delivery and Takeaway) with an estimated time for delivery or pickup.
- **FR3:** The system automatically assigns available delivery agents to Home Delivery orders; orders are queued if no agent is available.
- **FR4:** Customers can track order status and view estimated times.
- **FR5:** Administrators can manage delivery agents and view all orders.
- **FR6:** Administrators can add new restaurants and manage menu items.
- **FR7:** All data is stored in MongoDB to maintain persistent state.

### 4.2 Non-functional Requirements
- **Performance:** Order tracking and agent assignment must be updated in near real time.
- **Reliability:** The system must maintain data consistency and operate continuously.
- **Security:** User credentials must be handled securely (with proper hashing in production).
- **Usability:** The CLI should be intuitive and provide clear instructions.
- **Scalability:** The system should support growing numbers of orders, users, and delivery agents.
- **Maintainability:** Code must be modular and well-documented.

### 4.3 External Interface Requirements
- **User Interface:** Command-line interface with clear menus and prompts.
- **Software Interfaces:** Integration with MongoDB using Python’s pymongo driver.
- **Communication Interfaces:** Internet connectivity to interact with MongoDB Atlas.

---

## 5. System Features (Use Cases)

### Use Case Number: UC-01
**Use Case Name:** Place an Order  
**Overview:**  
Allows a customer to place an order by selecting a restaurant, choosing menu items, and specifying the order type (Home Delivery or Takeaway).  
**Actors:**  
- Customer, System, Restaurant  

**Pre condition:**  
- The customer is logged in and has viewed the restaurant’s menu. 

**Flow:**  
1. The customer selects a restaurant from the list.  
2. The system displays the menu (from MongoDB).  
3. The customer selects items and adds them to the cart.  
4. The customer chooses the order type.  
5. The customer confirms the order.  
6. For Home Delivery, an available agent is assigned (or the order is queued if none are available); for Takeaway, an estimated pickup time is set.  
7. The order is recorded in MongoDB with an Order ID.  

**Alternate Flows:**  
- Invalid or missing details prompt for corrections.  
- No available delivery agent results in the order being added to a pending queue.  

**Post Condition:**  
- The order is saved with a proper status and timing details.

---

### Use Case Number: UC-02
**Use Case Name:** Track an Order  
**Overview:**  
Enables customers to view the current status and remaining time for their order.  

**Actors:**  
- Customer, System  

**Pre condition:**  
- An order has been placed and an Order ID is available. 

**Flow:**  
1. The customer selects the "Track Order" option and enters the Order ID.  
2. The system retrieves order details from MongoDB.  
3. The system calculates the time remaining based on the estimated delivery/pickup time.  
4. The system displays the status, estimated time, and (if applicable) the assigned delivery agent for Home Delivery.  

**Alternate Flows:**  
- Invalid Order ID returns an error.  
- For Home Delivery orders with no assigned agent, the system displays “Not available” for time and agent details.  

**Post Condition:**  
- Up-to-date tracking information is provided to the customer.

---

### Use Case Number: UC-03
**Use Case Name:** Manage Delivery Agents  
**Overview:**  
Enables the manager to view and manage delivery agents, including adding new agents and monitoring their status. 

**Actors:**  
- Manager, System  

**Pre condition:**  
- The manager is logged in.  

**Flow:**  
1. The manager selects “Manage Delivery Agents” from the admin menu.  
2. The system displays all delivery agents (from MongoDB).  
3. The manager adds or updates agent details.  
4. The system updates the agents in MongoDB.  

**Alternate Flows:**  
- Invalid details prompt an error and re-entry.  

**Post Condition:**  
- Delivery agents are managed and their statuses updated.

---

### Use Case Number: UC-04
**Use Case Name:** View Restaurant Dashboard  
**Overview:**  
Provides a dashboard for managers to view metrics such as total orders, pending orders, completed orders, and revenue for each restaurant.  
**Actors:**  
- Manager, System, Restaurant 

**Pre condition:**  
- The manager is logged in and there is existing restaurant order data.  

**Flow:**  
1. The manager selects “Restaurant Dashboard” from the admin menu.  
2. The system displays a list of restaurants (from MongoDB).  
3. The manager selects a restaurant.  
4. The system retrieves and displays metrics (order counts, revenue, etc.) and recent orders.  

**Alternate Flows:**  
- No order data results in a notification.

**Post Condition:**  
- Detailed performance data for the selected restaurant is presented.

---

### Use Case Number: UC-05
**Use Case Name:** Persistent System Instance  
**Overview:**  
Ensures that system state (users, orders, restaurants, delivery agents) is maintained across multiple sessions using MongoDB. 

**Actors:**  
- System Administrator, System  

**Pre condition:**  
- The system is connected to MongoDB.  

**Flow:**  
1. Multiple application instances are launched.  
2. Each instance connects to MongoDB and loads current state data.  
3. All instances display consistent and up-to-date information.

**Alternate Flows:**  
- Database connection failures trigger error messages and degraded operation.  

**Post Condition:**  
- The state is synchronized across all instances.

---

### Use Case Number: UC-06
**Use Case Name:** User Registration and Login  
**Overview:**  
Allows new users to register and existing users to log in to the system.  

**Actors:**  
- Customer, System  

**Pre condition:**  
- The user accesses the registration/login interface.

**Flow:**  
1. The user registers by providing name, email, password, phone, and address.  
2. The system validates and saves the user in MongoDB.  
3. The user logs in with email and password.  
4. The system authenticates and grants access.  

**Alternate Flows:**  
- Duplicate registration or authentication failures result in error messages.  

**Post Condition:**  
- The user is registered and logged in successfully.

---

### Use Case Number: UC-07
**Use Case Name:** Manage Menu Items  
**Overview:**  
Allows restaurant managers (via the admin interface) to add, update, or remove menu items for a restaurant.

**Actors:**  
- Manager, System, Restaurant 

**Pre condition:**  
- The manager is logged in and a restaurant is selected.  

**Flow:**  
1. The manager selects “Manage Menu Items” for a restaurant.  
2. The system displays current menu items from MongoDB.  
3. The manager adds or edits menu item details.  
4. The system updates the menu in MongoDB.  

**Alternate Flows:**  
- Invalid menu data triggers error messages.  

**Post Condition:**  
- The restaurant’s menu is updated accordingly.

---

### Use Case Number: UC-08
**Use Case Name:** View Order Details  
**Overview:**  
Allows customers or admins to view detailed information about a specific order.  

**Actors:**  
- Customer, Admin, System, Restaurant, Delivery Agent (if applicable)  

**Pre condition:**  
- The order exists in the system with a valid Order ID. 

**Flow:**  
1. The user selects an order from the order list.  
2. The system retrieves order details from MongoDB.  
3. The system displays detailed order information, including items, pricing, and (for Home Delivery) the delivery agent’s details.

**Alternate Flows:**  
- An invalid Order ID results in an error message.  

**Post Condition:**  
- Detailed order information is presented to the user.

---

### Use Case Number: UC-09
**Use Case Name:** Add Restaurant  
**Overview:**  
Allows an administrator to add a new restaurant to the system, making it available for customer orders.  

**Actors:**  
- Manager, System  

**Pre condition:**  
- The admin is logged in.  

**Flow:**  
1. The admin selects “Add Restaurant” from the admin menu.  
2. The admin enters the restaurant name, address, and cuisine type.  
3. The system validates the input and saves the new restaurant in MongoDB.  
4. The system confirms the successful addition of the restaurant.

**Alternate Flows:**  
- Invalid or missing information triggers error messages and re-entry.  

**Post Condition:**  
- The new restaurant is added to the system and is available for customers to view and order from.

---

## 6. Appendices

### 6.1 Glossary
- **Home Delivery:** Orders delivered to the customer by a delivery agent.
- **Takeaway:** Orders prepared for customer pickup.
- **Delivery Agent:** Personnel responsible for delivering home orders.
- **MongoDB:** A NoSQL database used for data persistence.
- **CLI:** Command-Line Interface.
- **SRS:** Software Requirements Specification.

### 6.2 Index
- **User Management:** Registration, authentication, and profile management.
- **Order Processing:** Order placement, tracking, and status updates.
- **Delivery Management:** Delivery agent assignment and tracking.
- **Restaurant Management:** Management of restaurant data and menus.
- **Administration:** System administration, dashboard views, and data monitoring.

---

*End of SRS Document*


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