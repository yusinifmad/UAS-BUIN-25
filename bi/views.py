from django.shortcuts import render
from django.db.models import Sum, Avg
from django.conf import settings
from .models import FactSales, FactProfit, FactShipping, DimDate
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import os
import json
from datetime import datetime

# JSON encoder khusus untuk numpy
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer, np.floating)):
            return obj.item()
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

# Fungsi untuk load data CSV ke database jika kosong
def load_data_if_empty():
    base_path = os.path.join(settings.BASE_DIR, 'bi')

    if not DimDate.objects.exists():
        df_date = pd.read_csv(os.path.join(base_path, 'dim_date.csv'))
        for _, row in df_date.iterrows():
            DimDate.objects.create(
                id=row['ID_Date'],
                full_date=datetime.strptime(row['Full_Date'], '%Y-%m-%d')
            )

    if not FactSales.objects.exists():
        df_sales = pd.read_csv(os.path.join(base_path, 'fact_sales.csv'))
        for _, row in df_sales.iterrows():
            FactSales.objects.create(
                id=row['ID_Sales'],
                date_id=row['ID_Date'],
                sales_value=row['Sales_Value']
            )

    if not FactProfit.objects.exists():
        df_profit = pd.read_csv(os.path.join(base_path, 'fact_profit.csv'))
        for _, row in df_profit.iterrows():
            FactProfit.objects.create(
                id=row['ID_Profit'],
                date_id=row['ID_Date'],
                profit_value=row['Profit_Value']
            )

    if not FactShipping.objects.exists():
        df_shipping = pd.read_csv(os.path.join(base_path, 'fact_shipping.csv'))
        for _, row in df_shipping.iterrows():
            FactShipping.objects.create(
                id=row['ID_Shipping'],
                date_id=row['ID_Date'],
                shipping_delay=row['Shipping_Delay']
            )

# Fungsi prediksi sales
def get_sales_prediction():
    sales_data = FactSales.objects.values('date__full_date') \
        .annotate(total_sales=Sum('sales_value')) \
        .order_by('date__full_date')

    if not sales_data:
        return {k: [] for k in ['historical_months', 'historical_sales', 'predicted_months', 'predicted_sales']}

    historical_months = [item['date__full_date'].strftime('%b %Y') for item in sales_data]
    sales_values = [item['total_sales'] for item in sales_data]
    X = np.arange(len(sales_values)).reshape(-1, 1)
    y = np.array(sales_values)

    model = LinearRegression()
    model.fit(X, y)

    future_indices = np.arange(len(sales_values), len(sales_values) + 8).reshape(-1, 1)
    future_months = ['Mar 2015', 'Apr 2015', 'Mar 2016', 'Apr 2016', 'Mar 2017', 'Apr 2017', 'Mar 2018', 'Apr 2018']
    predicted_sales = model.predict(future_indices)

    return {
        'historical_months': historical_months,
        'historical_sales': sales_values,
        'predicted_months': future_months,
        'predicted_sales': predicted_sales.tolist()
    }

# Fungsi prediksi profit
def get_profit_prediction():
    profit_data = FactProfit.objects.values('date__full_date') \
        .annotate(total_profit=Sum('profit_value')) \
        .order_by('date__full_date')

    if not profit_data:
        return {k: [] for k in ['historical_months', 'historical_profit', 'predicted_months', 'predicted_profit']}

    historical_months = [item['date__full_date'].strftime('%b %Y') for item in profit_data]
    profit_values = [item['total_profit'] for item in profit_data]
    X = np.arange(len(profit_values)).reshape(-1, 1)
    y = np.array(profit_values)

    model = LinearRegression()
    model.fit(X, y)

    future_indices = np.arange(len(profit_values), len(profit_values) + 8).reshape(-1, 1)
    future_months = ['Mar 2015', 'Apr 2015', 'Mar 2016', 'Apr 2016', 'Mar 2017', 'Apr 2017', 'Mar 2018', 'Apr 2018']
    predicted_profit = model.predict(future_indices)

    return {
        'historical_months': historical_months,
        'historical_profit': profit_values,
        'predicted_months': future_months,
        'predicted_profit': predicted_profit.tolist()
    }

# Fungsi prediksi shipping delay
def get_shipping_delay_prediction():
    delay_data = FactShipping.objects.values('date__full_date') \
        .annotate(avg_delay=Avg('shipping_delay')) \
        .order_by('date__full_date')

    if not delay_data:
        return {k: [] for k in ['historical_months', 'historical_delay', 'predicted_months', 'predicted_delay']}

    historical_months = [item['date__full_date'].strftime('%b %Y') for item in delay_data]
    delay_values = [item['avg_delay'] for item in delay_data]
    X = np.arange(len(delay_values)).reshape(-1, 1)
    y = np.array(delay_values)

    model = LinearRegression()
    model.fit(X, y)

    future_indices = np.arange(len(delay_values), len(delay_values) + 8).reshape(-1, 1)
    future_months = ['Mar 2015', 'Apr 2015', 'Mar 2016', 'Apr 2016', 'Mar 2017', 'Apr 2017', 'Mar 2018', 'Apr 2018']
    predicted_delay = model.predict(future_indices)

    return {
        'historical_months': historical_months,
        'historical_delay': delay_values,
        'predicted_months': future_months,
        'predicted_delay': predicted_delay.tolist()
    }

# View utama untuk dashboard
def dashboard(request):
    load_data_if_empty()

    sales = get_sales_prediction()
    profit = get_profit_prediction()
    delay = get_shipping_delay_prediction()

    summary = {
        'total_sales': FactSales.objects.aggregate(Sum('sales_value'))['sales_value__sum'] or 0,
        'total_profit': FactProfit.objects.aggregate(Sum('profit_value'))['profit_value__sum'] or 0,
        'avg_delay': FactShipping.objects.aggregate(Avg('shipping_delay'))['shipping_delay__avg'] or 0,
        'total_shipments': FactShipping.objects.count(),
        'total_sales_prediction': sum(sales['predicted_sales']),
        'total_profit_prediction': sum(profit['predicted_profit']),
        'total_delay_prediction': sum(delay['predicted_delay']),
    }

    context = {
        'page_title': 'Dashboard Analisis dan Prediksi',
        'summary_stats': summary,
        'sales_prediction': sales,
        'profit_prediction': profit,
        'shipping_delay_prediction': delay,
    }

    return render(request, 'bi/visualisasi.html', context)
