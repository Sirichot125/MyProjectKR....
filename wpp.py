from flask import Flask, jsonify
from flask_cors import CORS
from mock_data import create_mock_data, calculate_dashboard_metrics

app = Flask(__name__)

# แก้ไข CORS configuration ให้รองรับทุก route
CORS(app, origins=["http://127.0.0.1:5501", "http://localhost:5501"])

try:
    # สร้างข้อมูลจำลอง
    df = create_mock_data()
    dashboard_data = calculate_dashboard_metrics(df)
except Exception as e:
    print(f"Error creating mock data: {str(e)}")
    dashboard_data = None


@app.route("/api/total-revenue")
def get_total_revenue():
    try:
        if dashboard_data is None:
            raise Exception("Dashboard data not available")
        return jsonify(
            {"value": dashboard_data["metrics"]["Total Revenue"], "trend": 0.15}
        )
    except Exception as e:
        print(f"Error in total-revenue: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/net-profit")
def get_net_profit():
    try:
        if dashboard_data is None:
            raise Exception("Dashboard data not available")
        return jsonify(
            {"value": dashboard_data["metrics"]["Net Profit"], "trend": 0.10}
        )
    except Exception as e:
        print(f"Error in net-profit: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/new-customers")
def get_new_customers():
    try:
        if dashboard_data is None:
            raise Exception("Dashboard data not available")
        return jsonify(
            {"value": dashboard_data["metrics"]["New Customers"], "trend": 0.05}
        )
    except Exception as e:
        print(f"Error in new-customers: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/cash-flow")
def get_cash_flow():
    try:
        if dashboard_data is None:
            raise Exception("Dashboard data not available")
        return jsonify({"value": dashboard_data["metrics"]["Cash Flow"], "trend": 0.08})
    except Exception as e:
        print(f"Error in cash-flow: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/revenue-data")
def get_revenue_data():
    try:
        if dashboard_data is None:
            raise Exception("Dashboard data not available")
        return jsonify(
            {
                "labels": list(dashboard_data["revenue_data"]["labels"]),
                "values": list(dashboard_data["revenue_data"]["values"]),
                "netProfitValues": list(dashboard_data["revenue_data"]["values"] * 0.3),
            }
        )
    except Exception as e:
        print(f"Error in revenue-data: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/expenses-data")
def get_expenses_data():
    try:
        if dashboard_data is None:
            raise Exception("Dashboard data not available")
        return jsonify(
            {
                "labels": list(dashboard_data["expense_data"]["labels"]),
                "values": list(dashboard_data["expense_data"]["values"]),
            }
        )
    except Exception as e:
        print(f"Error in expenses-data: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/net-profit-margin")
def get_net_profit_margin():
    try:
        if dashboard_data is None:
            raise Exception("Dashboard data not available")
        return jsonify({"value": dashboard_data["profit_margin"] / 100})
    except Exception as e:
        print(f"Error in net-profit-margin: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/revenue-target-data")
def get_revenue_target_data():
    try:
        if dashboard_data is None:
            raise Exception("Dashboard data not available")
        return jsonify(
            {
                "labels": list(dashboard_data["revenue_target"]["labels"]),
                "actual": list(dashboard_data["revenue_target"]["actual"]),
                "target": list(dashboard_data["revenue_target"]["target"]),
            }
        )
    except Exception as e:
        print(f"Error in revenue-target-data: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
