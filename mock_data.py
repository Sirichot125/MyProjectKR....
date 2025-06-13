import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def create_mock_data():
    # สร้างวันที่ย้อนหลัง 12 เดือน
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    dates = pd.date_range(start=start_date, end=end_date, freq="D")

    # สร้างข้อมูล
    data = []
    for date in dates:
        num_orders = np.random.randint(3, 9)
        for _ in range(num_orders):
            data.append(
                {
                    "OrderDate": date,
                    "CustomerID": f"CUST{np.random.randint(1, 101):03d}",
                    "ProductID": f"PROD{np.random.randint(1, 6):03d}",
                    "Quantity": np.random.randint(1, 21),
                    "UnitPrice": np.random.choice([100, 200, 300, 400, 500]),
                }
            )

    df = pd.DataFrame(data)
    df["TotalPrice"] = df["Quantity"] * df["UnitPrice"]
    df["Cost"] = df["TotalPrice"] * 0.7  # ต้นทุน 70%
    return df


def calculate_dashboard_metrics(df):
    # คำนวณตัวเลขสรุป
    metrics = {
        "Total Revenue": df["TotalPrice"].sum(),
        "Net Profit": (df["TotalPrice"] - df["Cost"]).sum(),
        "New Customers": len(df["CustomerID"].unique()),
        "Cash Flow": df["TotalPrice"].sum() - df["Cost"].sum(),
    }

    # คำนวณข้อมูลกราฟรายเดือน
    monthly_data = df.groupby(df["OrderDate"].dt.strftime("%Y-%m"))

    revenue_data = {
        "labels": list(monthly_data.groups.keys()),
        "values": list(monthly_data["TotalPrice"].sum().values),
    }

    expense_data = {
        "labels": list(monthly_data.groups.keys()),
        "values": list(monthly_data["Cost"].sum().values),
    }

    # คำนวณ Profit Margin
    profit_margin = (
        (df["TotalPrice"] - df["Cost"]).sum() / df["TotalPrice"].sum()
    ) * 100

    # สร้างข้อมูลเป้าหมาย
    revenue_target = {
        "labels": revenue_data["labels"],
        "actual": list(monthly_data["TotalPrice"].sum().values),
        "target": list(
            monthly_data["TotalPrice"].sum().values * 1.2
        ),  # เป้าหมายสูงกว่า 20%
    }

    return {
        "metrics": metrics,
        "revenue_data": revenue_data,
        "expense_data": expense_data,
        "profit_margin": profit_margin,
        "revenue_target": revenue_target,
    }
