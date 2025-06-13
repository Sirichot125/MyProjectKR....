from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd
import random
import logging
import numpy as np  # Import numpy for np.nan

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
# กำหนด format ของ log ให้ชัดเจนขึ้น รวมถึง timestamp
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s",
)


pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)


def create_mock_data():
    """
    อ่านข้อมูลจากไฟล์ Excel หรือ CSV และเตรียม DataFrame
    """
    file_config = {
        "path": "database.xlsx",
        "type": "excel",
        "sheet_name": "PurchaseOrderDtl",
    }
    # --- 📝 1. RENAME คอลัมน์ (ถ้าจำเป็น) ---
    column_rename_map = {
        "MainUnitPrice": "UnitPrice",  # ตัวอย่างการ rename
        # "ชื่อเก่าใน Excel": "ชื่อใหม่ที่ต้องการใน Python"
    }

    df = None
    try:
        file_path = file_config["path"]
        file_type = file_config["type"].lower()
        sheet_name = file_config["sheet_name"]

        logging.info(
            f"Attempting to read data from: {file_path} (Type: {file_type}, Sheet: {sheet_name if sheet_name else 'Default'}, Header Row: 3rd Excel row / index 2)"
        )

        if file_type == "excel":
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=2)
        elif file_type == "csv":
            df = pd.read_csv(file_path, header=2 if sheet_name else 0)
        else:
            logging.error(
                f"Unsupported file type: {file_type}. Please use 'excel' or 'csv'."
            )
            return pd.DataFrame()

        logging.info(f"Successfully read data. Original DataFrame shape: {df.shape}")
        logging.info(f"Original columns after specifying header: {df.columns.tolist()}")

        actual_renames = {k: v for k, v in column_rename_map.items() if k in df.columns}
        if actual_renames:
            df.rename(columns=actual_renames, inplace=True)
            logging.info(f"Columns renamed. New columns: {df.columns.tolist()}")
        else:
            logging.info(
                "No columns were renamed. OK if original names are correct or map keys don't match original columns."
            )

        if "DueDate" in df.columns:
            df["DueDate"] = pd.to_datetime(
                df["DueDate"], errors="coerce"
            )  # Coerce errors
            logging.info("'DueDate' column (post-rename if any) converted to datetime.")
            if df["DueDate"].isnull().any():
                logging.warning(
                    "Some 'DueDate' values could not be converted to datetime and are now NaT."
                )
        else:
            logging.warning(
                "'DueDate' column not found (post-rename if any). Calculations requiring it may fail."
            )

        # --- 🔢 แปลงชนิดข้อมูลคอลัมน์ใหม่ (ถ้าจำเป็น) ---
        if "Quantity" in df.columns:
            df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(
                0
            )  # แปลงเป็นตัวเลข, ถ้า error ให้เป็น NaN แล้วแทนด้วย 0
            logging.info(
                "'Quantity' column converted to numeric and NaNs filled with 0."
            )
        if "UnitPrice" in df.columns:
            df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce").fillna(
                0
            )  # แปลงเป็นตัวเลข, ถ้า error ให้เป็น NaN แล้วแทนด้วย 0
            logging.info(
                "'UnitPrice' column converted to numeric and NaNs filled with 0."
            )

        # --- 📋 2. ระบุคอลัมน์ที่จำเป็นสำหรับการคำนวณ (ถ้าต้องการ Log เตือน) ---
        required_columns_for_calculation = [
            "TotalPrice",
            "Quantity",
            "UnitPrice",
            "ItemCode",
        ]
        for col in required_columns_for_calculation:
            if col not in df.columns:
                logging.warning(
                    f"Required column '{col}' for calculation not found (post-rename if any). Calculations involving it may fail or use defaults."
                )

    except FileNotFoundError:
        logging.error(f"Error: The file was not found at path: {file_config['path']}")
        return pd.DataFrame()
    except Exception as e:
        logging.error(
            f"An error occurred while reading or processing data file: {e}",
            exc_info=True,
        )
        return pd.DataFrame()

    if df is None:
        df = pd.DataFrame()
    return df


df = create_mock_data()

if not df.empty:
    logging.info("DataFrame loaded for dashboard calculation.")
    if "DueDate" in df.columns and pd.api.types.is_datetime64_any_dtype(df["DueDate"]):
        if df["DueDate"].notna().any():
            df["OrderMonth"] = df["DueDate"].dt.to_period("M")
            logging.info("'OrderMonth' column created.")
        else:
            logging.warning(
                "All 'DueDate' values are NaT. Cannot create 'OrderMonth' from .dt accessor."
            )
            df["OrderMonth"] = pd.Series(dtype="period[M]", index=df.index)
    else:
        logging.warning(
            "'DueDate' column is missing or not datetime type (or all NaT). Cannot create 'OrderMonth'."
        )
        df["OrderMonth"] = pd.Series(
            dtype="period[M]", index=df.index if not df.empty else None
        )
else:
    logging.warning(
        "DataFrame is empty after create_mock_data(). Dashboard will use default/empty values."
    )
    if "DueDate" not in df.columns:
        df["DueDate"] = pd.Series(dtype="datetime64[ns]")
    if "OrderMonth" not in df.columns:
        df["OrderMonth"] = pd.Series(dtype="period[M]")
    if "TotalPrice" not in df.columns:
        df["TotalPrice"] = pd.Series(dtype="float")
    # --- 📄 3. เพิ่มคอลัมน์ใหม่สำหรับ DataFrame ว่าง ---
    if "Quantity" not in df.columns:
        df["Quantity"] = pd.Series(dtype="float")
    if "UnitPrice" not in df.columns:
        df["UnitPrice"] = pd.Series(dtype="float")
    if "ItemCode" not in df.columns:
        df["ItemCode"] = pd.Series(dtype="object")
    if "Cost" not in df.columns:
        df["Cost"] = pd.Series(dtype="float")  # เผื่อ Cost ไว้ด้วย


def calculate_dashboard_data(df_input):
    data = {}
    if df_input.empty:
        logging.warning(
            "calculate_dashboard_data received empty DataFrame. Returning defaults."
        )
        # --- ➕ 6. อัปเดต Default Data Structure ---
        return {
            "totalRevenue": 0,
            "netProfit": 0,
            "totalRevenueTrend": 0,
            "netProfitTrend": 0,
            "newCustomers": 0,
            "newCustomersTrend": 0.0,
            "cashFlow": 0,
            "cashFlowTrend": 0.0,
            "netProfitMargin": 0.0,
            "averagePricePerItem": 0.0,  # <--- เพิ่มใหม่
            "revenueByItemData": {"labels": [], "values": []},  # <--- เพิ่มใหม่
            "totalQuantitySold": 0,  # <--- เพิ่มใหม่ (ตัวอย่าง)
            "revenueData": {"labels": [], "values": [], "netProfitValues": []},
            "expensesData": {"labels": [], "values": []},
            "revenueTargetData": {"labels": [], "actual": [], "target": []},
            "uptime": 0.0,
            "uptimeTrend": 0.0,
            "responseTime": 0,
            "responseTimeTrend": 0.0,
            "bugs": 0,
            "bugsTrend": 0.0,
            "deployments": 0,
            "deploymentsTrend": 0.0,
            "uptimeData": {"labels": [], "values": []},
            "responseTimeData": {"labels": [], "values": []},
            "bugCountData": {"labels": [], "values": []},
            "deploymentFrequencyData": {"labels": [], "values": []},
        }

    data["totalRevenue"] = (
        df_input["TotalPrice"].sum()
        if "TotalPrice" in df_input.columns and not df_input["TotalPrice"].empty
        else 0.0
    )

    if "Cost" in df_input.columns and not df_input["Cost"].empty:
        total_cost = df_input["Cost"].sum()
        data["netProfit"] = data["totalRevenue"] - total_cost
        logging.info(f"Calculated netProfit using actual Cost: {data['netProfit']}")
    else:
        data["netProfit"] = data["totalRevenue"] * 0.2
        logging.info(
            f"Calculated netProfit as 20% of TotalRevenue (Cost column not found/used or empty): {data['netProfit']}"
        )

    # --- ✨ 4.1 เพิ่มการ Aggregate คอลัมน์ใหม่ (ถ้าต้องการ) ---
    agg_dict = {}
    if "TotalPrice" in df_input.columns:
        agg_dict["TotalPrice_sum"] = ("TotalPrice", "sum")
    if "DueDate" in df_input.columns:
        agg_dict["DueDate_nunique"] = ("DueDate", "nunique")
    if "CustomerID" in df_input.columns:
        agg_dict["UniqueCustomers"] = ("CustomerID", "nunique")  # สมมติว่ามี CustomerID
    if "Cost" in df_input.columns:
        agg_dict["Cost_sum"] = ("Cost", "sum")
    if "Quantity" in df_input.columns:
        agg_dict["Quantity_sum"] = ("Quantity", "sum")  # <--- เพิ่ม Quantity sum

    monthly_data = pd.DataFrame()
    if (
        "OrderMonth" in df_input.columns
        and isinstance(df_input["OrderMonth"].dtype, pd.PeriodDtype)
        and df_input["OrderMonth"].notna().any()
        and not df_input.empty
        and agg_dict
    ):
        try:
            monthly_data = (
                df_input.groupby(df_input["OrderMonth"]).agg(**agg_dict).reset_index()
            )
            rename_cols = {}
            if "TotalPrice_sum" in monthly_data.columns:
                rename_cols["TotalPrice_sum"] = "TotalPrice"
            if "DueDate_nunique" in monthly_data.columns:
                rename_cols["DueDate_nunique"] = "DueDate"
            if "UniqueCustomers" in monthly_data.columns:
                rename_cols["UniqueCustomers"] = "NewCustomersInMonth"
            if "Cost_sum" in monthly_data.columns:
                rename_cols["Cost_sum"] = "Cost"
            if "Quantity_sum" in monthly_data.columns:
                rename_cols["Quantity_sum"] = (
                    "TotalQuantity"  # <--- Rename Quantity sum
                )
            monthly_data.rename(columns=rename_cols, inplace=True)
        except Exception as e:
            logging.error(
                f"Error during groupby/agg or rename for monthly_data: {e}",
                exc_info=True,
            )
            # (ส่วนสร้าง monthly_data ว่าง ถ้าเกิด error - เหมือนเดิม)
            columns_for_empty_monthly = [
                "OrderMonth",
                "TotalPrice",
                "DueDate",
                "NewCustomersInMonth",
                "Cost",
                "TotalQuantity",
            ]
            monthly_data = pd.DataFrame(
                columns=[
                    col
                    for col in columns_for_empty_monthly
                    if col in rename_cols.values() or col == "OrderMonth"
                ]
            )

    else:
        logging.warning(
            "Could not group by 'OrderMonth' (missing, wrong type, all NaT, empty df, or no aggregations). Monthly data will be empty."
        )
        expected_cols = ["OrderMonth"]
        if "TotalPrice_sum" in agg_dict:
            expected_cols.append("TotalPrice")
        if "DueDate_nunique" in agg_dict:
            expected_cols.append("DueDate")
        if "UniqueCustomers" in agg_dict:
            expected_cols.append("NewCustomersInMonth")
        if "Cost_sum" in agg_dict:
            expected_cols.append("Cost")
        if "Quantity_sum" in agg_dict:
            expected_cols.append("TotalQuantity")  # <--- เพิ่ม
        monthly_data = pd.DataFrame(columns=expected_cols)

    # (ส่วนคำนวณ Trend ต่างๆ - เหมือนเดิม)
    if len(monthly_data) >= 2:
        last_month_data = monthly_data.iloc[-1]
        prev_month_data = monthly_data.iloc[-2]
        last_total_price = (
            last_month_data.get("TotalPrice", 0)
            if pd.api.types.is_number(last_month_data.get("TotalPrice"))
            else 0
        )
        prev_total_price = (
            prev_month_data.get("TotalPrice", 0)
            if pd.api.types.is_number(prev_month_data.get("TotalPrice"))
            else 0
        )
        data["totalRevenueTrend"] = (
            (last_total_price - prev_total_price) / prev_total_price
            if prev_total_price != 0
            else 0.0
        )
        last_cost = (
            last_month_data.get("Cost", 0)
            if pd.api.types.is_number(last_month_data.get("Cost"))
            else 0
        )
        prev_cost = (
            prev_month_data.get("Cost", 0)
            if pd.api.types.is_number(prev_month_data.get("Cost"))
            else 0
        )
        if "Cost" in monthly_data.columns:
            last_profit = last_total_price - last_cost
            prev_profit = prev_total_price - prev_cost
            data["netProfitTrend"] = (
                (last_profit - prev_profit) / prev_profit if prev_profit != 0 else 0.0
            )
        else:
            data["netProfitTrend"] = (
                (last_total_price * 0.2 - prev_total_price * 0.2)
                / (prev_total_price * 0.2)
                if prev_total_price * 0.2 != 0
                else 0.0
            )
    else:
        data["totalRevenueTrend"] = 0.0
        data["netProfitTrend"] = 0.0

    # (ส่วนคำนวณ newCustomers - เหมือนเดิม)
    logging.info(
        f"Before newCustomers calculation: Monthly_data is empty: {monthly_data.empty}, columns: {monthly_data.columns.tolist()}"
    )
    raw_value_for_new_customers = 0
    if not monthly_data.empty:
        logging.info(
            f"Monthly_data shape: {monthly_data.shape}, dtypes:\n{monthly_data.dtypes}"
        )
        logging.info(f"Monthly_data tail(1):\n{monthly_data.tail(1)}")
        last_month_data = monthly_data.iloc[-1]
        # ( ...ส่วน log ของ newCustomers ... )
        if "NewCustomersInMonth" in last_month_data and pd.api.types.is_number(
            last_month_data["NewCustomersInMonth"]
        ):
            raw_value_for_new_customers = last_month_data["NewCustomersInMonth"]
        elif "DueDate" in last_month_data and pd.api.types.is_number(
            last_month_data["DueDate"]
        ):
            raw_value_for_new_customers = last_month_data["DueDate"]
        else:
            raw_value_for_new_customers = 0
    else:
        raw_value_for_new_customers = 0
    try:  # ( ...ส่วน try-except ของ newCustomers ... )
        if isinstance(raw_value_for_new_customers, type):
            data["newCustomers"] = 0
        elif pd.isna(raw_value_for_new_customers):
            data["newCustomers"] = 0
        else:
            data["newCustomers"] = int(raw_value_for_new_customers)
    except (ValueError, TypeError) as e:
        data["newCustomers"] = 0
    logging.info(
        f"Calculated newCustomers: {data['newCustomers']} (Type: {type(data['newCustomers'])})"
    )

    data["newCustomersTrend"] = 0.15
    data["cashFlow"] = data["netProfit"]
    data["cashFlowTrend"] = data["netProfitTrend"]

    # --- 📊 4.2 คำนวณ Metrics และ Chart Data ใหม่ ---
    # ตัวอย่าง: Average Price per Item (ราคาสินค้าเฉลี่ยต่อชิ้น)
    total_quantity_sold = (
        df_input["Quantity"].sum()
        if "Quantity" in df_input.columns and not df_input["Quantity"].empty
        else 0
    )
    data["totalQuantitySold"] = total_quantity_sold  # เก็บยอดรวมจำนวนที่ขายได้
    if total_quantity_sold > 0 and data["totalRevenue"] > 0:
        data["averagePricePerItem"] = data["totalRevenue"] / total_quantity_sold
        logging.info(f"Calculated averagePricePerItem: {data['averagePricePerItem']}")
    else:
        data["averagePricePerItem"] = 0.0
        logging.info("averagePricePerItem set to 0 due to zero quantity or revenue.")

    # ตัวอย่าง: ยอดขายตาม ItemCode (Revenue per ItemCode) - Top 5
    if (
        "ItemCode" in df_input.columns
        and "TotalPrice" in df_input.columns
        and not df_input.empty
    ):
        try:
            # Ensure ItemCode is string for grouping, handle NaN
            df_input["ItemCode"] = df_input["ItemCode"].astype(str).fillna("Unknown")
            item_revenue = (
                df_input.groupby("ItemCode")["TotalPrice"]
                .sum()
                .sort_values(ascending=False)
                .head(5)
            )
            data["revenueByItemData"] = {
                "labels": item_revenue.index.tolist(),
                "values": item_revenue.values.tolist(),
            }
            logging.info(f"Calculated revenueByItemData for top 5 items.")
        except Exception as e:
            logging.error(f"Error calculating revenueByItemData: {e}", exc_info=True)
            data["revenueByItemData"] = {"labels": [], "values": []}
    else:
        data["revenueByItemData"] = {"labels": [], "values": []}
        logging.warning(
            "Could not calculate revenueByItemData due to missing ItemCode/TotalPrice or empty DataFrame."
        )

    # (ส่วน revenueData, expensesData, etc. - เหมือนเดิม)
    months = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]
    monthly_revenue_series = pd.Series(index=months, dtype="float64").fillna(0.0)
    monthly_profit_series = pd.Series(index=months, dtype="float64").fillna(0.0)
    monthly_expenses_series = pd.Series(index=months, dtype="float64").fillna(0.0)
    if (
        "DueDate" in df_input.columns
        and pd.api.types.is_datetime64_any_dtype(df_input["DueDate"])
        and "TotalPrice" in df_input.columns
        and not df_input.empty
    ):
        try:
            temp_due_date = df_input["DueDate"]
            valid_due_dates_mask = temp_due_date.notna()
            if valid_due_dates_mask.any():
                df_valid_dates = df_input[valid_due_dates_mask]
                grouped_revenue = df_valid_dates.groupby(
                    df_valid_dates["DueDate"].dt.strftime("%b")
                )["TotalPrice"].sum()
                monthly_revenue_series = monthly_revenue_series.add(
                    grouped_revenue, fill_value=0
                )
                if "Cost" in df_valid_dates.columns:
                    grouped_cost = df_valid_dates.groupby(
                        df_valid_dates["DueDate"].dt.strftime("%b")
                    )["Cost"].sum()
                    monthly_cost_series_temp = (
                        pd.Series(index=months, dtype="float64")
                        .fillna(0)
                        .add(grouped_cost, fill_value=0)
                    )
                    monthly_profit_series = monthly_revenue_series.subtract(
                        monthly_cost_series_temp, fill_value=0
                    )
                    monthly_expenses_series = monthly_cost_series_temp
                else:
                    monthly_profit_series = monthly_revenue_series * 0.2
                    monthly_expenses_series = monthly_revenue_series * 0.8
        except Exception as e:
            logging.error(f"Error calculating monthly chart data: {e}", exc_info=True)
    data["revenueData"] = {
        "labels": months,
        "values": monthly_revenue_series.tolist(),
        "netProfitValues": monthly_profit_series.tolist(),
    }
    data["expensesData"] = {
        "labels": months,
        "values": monthly_expenses_series.tolist(),
    }
    data["netProfitMargin"] = (
        data["netProfit"] / data["totalRevenue"] if data["totalRevenue"] != 0 else 0.0
    )
    data["revenueTargetData"] = {
        "labels": months,
        "actual": data["revenueData"]["values"],
        "target": [v * 1.2 for v in data["revenueData"]["values"]],
    }

    # (ส่วน Placeholder data - เหมือนเดิม)
    data["uptime"] = round(
        random.uniform(99.5, 100.0), 2
    )  # ... (and other random data) ...
    data["uptimeTrend"] = round(random.uniform(-0.01, 0.01), 2)
    data["responseTime"] = random.randint(50, 200)
    data["responseTimeTrend"] = round(random.uniform(-0.1, 0.1), 1)
    data["bugs"] = random.randint(0, 10)
    data["bugsTrend"] = round(random.uniform(-0.2, 0.2), 1)
    data["deployments"] = random.randint(1, 5)
    data["deploymentsTrend"] = round(random.uniform(-0.1, 0.1), 1)
    data["uptimeData"] = {
        "labels": months,
        "values": [round(random.uniform(99.0, 100.0), 2) for _ in months],
    }
    data["responseTimeData"] = {
        "labels": months,
        "values": [random.randint(50, 200) for _ in months],
    }
    data["bugCountData"] = {
        "labels": months,
        "values": [random.randint(0, 10) for _ in months],
    }
    data["deploymentFrequencyData"] = {
        "labels": months,
        "values": [random.randint(1, 5) for _ in months],
    }

    return data


dashboard_data = calculate_dashboard_data(df)
logging.info(
    f"Initial dashboard_data calculation complete. newCustomers: {dashboard_data.get('newCustomers')}, newCustomersTrend: {dashboard_data.get('newCustomersTrend')}"
)


# --- API Endpoints ---
# (ส่วน get_total_revenue, get_net_profit, get_new_customers, etc. - เหมือนเดิม)
@app.route("/api/total-revenue", methods=["GET"])
def get_total_revenue():
    return jsonify(
        {
            "value": dashboard_data.get("totalRevenue", 0),
            "trend": dashboard_data.get("totalRevenueTrend", 0),
        }
    )


@app.route("/api/net-profit", methods=["GET"])
def get_net_profit():
    return jsonify(
        {
            "value": dashboard_data.get("netProfit", 0),
            "trend": dashboard_data.get("netProfitTrend", 0),
        }
    )


@app.route("/api/new-customers", methods=["GET"])
def get_new_customers():
    logging.info("Request received for /api/new-customers")
    raw_value_new_customers = dashboard_data.get("newCustomers")
    final_value_new_customers = 0
    if pd.api.types.is_number(raw_value_new_customers) and not pd.isna(
        raw_value_new_customers
    ):
        final_value_new_customers = int(raw_value_new_customers)
    elif isinstance(raw_value_new_customers, type):
        final_value_new_customers = 0
    else:
        final_value_new_customers = 0
    raw_value_trend = dashboard_data.get("newCustomersTrend")
    final_value_trend = 0.0
    if pd.api.types.is_number(raw_value_trend) and not pd.isna(raw_value_trend):
        final_value_trend = float(raw_value_trend)
    elif isinstance(raw_value_trend, type):
        final_value_trend = 0.0
    else:
        final_value_trend = 0.0
    logging.info(
        f"Values for jsonify in /api/new-customers: value={final_value_new_customers} (type: {type(final_value_new_customers)}), trend={final_value_trend} (type: {type(final_value_trend)})"
    )
    try:
        return jsonify(
            {
                "value": final_value_new_customers,
                "trend": final_value_trend,
            }
        )
    except Exception as e:
        logging.error(f"Error during jsonify in /api/new-customers: {e}", exc_info=True)
        return jsonify({"error": "Failed to serialize data", "details": str(e)}), 500


@app.route("/api/cash-flow", methods=["GET"])
def get_cash_flow():
    return jsonify(
        {
            "value": dashboard_data.get("cashFlow", 0),
            "trend": dashboard_data.get("cashFlowTrend", 0),
        }
    )


@app.route("/api/net-profit-margin", methods=["GET"])
def get_net_profit_margin():
    return jsonify({"value": dashboard_data.get("netProfitMargin", 0)})


# --- 🚀 5. เพิ่ม API ENDPOINTS ใหม่ ---
@app.route("/api/average-price-per-item", methods=["GET"])
def get_average_price_per_item():
    logging.info("Request received for /api/average-price-per-item")
    value = dashboard_data.get("averagePricePerItem", 0.0)
    # Ensure the value is a float or int
    if not isinstance(value, (int, float)):
        logging.warning(
            f"/api/average-price-per-item: value '{value}' (type: {type(value)}) is not a number. Defaulting to 0.0."
        )
        value = 0.0
    return jsonify({"value": value})


@app.route("/api/revenue-by-item", methods=["GET"])
def get_revenue_by_item_data():
    logging.info("Request received for /api/revenue-by-item")
    data_to_return = dashboard_data.get(
        "revenueByItemData", {"labels": [], "values": []}
    )
    # Basic validation for chart data structure
    if not (
        isinstance(data_to_return, dict)
        and "labels" in data_to_return
        and isinstance(data_to_return["labels"], list)
        and "values" in data_to_return
        and isinstance(data_to_return["values"], list)
    ):
        logging.warning(
            f"/api/revenue-by-item: Data structure is invalid. Defaulting. Data: {data_to_return}"
        )
        data_to_return = {"labels": [], "values": []}
    return jsonify(data_to_return)


@app.route("/api/total-quantity-sold", methods=["GET"])
def get_total_quantity_sold():
    logging.info("Request received for /api/total-quantity-sold")
    value = dashboard_data.get("totalQuantitySold", 0)
    if not isinstance(value, (int, float)):  # Should be int from sum
        logging.warning(
            f"/api/total-quantity-sold: value '{value}' (type: {type(value)}) is not a number. Defaulting to 0."
        )
        value = 0
    return jsonify({"value": int(value)})  # Ensure int


# (ส่วน API Endpoints ที่เหลือ - เหมือนเดิม)
@app.route("/api/revenue-data", methods=["GET"])
def get_revenue_data():
    return jsonify(
        dashboard_data.get(
            "revenueData", {"labels": [], "values": [], "netProfitValues": []}
        )
    )


@app.route("/api/expenses-data", methods=["GET"])
def get_expenses_data():
    return jsonify(dashboard_data.get("expensesData", {"labels": [], "values": []}))


@app.route("/api/revenue-target-data", methods=["GET"])
def get_revenue_target_data():
    return jsonify(
        dashboard_data.get(
            "revenueTargetData", {"labels": [], "actual": [], "target": []}
        )
    )


@app.route("/api/uptime", methods=["GET"])
def get_uptime():
    return jsonify(
        {
            "value": dashboard_data.get("uptime", 0),
            "trend": dashboard_data.get("uptimeTrend", 0),
        }
    )


@app.route("/api/response-time", methods=["GET"])
def get_response_time():
    return jsonify(
        {
            "value": dashboard_data.get("responseTime", 0),
            "trend": dashboard_data.get("responseTimeTrend", 0),
        }
    )


@app.route("/api/bugs", methods=["GET"])
def get_bugs():
    return jsonify(
        {
            "value": dashboard_data.get("bugs", 0),
            "trend": dashboard_data.get("bugsTrend", 0),
        }
    )


@app.route("/api/deployments", methods=["GET"])
def get_deployments():
    return jsonify(
        {
            "value": dashboard_data.get("deployments", 0),
            "trend": dashboard_data.get("deploymentsTrend", 0),
        }
    )


@app.route("/api/uptime-data", methods=["GET"])
def get_uptime_data():
    return jsonify(dashboard_data.get("uptimeData", {"labels": [], "values": []}))


@app.route("/api/response-time-data", methods=["GET"])
def get_response_time_data():
    return jsonify(dashboard_data.get("responseTimeData", {"labels": [], "values": []}))


@app.route("/api/bug-count-data", methods=["GET"])
def get_bug_count_data():
    return jsonify(dashboard_data.get("bugCountData", {"labels": [], "values": []}))


@app.route("/api/deployment-frequency-data", methods=["GET"])
def get_deployment_frequency_data():
    return jsonify(
        dashboard_data.get("deploymentFrequencyData", {"labels": [], "values": []})
    )


if __name__ == "__main__":
    logging.info("Starting Flask application...")
    app.run(debug=True, port=5000, host="127.0.0.1", use_reloader=False)
