from flask import Flask, jsonify
from datetime import datetime, timedelta
import logging

app = Flask(__name__)

# Sample for Demonstration
# In a real application, this would all be coming from our database. This is just
# for showing how the logic works.
MOCK_DATABASE = {
    'products': {
        123: {'name': 'Widget A', 'sku': 'WID-001', 'supplier_id': 789, 'type_id': 1},
        124: {'name': 'Gadget B', 'sku': 'GAD-002', 'supplier_id': 790, 'type_id': 2},
    },
    'warehouses': {
        456: {'name': 'Main Warehouse', 'company_id': 1},
        457: {'name': 'West Warehouse', 'company_id': 1}
    },
    'inventory': {
        (123, 456): {'quantity': 5},  # Widget A in Main Warehouse
        (124, 456): {'quantity': 15}, # Gadget B in Main Warehouse
        (123, 457): {'quantity': 25}  # Widget A in West Warehouse
    },
    'inventory_history': [
        {'product_id': 123, 'warehouse_id': 456, 'change': -5, 'timestamp': datetime.now() - timedelta(days=10)}, 
        {'product_id': 124, 'warehouse_id': 456, 'change': -2, 'timestamp': datetime.now() - timedelta(days=2)},  
        {'product_id': 123, 'warehouse_id': 457, 'change': -1, 'timestamp': datetime.now() - timedelta(days=60)} 
    ],
    'suppliers': {
        789: {'name': 'Supplier Corp', 'contact_email': 'orders@supplier.com'},
        790: {'name': 'Tech Supply Inc.', 'contact_email': 'contact@tech.com'}
    },
    'product_types': {
        1: {'threshold': 20}, # Threshold for 'Widget A'
        2: {'threshold': 10}  # Threshold for 'Gadget B'
    }
}

@app.route('/api/companies/<int:company_id>/alerts/low-stock', methods=['GET'])
def get_low_stock_alerts(company_id):

    try:
        # Step 1: Find all warehouses for the given company
        company_warehouses = [
            w_id for w_id, w_data in MOCK_DATABASE['warehouses'].items()
            if w_data['company_id'] == company_id
        ]
        if not company_warehouses:
            # Edge case: The company doesn't exist or has no warehouses. Let's send a 404.
            return jsonify({"alerts": [], "total_alerts": 0, "message": "Company not found or has no warehouses."}), 404

        low_stock_alerts = []
        recent_sales_period = timedelta(days=30)
        
        # Step 2: Iterate through the company's warehouses and their products
        for warehouse_id in company_warehouses:
            # In a real database, we'd do this with a single, efficient query.
            for (p_id, w_id), inv_data in MOCK_DATABASE['inventory'].items():
                if w_id != warehouse_id:
                    continue 

                product_data = MOCK_DATABASE['products'].get(p_id)
                if not product_data:
                    # Edge case: This product's info is missing for some reason.
                    continue 

                current_stock = inv_data['quantity']

                # Step 3: Check for recent sales activity
                sales_in_period = [
                    h['change'] for h in MOCK_DATABASE['inventory_history']
                    if h['product_id'] == p_id and h['warehouse_id'] == w_id and h['timestamp'] > datetime.now() - recent_sales_period
                ]
                
                # We're just looking at the sales (negative changes)
                total_sales_quantity = -sum(c for c in sales_in_period if c < 0)
                if total_sales_quantity == 0:
                    # Edge case: No recent sales, so no alert is needed. We can skip it.
                    continue 

                # Step 4: Determine the low-stock threshold
                product_type_id = product_data.get('type_id')
                threshold = MOCK_DATABASE['product_types'].get(product_type_id, {}).get('threshold', 10) # Default to 10 if we can't find a type

                # Step 5: Check if the product is low on stock
                if current_stock <= threshold:
                    # Step 6: Gather all the necessary alert info
                    supplier_data = MOCK_DATABASE['suppliers'].get(product_data['supplier_id'])
                    
                    # Calculate 'Days Until Stockout' (this is a simplified estimate!)
                    avg_daily_sales = total_sales_quantity / (recent_sales_period.days)
                    days_until_stockout = round(current_stock / avg_daily_sales) if avg_daily_sales > 0 else None

                    alert_details = {
                        "product_id": p_id,
                        "product_name": product_data['name'],
                        "sku": product_data['sku'],
                        "warehouse_id": warehouse_id,
                        "warehouse_name": MOCK_DATABASE['warehouses'][warehouse_id]['name'],
                        "current_stock": current_stock,
                        "threshold": threshold,
                        "days_until_stockout": days_until_stockout,
                        "supplier": {
                            "id": product_data['supplier_id'],
                            "name": supplier_data['name'],
                            "contact_email": supplier_data['contact_email']
                        } if supplier_data else None
                    }
                    low_stock_alerts.append(alert_details)

        # Step 7: Send back the final list of alerts
        return jsonify({
            "alerts": low_stock_alerts,
            "total_alerts": len(low_stock_alerts)
        }), 200

    except Exception as e:
        # Step 8: Handle any unexpected errors gracefully
        logging.error(f"Whoops, something went wrong: {e}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(debug=True)
