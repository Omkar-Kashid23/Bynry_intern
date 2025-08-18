from flask import request, jsonify
from sqlalchemy.exc import SQLAlchemyError

@app.route('/api/products', methods=['POST'])
def create_product():
    # Createing a new product and its initial inventory entry in a single transaction.
    data = request.json
    
    # 1. User input and error handling
    required_fields = ['name', 'sku', 'price', 'warehouse_id', 'initial_quantity']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing one or more required fields in the request body."}), 400

    try:
        # 2. business logic validation (Unique SKU)
        existing_product = Product.query.filter_by(sku=data['sku']).first()
        if existing_product:
            return jsonify({"error": f"Product with SKU '{data['sku']}' already exists."}), 409

        # 3. data type and value validation
        price = float(data['price'])
        initial_quantity = int(data['initial_quantity'])

        if initial_quantity < 0:
            return jsonify({"error": "Initial quantity cannot be a negative value."}), 400

        # 4. Use a single, atomic transaction for data integrity
        product = Product(
            name=data['name'],
            sku=data['sku'],
            price=price,
            warehouse_id=data['warehouse_id']
        )
        db.session.add(product)
        
        # Flush the session to get the new product's ID before committing.
        db.session.flush()

        inventory = Inventory(
            product_id=product.id,
            warehouse_id=data['warehouse_id'],
            quantity=initial_quantity
        )
        db.session.add(inventory)

        # Commit both operations together. If one fails, both are rolled back.
        db.session.commit()

        return jsonify({"message": "Product created successfully.", "product_id": product.id}), 201

    except (ValueError, TypeError):
        # Rollback the session if type conversion fails.
        db.session.rollback()
        return jsonify({"error": "Invalid data type for price or initial_quantity. Please provide numbers."}), 400
    except SQLAlchemyError as e:
        # Rollback the session for any other database-related error.
        db.session.rollback()
        # Log the detailed error for internal debugging
        print(f"An internal database error occurred: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500

'''
1} Database Schema: It's assumed that Product and Inventory are database models with the fields used in the code (e.g., name, sku, price, warehouse_id, product_id, quantity). It's also assumed that a 
db.session object is available for database interactions.

2} SKU Uniqueness: Although the "Additional Context" states that SKUs must be unique, the provided code doesn't enforce this. The corrected code assumes that the database has a unique constraint on the 
sku column, but it also adds an application-level check for robustness.

3} Price Data Type: The code assumes that data['price'] is a value that can be cast to a decimal or float, as per the additional context.
Warehouse Existence: The provided code assumes that the warehouse_id in the request payload corresponds to an existing and valid warehouse. The corrected code doesn't explicitly validate this, assuming it's handled by database foreign key constraints.
Business Logic: It's assumed that the initial product creation and the first inventory count should be a single, atomic operation. The original code's separation of these steps is a key flaw.
'''
