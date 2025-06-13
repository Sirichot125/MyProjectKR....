from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd
import random
import logging

app = Flask(__name__)
# ตั้งค่า CORS ให้กับ API endpoints ทั้งหมด
CORS(app, resources={r"/api/*": {"origins": "*"}})
logging.basicConfig(level=logging.INFO)  # ตั้งค่า logging เพื่อดูข้อมูลการทำงานและข้อผิดพลาด

# ตั้งค่าการแสดงผลของ Pandas (มีประโยชน์ตอนดีบัก)
pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)


def create_mock_data():
    """
    อ่านข้อมูลจากไฟล์ Excel หรือ CSV และเตรียม DataFrame
    !!! ผู้ใช้ต้องแก้ไขส่วนการกำหนดค่าไฟล์ (file_config) และการแมปชื่อคอลัมน์ (column_rename_map) ด้านล่าง !!!
    """
    # --- 1. กำหนดค่าไฟล์ข้อมูลของคุณที่นี่ ---
    file_config = {
        "path": "database.xlsx",
        "type": "excel",
        "sheet_name": "PurchaseOrderDtl",
    }

    # --- 2. กำหนดการเปลี่ยนชื่อคอลัมน์ (ถ้าจำเป็น) ---
    # จาก Log ล่าสุด (image_428c7f.png) หลังจากใช้ header=2 แล้ว
    # ชื่อคอลัมน์ "DueDate" และ "TotalPrice" มีอยู่ใน "Original columns after specifying header" แล้ว
    # ดังนั้น หากชื่อเหล่านั้นคือชื่อที่คุณต้องการใช้จริงๆ คุณอาจไม่จำเป็นต้อง rename สองคอลัมน์นี้อีก
    column_rename_map = {
        # <<_ตรวจสอบ Log 'Original columns after specifying header:' ของคุณ_>>
        # ตัวอย่าง: ถ้า Log แสดงว่ามีคอลัมน์ชื่อ "Order Date" และคุณต้องการให้มันเป็น "DueDate" ในโค้ด:
        # "Order Date": "DueDate",

        # ตัวอย่าง: ถ้า Log แสดงว่ามีคอลัมน์ชื่อ "Amount" และคุณต้องการให้มันเป็น "TotalPrice" ในโค้ด:
        # "Amount": "TotalPrice",

        # ตัวอย่าง: ถ้า Log แสดงว่ามีคอลัมน์ชื่อ "ActualItemCost" และคุณต้องการให้เป็น "Cost" สำหรับคำนวณ NetProfit:
        # "ActualItemCost": "Cost",

        # ถ้าชื่อ "DueDate" และ "TotalPrice" ที่อ่านได้จาก Excel (หลัง header=2) ถูกต้องแล้ว
        # และคุณไม่ต้องการ rename คอลัมน์อื่นเพิ่มเติม ให้ปล่อย dict นี้ว่างไว้:
        # column_rename_map = {}
    }
    # ----------------------------------------------------

    df = None

    try:
        file_path = file_config["path"]
        file_type = file_config["type"].lower()
        sheet_name = file_config["sheet_name"]

        logging.info(
            f"Attempting to read data from: {file_path} (Type: {file_type}, Sheet: {sheet_name if sheet_name else 'Default'}, Header Row: 3rd Excel row / index 2)"
        )

        if file_type == "excel":
            df = pd.read_excel(
                file_path, sheet_name=sheet_name, header=2
            )  # ใช้ header=2
        elif file_type == "csv":
            # สำหรับ CSV ถ้าโครงสร้างคล้าย Excel (มีหัวตารางจริงๆ อยู่แถว 3) ก็อาจจะใช้ header=2
            # แต่ถ้า CSV มี header อยู่แถวแรกสุด ก็ใช้ header=0 (หรือลบ parameter header ออกไปเลย)
            df = pd.read_csv(
                file_path, header=2 if sheet_name else 0 # ปรับ header สำหรับ CSV ตามความเหมาะสม
            )
        else:
            logging.error(
                f"Unsupported file type: {file_type}. Please use 'excel' or 'csv'."
            )
            return pd.DataFrame()

        logging.info(f"Successfully read data. Original DataFrame shape: {df.shape}")
        logging.info(f"Original columns after specifying header: {df.columns.tolist()}")

        # --- ทำการเปลี่ยนชื่อคอลัมน์ ---
        actual_renames = {k: v for k, v in column_rename_map.items() if k in df.columns}
        if actual_renames:
            df.rename(columns=actual_renames, inplace=True)
            logging.info(f"Columns renamed. New columns: {df.columns.tolist()}")
        else:
            logging.info(
                "No columns were renamed. This is OK if original column names (from header) are already what you need, or if map keys don't match any original columns."
            )

        # --- การแปลงชนิดข้อมูล และตรวจสอบคอลัมน์ที่จำเป็น (หลังจาก rename ถ้ามี) ---
        if "DueDate" in df.columns:
            df["DueDate"] = pd.to_datetime(df["DueDate"])
            logging.info("'DueDate' column (post-rename if any) converted to datetime.")
        else:
            logging.warning(
                "'DueDate' column not found (post-rename if any). Calculations requiring it may fail."
            )

        # <<_เพิ่มคอลัมน์ที่จำเป็นอื่นๆ ที่นี่_>> เช่น "Cost", "CustomerID"
        required_columns_for_calculation = ["TotalPrice"]
        for col in required_columns_for_calculation:
            if col not in df.columns:
                logging.warning(
                    f"Required column '{col}' not found (post-rename if any). Calculations involving it may fail."
                )

    except FileNotFoundError:
        logging.error(
            f"Error: The file was not found at the specified path: {file_config['path']}"
        )
        return pd.DataFrame()
    except Exception as e:
        logging.error(
            f"An error occurred while reading or processing the data file: {e}"
        )
        return pd.DataFrame()

    if df is None:
        logging.warning(
            "DataFrame is still None after try-except block. Returning empty DataFrame."
        )
        df = pd.DataFrame()

    return df


# --- ส่วนหลักของโปรแกรม ---
df = create_mock_data() # เรียกฟังก์ชันเพื่อโหลดข้อมูล (เรียกครั้งเดียว)

if not df.empty:
    logging.info("DataFrame loaded successfully for dashboard calculation.")
    if "DueDate" in df.columns and pd.api.types.is_datetime64_any_dtype(df["DueDate"]):
        df["OrderMonth"] = df["DueDate"].dt.to_period("M")
        logging.info("'OrderMonth' column created.")
    else:
        logging.warning(
            "'DueDate' column is missing or not datetime type after create_mock_data(). Cannot create 'OrderMonth'."
        )
        # สร้างคอลัมน์ OrderMonth ว่างๆ เพื่อไม่ให้ code ส่วนอื่น error ทันที
        # (แต่อาจจะทำให้ monthly_data ว่างเปล่า ถ้า OrderMonth สำคัญมาก)
        df["OrderMonth"] = pd.Series(dtype="period[M]")
else:
    logging.warning(
        "DataFrame is empty after create_mock_data(). Dashboard will use default/empty values."
    )
    # สร้างคอลัมน์ที่จำเป็นหาก df ว่าง เพื่อไม่ให้เกิด error ใน calculate_dashboard_data
    if "DueDate" not in df.columns: df["DueDate"] = pd.Series(dtype="datetime64[ns]")
    if "OrderMonth" not in df.columns: df["OrderMonth"] = pd.Series(dtype="period[M]")
    if "TotalPrice" not in df.columns: df["TotalPrice"] = pd.Series(dtype="float")
    # <<_เพิ่มการสร้างคอลัมน์ว่างอื่นๆ ที่จำเป็นสำหรับ calculate_dashboard_data ที่นี่_>>
    # if "Cost" not in df.columns: df["Cost"] = pd.Series(dtype="float")
    # if "CustomerID" not in df.columns: df["CustomerID"] = pd.Series(dtype="object")


def calculate_dashboard_data(
    df_input,
):
    data = {}
    if df_input.empty:
        logging.warning(
            "calculate_dashboard_data received an empty DataFrame. Returning default dashboard data."
        )
        # (โค้ดส่วน return default data เหมือนเดิม)
        return {
            "totalRevenue": 0, "netProfit": 0, "totalRevenueTrend": 0, "netProfitTrend": 0,
            "newCustomers": 0, "newCustomersTrend": 0, "cashFlow": 0, "cashFlowTrend": 0,
            "netProfitMargin": 0,
            "revenueData": {"labels": [], "values": [], "netProfitValues": []},
            "expensesData": {"labels": [], "values": []},
            "revenueTargetData": {"labels": [], "actual": [], "target": []},
            "uptime": 0, "uptimeTrend": 0, "responseTime": 0, "responseTimeTrend": 0,
            "bugs": 0, "bugsTrend": 0, "deployments": 0, "deploymentsTrend": 0,
            "uptimeData": {"labels": [], "values": []},
            "responseTimeData": {"labels": [], "values": []},
            "bugCountData": {"labels": [], "values": []},
            "deploymentFrequencyData": {"labels": [], "values": []},
        }

    data["totalRevenue"] = (
        df_input["TotalPrice"].sum() if "TotalPrice" in df_input.columns else 0
    )

    # --- <<_ปรับปรุงการคำนวณ NetProfit ที่นี่_>> ---
    # ตัวอย่าง: ถ้าคุณมีคอลัมน์ "Cost" (หลังจาก rename ถ้าจำเป็น)
    if "Cost" in df_input.columns:
        total_cost = df_input["Cost"].sum()
        data["netProfit"] = data["totalRevenue"] - total_cost
        logging.info(f"Calculated netProfit using TotalRevenue - Cost: {data['netProfit']}")
    else:
        data["netProfit"] = data["totalRevenue"] * 0.2  # ใช้ค่าประมาณเดิมถ้าไม่มี Cost
        logging.info(f"Calculated netProfit as 20% of TotalRevenue: {data['netProfit']}")
    # ---------------------------------------------

    if (
        "OrderMonth" in df_input.columns
        and isinstance(df_input["OrderMonth"].dtype, pd.PeriodDtype)
        and "TotalPrice" in df_input.columns
        and "DueDate" in df_input.columns
        and pd.api.types.is_datetime64_any_dtype(df_input["DueDate"])
        # <<_เพิ่มการตรวจสอบคอลัมน์ที่จำเป็นสำหรับการ aggregate ที่นี่_>>
        # and "CustomerID" in df_input.columns # ถ้าจะใช้ CustomerID
    ):
        agg_functions = {
            "TotalPrice_sum": ("TotalPrice", "sum"),
            "DueDate_nunique": ("DueDate", "nunique"),
            # <<_เพิ่มการ aggregate สำหรับ CustomerID ที่นี่ ถ้าต้องการ_>>
            # "UniqueCustomers": ("CustomerID", "nunique"),
        }
        monthly_data = (
            df_input.groupby("OrderMonth")
            .agg(agg_functions)
            .reset_index()
        )
        rename_monthly_columns = {"TotalPrice_sum": "TotalPrice", "DueDate_nunique": "DueDate"}
        # if "UniqueCustomers" in monthly_data.columns:
        #     rename_monthly_columns["UniqueCustomers"] = "NewCustomersInMonth"
        monthly_data.rename(columns=rename_monthly_columns, inplace=True)
    else:
        monthly_data = pd.DataFrame(columns=["OrderMonth", "TotalPrice", "DueDate"]) #, "NewCustomersInMonth"])
        logging.warning(
            "Could not group by 'OrderMonth' due to missing or incorrect type columns. Monthly data will be empty."
        )

    if len(monthly_data) >= 2:
        # (โค้ดส่วนคำนวณ Trend เหมือนเดิม)
        last_month = monthly_data.iloc[-1]
        prev_month = monthly_data.iloc[-2]
        data["totalRevenueTrend"] = (
            (last_month["TotalPrice"] - prev_month["TotalPrice"])
            / prev_month["TotalPrice"]
            if prev_month["TotalPrice"] != 0
            else 0
        )
        data["netProfitTrend"] = (
            (last_month["TotalPrice"] * 0.2 - prev_month["TotalPrice"] * 0.2) # <<_ถ้า NetProfit เปลี่ยน ต้องแก้ Trend ด้วย_>>
            / (prev_month["TotalPrice"] * 0.2)
            if prev_month["TotalPrice"] != 0
            else 0
        )
        # ถ้า NetProfit คำนวณจาก Cost จริง ควรปรับ NetProfitTrend ให้สอดคล้องกัน
        # if "Cost" in df_input.columns and prev_month["TotalPrice"] - prev_month.get("Cost", 0) !=0 : #สมมติ monthly_data มี Cost ด้วย
        #     last_month_profit = last_month["TotalPrice"] - last_month.get("Cost", 0)
        #     prev_month_profit = prev_month["TotalPrice"] - prev_month.get("Cost", 0)
        #     data["netProfitTrend"] = (last_month_profit - prev_month_profit) / prev_month_profit if prev_month_profit != 0 else 0


    else:
        data["totalRevenueTrend"] = 0
        data["netProfitTrend"] = 0

    logging.info(f"Before newCustomers calculation: Monthly_data is empty: {monthly_data.empty}")
    if not monthly_data.empty:
        logging.info(f"Monthly_data shape: {monthly_data.shape}")
        logging.info(f"Monthly_data columns: {monthly_data.columns.tolist()}")
        logging.info(f"Monthly_data head:\n{monthly_data.head()}")
    else:
        logging.info("Monthly_data is indeed empty before newCustomers calculation.")

    # --- <<_ปรับปรุงการคำนวณ NewCustomers ที่นี่_>> ---
    # data["newCustomers"] = (
    #     monthly_data.iloc[-1]["DueDate"] # ค่าเดิมคือ DueDate_nunique
    #     if not monthly_data.empty and "DueDate" in monthly_data.columns
    #     else 0
    # )
    # ถ้าคุณเพิ่ม "UniqueCustomers" หรือ "NewCustomersInMonth" ใน monthly_data:
    data["newCustomers"] = (
         monthly_data.iloc[-1].get("NewCustomersInMonth", monthly_data.iloc[-1].get("DueDate", 0)) # ใช้ค่า UniqueCustomers ถ้ามี, fallback ไป DueDate_nunique
         if not monthly_data.empty else 0
    )
    logging.info(f"Calculated newCustomers: {data['newCustomers']}")
    # ---------------------------------------------

    data["newCustomersTrend"] = 0.15
    data["cashFlow"] = data["netProfit"]
    data["cashFlowTrend"] = data["netProfitTrend"]

    # (ส่วนที่เหลือของ calculate_dashboard_data และ API Endpoints เหมือนเดิม)
    # ... (คัดลอกส่วนที่เหลือจากโค้ดเดิมของคุณมาใส่ต่อได้เลย) ...
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    if (
        "DueDate" in df_input.columns
        and pd.api.types.is_datetime64_any_dtype(df_input["DueDate"])
        and "TotalPrice" in df_input.columns
    ):
        monthly_revenue = df_input.groupby(df_input["DueDate"].dt.strftime("%b"))[
            "TotalPrice"
        ].sum()
        # ถ้า netProfit คำนวณจาก Cost จริง ควรปรับ monthly_profit ให้สอดคล้อง
        monthly_profit_series_base = df_input.groupby(df_input["DueDate"].dt.strftime("%b"))["TotalPrice"].sum()
        if "Cost" in df_input.columns:
            monthly_cost_series = df_input.groupby(df_input["DueDate"].dt.strftime("%b"))["Cost"].sum()
            monthly_profit = monthly_profit_series_base.subtract(monthly_cost_series, fill_value=0)
        else:
            monthly_profit = monthly_profit_series_base * 0.2

        monthly_expenses = ( # Expenses อาจจะหมายถึง Cost หรือส่วนที่เหลือจาก Profit
            df_input.groupby(df_input["DueDate"].dt.strftime("%b"))["Cost"].sum()
            if "Cost" in df_input.columns else monthly_profit_series_base * 0.8 # ถ้าไม่มี Cost ก็ใช้แบบเดิม
        )
    else:
        empty_series = pd.Series(index=months, dtype="float64").fillna(0)
        monthly_revenue = empty_series.copy()
        monthly_profit = empty_series.copy()
        monthly_expenses = empty_series.copy()
        logging.warning(
            "Could not generate monthly chart data due to missing 'DueDate' (datetime) or 'TotalPrice'."
        )

    data["revenueData"] = {
        "labels": months,
        "values": [monthly_revenue.get(month, 0) for month in months],
        "netProfitValues": [monthly_profit.get(month, 0) for month in months],
    }
    data["expensesData"] = {
        "labels": months,
        "values": [monthly_expenses.get(month, 0) for month in months],
    }
    data["netProfitMargin"] = (
        data["netProfit"] / data["totalRevenue"] if data["totalRevenue"] != 0 else 0
    )
    data["revenueTargetData"] = {
        "labels": months,
        "actual": data["revenueData"]["values"],
        "target": [value * 1.2 for value in data["revenueData"]["values"]],
    }

    # Metrics อื่นๆ (ถ้ามีข้อมูลจริงจาก Excel ให้แทนที่ random)
    # ตัวอย่าง: ถ้ามีคอลัมน์ "SystemUptime" ใน df_input
    # data["uptime"] = df_input["SystemUptime"].mean() if "SystemUptime" in df_input.columns else random.uniform(99.5, 100)

    data["uptime"] = random.uniform(99.5, 100)
    data["uptimeTrend"] = random.uniform(-0.01, 0.01)
    data["responseTime"] = random.randint(50, 200)
    data["responseTimeTrend"] = random.uniform(-0.1, 0.1)
    data["bugs"] = random.randint(0, 10)
    data["bugsTrend"] = random.uniform(-0.2, 0.2)
    data["deployments"] = random.randint(1, 5)
    data["deploymentsTrend"] = random.uniform(-0.1, 0.1)
    data["uptimeData"] = {"labels": months, "values": [random.uniform(99, 100) for _ in months]}
    data["responseTimeData"] = {"labels": months, "values": [random.randint(50, 200) for _ in months]}
    data["bugCountData"] = {"labels": months, "values": [random.randint(0, 10) for _ in months]}
    data["deploymentFrequencyData"] = {"labels": months, "values": [random.randint(1, 5) for _ in months]}
    return data


dashboard_data = calculate_dashboard_data(df)


# --- API Endpoints (คงเดิม) ---
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
    response = jsonify(
        {
            "value": dashboard_data.get("newCustomers", 0),
            "trend": dashboard_data.get("newCustomersTrend", 0),
        }
    )
    logging.info(f"Response headers for /api/new-customers: {response.headers}")
    return response


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
    app.run(debug=True, port=5000, host="127.0.0.1")