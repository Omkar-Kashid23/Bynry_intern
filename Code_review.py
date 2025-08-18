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
