import pandas as pd
import pyodbc
from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
import numpy  # For checking numpy types
import datetime
from werkzeug.security import (
    generate_password_hash,
    check_password_hash,
)  # เพิ่มสำหรับ Password Hashing

app = Flask(__name__)
CORS(app)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(module)s - %(funcName)s - %(message)s",
)
logger = logging.getLogger(__name__)

SERVER = "(LOCAL)"
DATABASE = "db_KRS"
USERNAME = "sa"
PASSWORD = "$kero.SOFT(2020)"  # โปรดระวังการ hardcode password ใน production
DRIVER = "{ODBC Driver 17 for SQL Server}"

month_labels = [
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
default_monthly_data_structure = {
    "labels": month_labels,
    "values": [0.0] * 12,
    "netProfitValues": [0.0] * 12,
}
default_target_data_structure = {
    "labels": month_labels,
    "actual": [0.0] * 12,
    "target": [0.0] * 12,
}
default_simple_monthly_structure = {"labels": month_labels, "values": [0.0] * 12}


def database(table_name_to_load):  # <<< รับ table_name
    cnxn = None
    logger.info(f"Attempting to fetch data from table: {table_name_to_load}")

    # >>> สำคัญ: ตรวจสอบ table_name_to_load ว่าปลอดภัยและมีอยู่จริง (อาจใช้ get_allowed_tables_from_db()) <<<
    allowed_tables = get_allowed_tables_from_db()  # สมมติว่าคุณมีฟังก์ชันนี้แล้ว
    if table_name_to_load not in allowed_tables:
        logger.error(
            f"Attempt to load non-allowed or non-existent table for main dashboard: {table_name_to_load}"
        )
        # คืน DataFrame ว่างที่มีโครงสร้างคอลัมน์ที่คาดหวังโดย calculate_dashboard_data
        # หรือจัดการ error ตามความเหมาะสม
        return pd.DataFrame(
            columns=[  # ใส่คอลัมน์ที่ calculate_dashboard_data คาดหวัง
                "RowOrder",
                "TransactionNo",
                "Number",
                "ItemCode",
                "ItemSubNo",
                "Description",
                "OEMNo",
                "Model",
                "OrderType",
                "PRNo",
                "PRTrNo",
                "DueDate",
                "MainQuantity",
                "MainUnitPrice",
                "TotalPrice",
                "DiNo",
                "QtyReceive",
                "Cost",
                "DiscountAmount",
                "ActualFinancialDate",
                "OrderMonth",
                "CustomerID",
                "KPI_MainQuantity",
                "KPI_QtyReceive",
                "KPI_DiscountAmount",
                "KpiQtyOrderDate",
                "KpiQtyReceiveDate",
                "KpiDiscountDate",
            ]
        )

    query = ""  # เคลียร์ query เก่า
    try:
        cnxn_str = (
            f"DRIVER={DRIVER};SERVER={SERVER};DATABASE={DATABASE};"
            f"UID={USERNAME};PWD={PASSWORD};TrustServerCertificate=yes;"
        )
        cnxn = pyodbc.connect(cnxn_str)

        # >>> สร้าง SQL Query แบบไดนามิก <<<
        # !!! คำเตือน: ส่วนนี้ยังคงคาดหวังว่าตารางที่เลือกจะมีคอลัมน์คล้าย PurchaseOrderDtl !!!
        # คุณอาจจะต้องปรับ SELECT list นี้ให้ยืดหยุ่น หรือมีเงื่อนไขตาม table_name_to_load
        # หรือทำให้แน่ใจว่าตารางที่คุณอนุญาตให้ใช้กับ Dashboard นี้มีคอลัมน์เหล่านี้จริงๆ
        safe_table_sql = f"[{table_name_to_load.replace(']', ']]')}]"
        query = f"""
        SELECT 
            RowOrder, TransactionNo, Number, ItemCode, ItemSubCode AS ItemSubNo, Description,
            OEMNo, Model, OrderType, PRNo, PRTrNo, DueDate, MainQuantity, MainUnitPrice,
            TotalPrice, DiNo, QtyReceive 
            /* คุณอาจจะต้องปรับคอลัมน์เหล่านี้ให้ตรงกับตารางที่เลือก 
                หรือทำให้แน่ใจว่าตารางที่เลือกมีคอลัมน์เหล่านี้ครบถ้วน
                ตัวอย่างเช่น ถ้า SalesOrderHdr ไม่มี PRNo, PRTrNo จะเกิด Error
            */
        FROM {safe_table_sql}
        ORDER BY TransactionNo DESC, RowOrder 
        """
        # ถ้าตารางอื่นไม่มี TransactionNo หรือ RowOrder ก็ต้องปรับ ORDER BY ด้วย

        logger.info(f"Executing SQL query for main data: \n{query[:500]}...")
        df = pd.read_sql(query, cnxn)
        logger.info(f"Data fetched for {table_name_to_load}. Shape: {df.shape}.")

        if df.empty:
            logger.warning(
                f"DB returned empty DataFrame for table {table_name_to_load}."
            )
            # คืน DataFrame ว่างที่มีโครงสร้างคอลัมน์ที่คาดหวัง
            return pd.DataFrame(
                columns=[
                    "RowOrder",
                    "TransactionNo",
                    "Number",
                    "ItemCode",
                    "ItemSubNo",
                    "Description",
                    "OEMNo",
                    "Model",
                    "OrderType",
                    "PRNo",
                    "PRTrNo",
                    "DueDate",
                    "MainQuantity",
                    "MainUnitPrice",
                    "TotalPrice",
                    "DiNo",
                    "QtyReceive",
                    # เพิ่มคอลัมน์อื่นๆ ที่จะถูกสร้างในขั้นตอน preprocessing ด้านล่าง
                ]
            )

        # --- Preprocessing (ส่วนนี้ยังคงผูกกับโครงสร้างคอลัมน์แบบ PurchaseOrderDtl มาก) ---
        # คุณจะต้องปรับแก้ส่วนนี้อย่างมาก หากโครงสร้างตารางที่เลือกแตกต่างกัน
        if "TotalPrice" in df.columns:
            df["TotalPrice"] = pd.to_numeric(df["TotalPrice"], errors="coerce").fillna(
                0
            )
        elif "MainQuantity" in df.columns and "MainUnitPrice" in df.columns:
            df["TotalPrice"] = pd.to_numeric(
                df["MainQuantity"], errors="coerce"
            ).fillna(0) * pd.to_numeric(df["MainUnitPrice"], errors="coerce").fillna(0)
        else:
            df["TotalPrice"] = 0.0  # หรือจัดการ error
            logger.warning(
                f"Cannot determine 'TotalPrice' for {table_name_to_load}. Setting to 0.0."
            )

        # สมมติว่า 'Cost' มาจาก 'PRNo' (นี่เป็น Logic เฉพาะของคุณ)
        # ถ้าตารางอื่นไม่มี PRNo หรือ Cost มีความหมายอื่น ต้องปรับ
        df["Cost"] = pd.to_numeric(df.get("PRNo", default=0), errors="coerce").fillna(0)
        df["DiscountAmount"] = 0.0  # สมมติ

        if "QtyReceive" in df.columns:
            df["QtyReceive"] = pd.to_numeric(df["QtyReceive"], errors="coerce").fillna(
                0
            )
        else:
            df["QtyReceive"] = 0.0

        financial_date_col = "DueDate"  # ตรวจสอบว่าตารางที่เลือกมีคอลัมน์นี้หรือไม่
        if (
            financial_date_col in df.columns
            and not df[financial_date_col].isnull().all()
        ):
            df["ActualFinancialDate"] = pd.to_datetime(
                df[financial_date_col], errors="coerce"
            )
            df["OrderMonth"] = (
                df["ActualFinancialDate"]
                .dt.to_period("M")
                .where(df["ActualFinancialDate"].notna())
            )
        else:
            df["ActualFinancialDate"] = pd.NaT
            df["OrderMonth"] = pd.Series(dtype="period[M]", index=df.index).fillna(
                pd.NaT
            )
            logger.warning(
                f"Date column '{financial_date_col}' not found or all null in {table_name_to_load}."
            )

        # คอลัมน์เหล่านี้ถูกใช้ใน calculate_dashboard_data และ get_products/get_stock_history
        # ตรวจสอบว่าตารางที่เลือกสามารถให้ข้อมูลเหล่านี้ได้
        df["CustomerID"] = (
            df["TransactionNo"] if "TransactionNo" in df.columns else None
        )
        df["KPI_MainQuantity"] = pd.to_numeric(
            df.get("MainQuantity", 0), errors="coerce"
        ).fillna(0)
        df["KPI_QtyReceive"] = pd.to_numeric(
            df.get("QtyReceive", 0), errors="coerce"
        ).fillna(0)
        df["KPI_DiscountAmount"] = pd.to_numeric(
            df.get("DiscountAmount", 0), errors="coerce"
        ).fillna(0)
        df["KpiQtyOrderDate"] = df["ActualFinancialDate"]
        df["KpiQtyReceiveDate"] = df["ActualFinancialDate"]
        df["KpiDiscountDate"] = df["ActualFinancialDate"]
        # เพิ่มคอลัมน์ที่ Product Management API Endpoint คาดหวัง เช่น ItemSubNo, OEMNo, Model
        # ถ้าไม่มีในตารางที่เลือก อาจจะต้องใส่ค่า default หรือ None
        for col in [
            "ItemSubNo",
            "OEMNo",
            "Model",
            "Description",
            "MainUnitPrice",
            "MainUnits",
        ]:
            if col not in df.columns:
                df[col] = None if col != "Description" else "N/A"  # หรือค่า default อื่นๆ

        logger.info(f"DB data preprocessing complete for table {table_name_to_load}.")
        return df

    except pyodbc.Error as db_err:
        logger.error(f"PYODBC Database Error in database(): {db_err}", exc_info=True)
        query_to_log = query if "query" in locals() and query else "Query not defined."
        logger.error(f"Problematic SQL Query was: \n{query_to_log}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"General Error in database(): {e}", exc_info=True)
        query_to_log = query if "query" in locals() and query else "Query not defined."
        logger.error(f"Problematic SQL Query (if defined) was: \n{query_to_log}")
        return pd.DataFrame()
    finally:
        if cnxn:
            logger.info("Closing SQL Server connection.")
            cnxn.close()


CURRENT_DASHBOARD_TABLE_NAME = "PurchaseOrderDtl"  # <<< ตั้งค่าเริ่มต้นเป็นตารางเดิม
df_main_data = pd.DataFrame()  # <<< ประกาศเป็น DataFrame ว่างไว้ก่อน
dashboard_data = {}  # <<< ประกาศเป็น dict ว่างไว้ก่อน


def load_initial_dashboard_data():
    global df_main_data, dashboard_data, CURRENT_DASHBOARD_TABLE_NAME
    logger.info(
        f"Loading initial dashboard data for table: {CURRENT_DASHBOARD_TABLE_NAME}"
    )
    df_main_data = database(CURRENT_DASHBOARD_TABLE_NAME)
    if df_main_data.empty:
        logger.error(
            f"Failed to load initial data for {CURRENT_DASHBOARD_TABLE_NAME}. Dashboard will be empty or show defaults."
        )
        # สร้าง df_main_data และ dashboard_data ที่มีโครงสร้าง default เพื่อไม่ให้ API อื่นๆ พัง
        # (อาจจะเหมือนกับที่ทำในกรณี df_main_data.empty ในโค้ดเดิมของคุณ)
    dashboard_data = calculate_dashboard_data(
        df_main_data.copy(), CURRENT_DASHBOARD_TABLE_NAME
    )
    logger.info("Initial dashboard data loaded and calculated.")


if df_main_data.empty:
    logger.warning("Global DataFrame 'df_main_data' is empty after database call.")
    expected_cols_global = [
        "RowOrder",
        "TransactionNo",
        "Number",
        "ItemCode",
        "ItemSubNo",
        "Description",
        "OEMNo",
        "Model",
        "OrderType",
        "PRNo",
        "PRTrNo",
        "DueDate",
        "MainQuantity",
        "MainUnitPrice",
        "TotalPrice",
        "DiNo",
        "QtyReceive",
        "Cost",
        "DiscountAmount",
        "ActualFinancialDate",
        "OrderMonth",
        "CustomerID",
        "KPI_MainQuantity",
        "KPI_QtyReceive",
        "KPI_DiscountAmount",
        "KpiQtyOrderDate",
        "KpiQtyReceiveDate",
        "KpiDiscountDate",
    ]
    df_data_empty = {}
    for col_name in expected_cols_global:
        if "Date" in col_name or "Month" in col_name:
            df_data_empty[col_name] = pd.Series(
                dtype="datetime64[ns]" if col_name != "OrderMonth" else "period[M]"
            )
        elif col_name in [
            "Description",
            "OEMNo",
            "Model",
            "OrderType",
            "PRNo",
            "PRTrNo",
            "DiNo",
            "ItemCode",
            "ItemSubNo",
            "TransactionNo",
            "CustomerID",
        ]:
            df_data_empty[col_name] = pd.Series(dtype="object")
        else:
            df_data_empty[col_name] = pd.Series(dtype="float64")
    df_main_data = pd.DataFrame(df_data_empty)
    for col_fill in df_main_data.columns:
        if df_main_data[col_fill].dtype == "float64":
            df_main_data[col_fill] = df_main_data[col_fill].fillna(0.0)
        elif pd.api.types.is_datetime64_any_dtype(
            df_main_data[col_fill].dtype
        ) or pd.api.types.is_period_dtype(df_main_data[col_fill].dtype):
            df_main_data[col_fill] = pd.NaT
else:
    logger.info(
        f"Global DataFrame 'df_main_data' loaded. Shape: {df_main_data.shape}. Columns: {df_main_data.columns.tolist()}"
    )


def ensure_native_types_in_list(data_list):
    if not isinstance(data_list, list):
        if isinstance(data_list, pd.Series):
            data_list = data_list.tolist()
        else:
            return []
    native_list = []
    for item in data_list:
        if pd.isna(item):
            native_list.append(None)
        elif isinstance(item, (numpy.floating, float)):
            native_list.append(float(item))
        elif isinstance(item, (numpy.integer, int)):
            native_list.append(int(item))
        elif isinstance(item, pd.Timestamp):
            native_list.append(item.isoformat())
        elif isinstance(item, pd.Period):
            native_list.append(str(item))
        else:
            native_list.append(item)
    return native_list


def calculate_dashboard_data(df_input, source_table_name="N/A"):
    logger.info(
        f"Calculating dashboard data for table '{source_table_name}' with input shape: {df_input.shape}"
    )
    data = {"totalRevenue": 0.0, "netProfit": 0.0, "newCustomers": 0}

    if not df_input.empty:
        data["totalRevenue"] = float(
            df_input.get("TotalPrice", pd.Series(0.0, dtype="float64")).sum()
        )
        data["netProfit"] = float(
            data["totalRevenue"]
            - df_input.get("Cost", pd.Series(0.0, dtype="float64")).sum()
        )
        data["newCustomers"] = int(
            df_input.get("CustomerID", pd.Series(dtype="object")).nunique()
        )
        data["totalquantityordered"] = float(
            df_input.get("KPI_MainQuantity", pd.Series(0.0, dtype="float64")).sum()
        )
        data["totalquantityreceived"] = float(
            df_input.get("KPI_QtyReceive", pd.Series(0.0, dtype="float64")).sum()
        )
        data["averagediscount"] = 0.0

    chart_keys_monthly = [
        "revenueData",
        "quantityOrderedData",
        "quantityReceivedData",
        "avgDiscountData",
    ]
    chart_keys_simple = ["expensesData"]
    for key in chart_keys_monthly:
        data[key] = (
            default_monthly_data_structure.copy()
            if key == "revenueData"
            else default_simple_monthly_structure.copy()
        )
    for key in chart_keys_simple:
        data[key] = default_simple_monthly_structure.copy()
    data["revenueTargetData"] = default_target_data_structure.copy()

    trends = [
        "totalRevenueTrend",
        "netProfitTrend",
        "newCustomersTrend",
        "totalquantityorderedTrend",
        "totalquantityreceivedTrend",
        "averagediscountTrend",
    ]
    for trend_key in trends:
        data[trend_key] = 0.0

    if (
        not df_input.empty
        and "OrderMonth" in df_input.columns
        and df_input["OrderMonth"].notna().any()
    ):
        df_input_charts = df_input[df_input["OrderMonth"].notna()].copy()
        if not df_input_charts.empty:
            df_input_charts["MonthStr"] = df_input_charts["OrderMonth"].dt.strftime(
                "%b"
            )

            if "TotalPrice" in df_input_charts.columns:
                monthly_revenue_series = (
                    df_input_charts.groupby("MonthStr")["TotalPrice"]
                    .sum()
                    .reindex(month_labels, fill_value=0.0)
                )
                data["revenueData"]["values"] = ensure_native_types_in_list(
                    monthly_revenue_series
                )
                # logger.info(f"Chart - Monthly Revenue: {data['revenueData']['values']}")

                if "Cost" in df_input_charts.columns:
                    monthly_expenses_series = (
                        df_input_charts.groupby("MonthStr")["Cost"]
                        .sum()
                        .reindex(month_labels, fill_value=0.0)
                    )
                    data["expensesData"]["values"] = ensure_native_types_in_list(
                        monthly_expenses_series
                    )
                    # logger.info(f"Chart - Monthly Expenses: {data['expensesData']['values']}")

                    monthly_profit_series = (
                        monthly_revenue_series - monthly_expenses_series
                    )
                    data["revenueData"]["netProfitValues"] = (
                        ensure_native_types_in_list(monthly_profit_series)
                    )
                    # logger.info(f"Chart - Monthly Net Profit: {data['revenueData']['netProfitValues']}")
                else:
                    data["revenueData"]["netProfitValues"] = data["revenueData"][
                        "values"
                    ][:]
                    data["expensesData"]["values"] = [0.0] * 12
                    # logger.info("Chart - Cost column missing, NetProfit for chart equals Revenue, Expenses are 0.")
            # else: logger.warning("Chart - TotalPrice column missing...")

            data["revenueTargetData"]["actual"] = data["revenueData"]["values"]
            data["revenueTargetData"]["target"] = [
                round(v * 1.2, 2) if isinstance(v, (int, float)) else 0.0
                for v in data["revenueData"]["values"]
            ]

            if "KPI_MainQuantity" in df_input_charts.columns:
                monthly_qty_ordered_series = (
                    df_input_charts.groupby("MonthStr")["KPI_MainQuantity"]
                    .sum()
                    .reindex(month_labels, fill_value=0.0)
                )
                data["quantityOrderedData"]["values"] = ensure_native_types_in_list(
                    monthly_qty_ordered_series
                )
                # logger.info(f"Chart - Monthly Qty Ordered: {data['quantityOrderedData']['values']}")

            if "KPI_QtyReceive" in df_input_charts.columns:
                monthly_qty_received_series = (
                    df_input_charts.groupby("MonthStr")["KPI_QtyReceive"]
                    .sum()
                    .reindex(month_labels, fill_value=0.0)
                )
                data["quantityReceivedData"]["values"] = ensure_native_types_in_list(
                    monthly_qty_received_series
                )
                # logger.info(f"Chart - Monthly Qty Received: {data['quantityReceivedData']['values']}")

            data["avgDiscountData"]["values"] = [0.0] * 12
            # logger.info(f"Chart - Monthly Avg Discount (defaulted to 0): {data['avgDiscountData']['values']}")
        else:
            logger.warning(
                "No valid OrderMonth data for chart aggregation after filtering NaT."
            )
    else:
        logger.warning(
            "df_input is empty or OrderMonth column missing/all NaT. Charts will use default empty values."
        )

    logger.info(
        f"Finished calculating dashboard_data: { {k:v for k,v in data.items() if not isinstance(v,dict)} }"
    )
    return data


dashboard_data = calculate_dashboard_data(df_main_data.copy())


def convert_df_for_json(df_to_convert):
    logger.debug(f"Converting DataFrame for JSON. Input shape: {df_to_convert.shape}")

    df_copy = df_to_convert.copy()

    try:
        # For pandas versions that use pd.NA
        if hasattr(pd, "NA"):
            df_copy = df_copy.replace({pd.NA: numpy.nan})
        # Convert all NaNs (which now includes original pd.NA) to None for JSON compatibility
        # and then convert to list of dictionaries
        records = df_copy.where(pd.notnull(df_copy), None).to_dict(orient="records")
    except Exception as e:
        logger.error(f"Error during initial to_dict conversion: {e}", exc_info=True)
        records = []  # Fallback to empty list if conversion fails

    sanitized_records = []
    for record in records:
        sanitized_record = {}
        for key, value in record.items():
            if value is None or pd.isna(value):  # Handles None, NaN, NaT
                sanitized_record[key] = None
            # Check for specific NumPy integer types
            elif isinstance(
                value,
                (
                    numpy.int8,
                    numpy.int16,
                    numpy.int32,
                    numpy.int64,
                    numpy.uint8,
                    numpy.uint16,
                    numpy.uint32,
                    numpy.uint64,
                ),
            ):
                sanitized_record[key] = int(value)
            # Check for specific NumPy float types (avoiding deprecated np.float, np.floating)
            elif isinstance(value, (numpy.float16, numpy.float32, numpy.float64)):
                sanitized_record[key] = float(value)
            # Check for NumPy boolean type (np.bool_ is the correct type)
            elif isinstance(value, numpy.bool_):
                sanitized_record[key] = bool(value)
            # Check for Python's native boolean, just in case (though usually not an issue for JSON)
            elif isinstance(value, bool):
                sanitized_record[key] = value
            elif isinstance(value, pd.Timestamp):
                sanitized_record[key] = value.isoformat()
            elif isinstance(value, pd.Period):
                sanitized_record[key] = str(value)
            elif isinstance(
                value, (datetime.date, datetime.datetime)
            ):  # Python's native date/datetime
                sanitized_record[key] = value.isoformat()
            else:
                sanitized_record[key] = value
        sanitized_records.append(sanitized_record)

    logger.debug(
        f"Finished converting DataFrame to JSON-friendly list of dicts. Record count: {len(sanitized_records)}"
    )
    return sanitized_records


# --- ฟังก์ชัน Helper ใหม่ (หรือปรับปรุง) ---
def get_allowed_tables_from_db():  # เปลี่ยนชื่อเล็กน้อยเพื่อความชัดเจน
    cnxn = None
    cursor = None
    allowed_tables = []
    try:
        cnxn_str = (
            f"DRIVER={DRIVER};SERVER={SERVER};DATABASE={DATABASE};"
            f"UID={USERNAME};PWD={PASSWORD};TrustServerCertificate=yes;"
        )
        cnxn = pyodbc.connect(cnxn_str)
        cursor = cnxn.cursor()
        query = "SELECT table_name FROM information_schema.tables WHERE table_type = 'BASE TABLE' AND table_catalog = ? ORDER BY table_name"
        cursor.execute(query, DATABASE)
        allowed_tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"Fetched allowed tables for validation: {allowed_tables}")
    except pyodbc.Error as db_err:
        logger.error(f"DB Error in get_allowed_tables_from_db: {db_err}", exc_info=True)
    except Exception as e:
        logger.error(f"General Error in get_allowed_tables_from_db: {e}", exc_info=True)
    finally:
        if cursor:
            cursor.close()
        if cnxn:
            cnxn.close()
    return allowed_tables


# --- API Endpoints ---
@app.route("/api/total-revenue", methods=["GET"])
def get_total_revenue():
    return jsonify(
        {
            "value": dashboard_data.get("totalRevenue", 0.0),
            "trend": dashboard_data.get("totalRevenueTrend", 0.0),
        }
    )


# ... (โค้ด API endpoints อื่นๆ ของคุณเหมือนเดิม) ...
@app.route("/api/net-profit", methods=["GET"])
def get_net_profit():
    return jsonify(
        {
            "value": dashboard_data.get("netProfit", 0.0),
            "trend": dashboard_data.get("netProfitTrend", 0.0),
        }
    )


@app.route("/api/new-customers", methods=["GET"])
def get_new_customers():
    return jsonify(
        {
            "value": dashboard_data.get("newCustomers", 0),
            "trend": dashboard_data.get("newCustomersTrend", 0.0),
        }
    )


@app.route("/api/total-quantity-ordered", methods=["GET"])
def get_total_quantity_ordered():
    return jsonify(
        {
            "value": dashboard_data.get("totalquantityordered", 0.0),
            "trend": dashboard_data.get("totalquantityorderedTrend", 0.0),
        }
    )


@app.route("/api/total-quantity-received", methods=["GET"])
def get_total_quantity_received():
    return jsonify(
        {
            "value": dashboard_data.get("totalquantityreceived", 0.0),
            "trend": dashboard_data.get("totalquantityreceivedTrend", 0.0),
        }
    )


@app.route("/api/average-discount", methods=["GET"])
def get_average_discount():
    return jsonify(
        {
            "value": dashboard_data.get("averagediscount", 0.0),
            "trend": dashboard_data.get("averagediscountTrend", 0.0),
        }
    )


@app.route("/api/revenue-data", methods=["GET"])
def get_revenue_data():
    return jsonify(
        dashboard_data.get("revenueData", default_monthly_data_structure.copy())
    )


@app.route("/api/expenses-data", methods=["GET"])
def get_expenses_data():
    return jsonify(
        dashboard_data.get("expensesData", default_simple_monthly_structure.copy())
    )


@app.route("/api/revenue-target-data", methods=["GET"])
def get_revenue_target_data():
    return jsonify(
        dashboard_data.get("revenueTargetData", default_target_data_structure.copy())
    )


@app.route("/api/quantity-ordered-data", methods=["GET"])
def get_quantity_ordered_data():
    return jsonify(
        dashboard_data.get(
            "quantityOrderedData", default_simple_monthly_structure.copy()
        )
    )


@app.route("/api/quantity-received-data", methods=["GET"])
def get_quantity_received_data():
    return jsonify(
        dashboard_data.get(
            "quantityReceivedData", default_simple_monthly_structure.copy()
        )
    )


@app.route("/api/average-discount-data", methods=["GET"])
def get_average_discount_data():
    return jsonify(
        dashboard_data.get("avgDiscountData", default_simple_monthly_structure.copy())
    )


@app.route("/api/products", methods=["GET"])
def get_products():
    logger.info("API call to /api/products")
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        search_term = request.args.get("search", "", type=str).lower()

        if df_main_data.empty or "ItemCode" not in df_main_data.columns:
            return jsonify(
                {
                    "data": [],
                    "total": 0,
                    "page": page,
                    "per_page": per_page,
                    "error": "Product data not available.",
                }
            ), 500

        df_products_source = df_main_data.copy()
        df_products_source["EffectiveProductName"] = df_products_source.get(
            "Description", pd.Series(dtype="object")
        ).fillna("N/A")

        product_display_cols_map = {
            "ItemCode": "ItemCode",
            "ProductName": "EffectiveProductName",
            "Description": "Description",
            "Category": None,
            "Price": "MainUnitPrice",
            "Unit": "MainUnits",
            "OEMNo": "OEMNo",
            "Model": "Model",
            "ItemSubNo": "ItemSubNo",
        }
        df_products_view = pd.DataFrame()
        for display_col, source_col in product_display_cols_map.items():
            if source_col and source_col in df_products_source.columns:
                df_products_view[display_col] = df_products_source[source_col]
            else:
                df_products_view[display_col] = None

        if (
            "ItemCode" in df_products_view.columns
            and "MainQuantity" in df_main_data.columns
        ):
            stock_summary = (
                df_main_data.groupby("ItemCode")["MainQuantity"]
                .sum()
                .reset_index()
                .rename(columns={"MainQuantity": "CalculatedStock"})
            )
            df_products_view = pd.merge(
                df_products_view, stock_summary, on="ItemCode", how="left"
            )
            df_products_view["Stock"] = df_products_view["CalculatedStock"].fillna(0)
        else:
            df_products_view["Stock"] = 0
        df_products_view["Status"] = "Active"

        if (
            search_term
            and not df_products_view.empty
            and all(c in df_products_view.columns for c in ["ProductName", "ItemCode"])
        ):
            df_products_view = df_products_view[
                df_products_view["ProductName"]
                .astype(str)
                .str.lower()
                .fillna("")
                .str.contains(search_term)
                | df_products_view["ItemCode"]
                .astype(str)
                .str.lower()
                .fillna("")
                .str.contains(search_term)
            ]

        if not df_products_view.empty and "ItemCode" in df_products_view.columns:
            df_products_view.drop_duplicates(
                subset=["ItemCode"], keep="first", inplace=True
            )

        total_items = len(df_products_view)
        paginated_df = df_products_view.iloc[(page - 1) * per_page : page * per_page]
        products_list = convert_df_for_json(paginated_df)

        return jsonify(
            {
                "data": products_list,
                "total": total_items,
                "page": page,
                "per_page": per_page,
            }
        )
    except Exception as e:
        logger.error(f"Error in /api/products: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/stock-history", methods=["GET"])
def get_stock_history():
    logger.info("API call to /api/stock-history")
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        search_term = request.args.get("search", "", type=str).lower()

        if df_main_data.empty:
            return jsonify(
                {
                    "data": [],
                    "total": 0,
                    "page": page,
                    "per_page": per_page,
                    "error": "Stock history data not available.",
                }
            ), 500

        df_history_source = df_main_data.copy()
        df_history_source["EffectiveProductName"] = df_history_source.get(
            "Description", pd.Series(dtype="object")
        ).fillna("N/A")
        df_history_source.rename(columns={"DueDate": "Timestamp"}, inplace=True)

        all_movements = []
        if (
            "MainQuantity" in df_history_source.columns
            and (df_history_source["MainQuantity"] != 0).any()
        ):
            df_ordered = df_history_source[
                df_history_source["MainQuantity"] != 0
            ].copy()
            if not df_ordered.empty:
                df_ordered["MovementType"] = "Ordered/Adjust"
                df_ordered["QuantityChange"] = df_ordered["MainQuantity"]
                all_movements.append(df_ordered)

        if (
            "QtyReceive" in df_history_source.columns
            and (df_history_source["QtyReceive"] != 0).any()
            and (
                not df_history_source["MainQuantity"].equals(
                    df_history_source["QtyReceive"]
                )
            )
        ):
            df_received = df_history_source[df_history_source["QtyReceive"] != 0].copy()
            if not df_received.empty:
                df_received["MovementType"] = "Received"
                df_received["QuantityChange"] = df_received["QtyReceive"]
                all_movements.append(df_received)

        df_history_final = (
            pd.concat(all_movements, ignore_index=True)
            if all_movements
            else pd.DataFrame(
                columns=[
                    "Timestamp",
                    "ItemCode",
                    "EffectiveProductName",
                    "MovementType",
                    "QuantityChange",
                    "TransactionNo",
                ]
            )
        )
        df_history_final.rename(
            columns={
                "ItemCode": "ProductIdentifier",
                "EffectiveProductName": "ProductName",
                "TransactionNo": "Reference",
            },
            inplace=True,
            errors="ignore",
        )

        cols_to_keep_history = [
            "Timestamp",
            "ProductIdentifier",
            "ProductName",
            "MovementType",
            "QuantityChange",
            "Reference",
        ]
        for col in cols_to_keep_history:
            if col not in df_history_final.columns:
                df_history_final[col] = None
        df_history_final = df_history_final[cols_to_keep_history]
        df_history_final["BalanceAfter"] = "N/A"

        if "Timestamp" in df_history_final.columns and not df_history_final.empty:
            df_history_final["Timestamp"] = pd.to_datetime(
                df_history_final["Timestamp"], errors="coerce"
            )
            df_history_final.sort_values(
                by="Timestamp", ascending=False, inplace=True, na_position="last"
            )

        if (
            search_term
            and not df_history_final.empty
            and all(
                c in df_history_final.columns
                for c in ["ProductName", "ProductIdentifier", "Reference"]
            )
        ):
            df_history_final = df_history_final[
                df_history_final["ProductName"]
                .astype(str)
                .str.lower()
                .fillna("")
                .str.contains(search_term)
                | df_history_final["ProductIdentifier"]
                .astype(str)
                .str.lower()
                .fillna("")
                .str.contains(search_term)
                | df_history_final["Reference"]
                .astype(str)
                .str.lower()
                .fillna("")
                .str.contains(search_term)
            ]

        total_items = len(df_history_final)
        paginated_df = df_history_final.iloc[(page - 1) * per_page : page * per_page]
        history_list = convert_df_for_json(paginated_df)

        return jsonify(
            {
                "data": history_list,
                "total": total_items,
                "page": page,
                "per_page": per_page,
            }
        )
    except Exception as e:
        logger.error(f"Error in /api/stock-history: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# --- API Endpoints ใหม่ สำหรับการเลือกตาราง ---
@app.route("/api/database/tables", methods=["GET"])
def get_database_tables():
    cnxn = None
    cursor = None
    tables = []
    try:
        cnxn_str = (
            f"DRIVER={DRIVER};SERVER={SERVER};DATABASE={DATABASE};"
            f"UID={USERNAME};PWD={PASSWORD};TrustServerCertificate=yes;"
        )
        cnxn = pyodbc.connect(cnxn_str)
        cursor = cnxn.cursor()
        query = "SELECT table_name FROM information_schema.tables WHERE table_type = 'BASE TABLE' AND table_catalog = ? ORDER BY table_name"
        cursor.execute(query, DATABASE)
        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"API: Fetched available tables: {tables}")
        return jsonify(tables), 200
    except pyodbc.Error as db_err:
        logger.error(f"API: Error fetching table list: {db_err}", exc_info=True)
        return jsonify({"error": "Could not fetch table list from database."}), 500
    except Exception as e:
        logger.error(f"API: General error fetching table list: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred."}), 500
    finally:
        if cursor:
            cursor.close()
        if cnxn:
            cnxn.close()


@app.route("/api/database/table/<string:table_name>", methods=["GET"])
def get_table_data_from_selected_table(table_name):  # เปลี่ยนชื่อฟังก์ชันเล็กน้อยเพื่อไม่ให้ซ้ำกับ JS
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    allowed_tables = get_allowed_tables_from_db()  # เรียกใช้ helper function
    if not allowed_tables:  # กรณี helper function มีปัญหาในการดึง list
        logger.error("API: Allowed table list is empty. Cannot validate table name.")
        return jsonify(
            {"error": "Server configuration error: Could not validate table."}
        ), 500

    if table_name not in allowed_tables:
        logger.warning(f"API: Attempt to access non-allowed table: {table_name}")
        return jsonify(
            {"error": f"Table '{table_name}' not found or access denied."}
        ), 404

    cnxn = None
    try:
        cnxn_str = (
            f"DRIVER={DRIVER};SERVER={SERVER};DATABASE={DATABASE};"
            f"UID={USERNAME};PWD={PASSWORD};TrustServerCertificate=yes;"
        )
        cnxn = pyodbc.connect(cnxn_str)

        safe_table_name_sql = (
            f"[{table_name.replace(']', ']]')}]"  # Escaping for SQL Server
        )

        count_query = f"SELECT COUNT(*) FROM {safe_table_name_sql}"
        df_count = pd.read_sql(count_query, cnxn)
        total_items = (
            int(df_count.iloc[0, 0])
            if not df_count.empty and df_count.iloc[0, 0] is not None
            else 0
        )

        offset = (page - 1) * per_page
        query = f"""
            SELECT *
            FROM {safe_table_name_sql}
            ORDER BY (SELECT NULL) 
            OFFSET ? ROWS
            FETCH NEXT ? ROWS ONLY;
        """
        logger.info(
            f"API: Executing query for table {safe_table_name_sql} with offset {offset}, limit {per_page}"
        )
        df_table = pd.read_sql(query, cnxn, params=[offset, per_page])

        # ใช้ฟังก์ชัน convert_df_for_json เดิมของคุณ
        table_data_json = convert_df_for_json(df_table)

        return jsonify(
            {
                "data": table_data_json,
                "columns": list(df_table.columns),
                "total": total_items,
                "page": page,
                "per_page": per_page,
                "table_name": table_name,
            }
        ), 200
    except pyodbc.Error as db_err:
        logger.error(
            f"API: DB Error fetching data for table '{table_name}': {db_err}",
            exc_info=True,
        )
        return jsonify(
            {"error": f"Database error fetching data for table '{table_name}'."}
        ), 500
    except Exception as e:
        logger.error(
            f"API: General error fetching data for table '{table_name}': {e}",
            exc_info=True,
        )
        return jsonify(
            {"error": "An unexpected error occurred fetching table data."}
        ), 500
    finally:
        if cnxn:
            cnxn.close()


# --- NEW: PRODUCT MANAGEMENT API ENDPOINTS (Update & Delete) ---
@app.route("/api/products/<string:item_code_param>", methods=["PUT"])
def update_product_by_item_code(item_code_param):
    data = request.get_json()
    logger.info(
        f"Attempting to update all PurchaseOrderDtl entries for ItemCode '{item_code_param}' with data: {data}"
    )

    if not data:
        return jsonify({"error": "No data provided for update"}), 400

    allowed_update_fields = {"Description": None, "MainUnitPrice": None}
    update_fields_map = {}
    params_sql = []

    if "Description" in data:
        update_fields_map["Description"] = data["Description"]
    if "MainUnitPrice" in data:
        try:
            update_fields_map["MainUnitPrice"] = float(data["MainUnitPrice"])
        except ValueError:
            return jsonify(
                {"error": "Invalid value for MainUnitPrice. Must be a number."}
            ), 400

    if not update_fields_map:
        return jsonify({"error": "No valid or allowed fields provided for update"}), 400

    set_clauses = [f"{field_db} = ?" for field_db in update_fields_map.keys()]

    for field_db_key in update_fields_map.keys():
        params_sql.append(update_fields_map[field_db_key])
    params_sql.append(item_code_param)

    cnxn = None
    cursor = None
    try:
        cnxn_str = f"DRIVER={DRIVER};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD};TrustServerCertificate=yes;"
        cnxn = pyodbc.connect(cnxn_str)
        cursor = cnxn.cursor()

        sql_update = (
            f"UPDATE PurchaseOrderDtl SET {', '.join(set_clauses)} WHERE ItemCode = ?"
        )
        logger.info(
            f"Executing product update SQL: {sql_update} with params: {params_sql}"
        )

        cursor.execute(sql_update, *params_sql)
        cnxn.commit()

        if cursor.rowcount == 0:
            logger.warning(
                f"No rows found in PurchaseOrderDtl for ItemCode '{item_code_param}' to update."
            )
            return jsonify(
                {"error": f"Product with ItemCode '{item_code_param}' not found."}
            ), 404

        logger.info(
            f"Successfully updated {cursor.rowcount} rows in PurchaseOrderDtl for ItemCode '{item_code_param}'."
        )

        global df_main_data, dashboard_data  # Declare them as global to modify
        df_main_data = database()
        dashboard_data = calculate_dashboard_data(df_main_data.copy())

        return jsonify(
            {"message": f"Product (ItemCode: {item_code_param}) updated successfully."}
        ), 200

    except pyodbc.Error as db_err:
        logger.error(
            f"DB Error updating product (ItemCode: {item_code_param}): {db_err}",
            exc_info=True,
        )
        return jsonify({"error": "Database error updating product"}), 500
    except Exception as e:
        logger.error(
            f"General Error updating product (ItemCode: {item_code_param}): {e}",
            exc_info=True,
        )
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if cnxn:
            cnxn.close()


@app.route("/api/products/<string:item_code_param>", methods=["DELETE"])
def delete_product_by_item_code(item_code_param):
    logger.warning(
        f"!!! DESTRUCTIVE DELETE for all PurchaseOrderDtl entries with ItemCode '{item_code_param}' !!!"
    )
    cnxn = None
    cursor = None
    try:
        cnxn_str = f"DRIVER={DRIVER};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD};TrustServerCertificate=yes;"
        cnxn = pyodbc.connect(cnxn_str)
        cursor = cnxn.cursor()

        sql_delete = "DELETE FROM PurchaseOrderDtl WHERE ItemCode = ?"
        logger.info(
            f"Executing product DELETE SQL: {sql_delete} with ItemCode: {item_code_param}"
        )

        cursor.execute(sql_delete, item_code_param)
        cnxn.commit()

        if cursor.rowcount == 0:
            logger.warning(
                f"No rows found in PurchaseOrderDtl for ItemCode '{item_code_param}' to delete."
            )
            return jsonify(
                {
                    "error": f"Product with ItemCode '{item_code_param}' not found for deletion."
                }
            ), 404

        logger.info(
            f"Successfully DELETED {cursor.rowcount} rows from PurchaseOrderDtl for ItemCode '{item_code_param}'."
        )

        global df_main_data, dashboard_data  # Declare them as global to modify
        df_main_data = database()
        dashboard_data = calculate_dashboard_data(df_main_data.copy())

        return jsonify(
            {
                "message": f"Product (ItemCode: {item_code_param}) and related transactions DELETED."
            }
        ), 200

    except pyodbc.Error as db_err:
        logger.error(
            f"DB Error deleting product (ItemCode: {item_code_param}): {db_err}",
            exc_info=True,
        )
        return jsonify({"error": "Database error deleting product"}), 500
    except Exception as e:
        logger.error(
            f"General Error deleting product (ItemCode: {item_code_param}): {e}",
            exc_info=True,
        )
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if cnxn:
            cnxn.close()


# --- USER MANAGEMENT API ENDPOINTS (Placeholders - WAITING FOR USER TABLE SCHEMA) ---
# @app.route("/api/users", methods=["POST"])
# def create_user():
#     logger.warning("POST /api/users - Not implemented yet. Waiting for User table schema.")
#     return jsonify({"message": "Create user endpoint not implemented"}), 501

# @app.route("/api/users", methods=["GET"])
# def get_users():
#     logger.warning("GET /api/users - Not implemented yet. Waiting for User table schema.")
#     return jsonify({"data": [], "total": 0, "page": 1, "per_page": 10, "message": "Get users endpoint not implemented"}), 501

# @app.route("/api/users/<int:user_id>", methods=["PUT"])
# def update_user(user_id):
#     logger.warning(f"PUT /api/users/{user_id} - Not implemented yet. Waiting for User table schema.")
#     return jsonify({"message": f"Update user {user_id} endpoint not implemented"}), 501

# @app.route("/api/users/<int:user_id>", methods=["DELETE"])
# def delete_user(user_id):
#     logger.warning(f"DELETE /api/users/{user_id} - Not implemented yet. Waiting for User table schema.")
#     return jsonify({"message": f"Delete user {user_id} endpoint not implemented"}), 501


if __name__ == "__main__":
    load_initial_dashboard_data()
    logger.info("Starting Flask application on http://127.0.0.1:5000 ...")
    app.run(debug=True, port=10000, host='0.0.0.0')
else:  # ถ้าไม่ได้รันโดยตรง (เช่น ถูก import) ก็ควรจะโหลดข้อมูลเริ่มต้นเช่นกัน
    load_initial_dashboard_data()
