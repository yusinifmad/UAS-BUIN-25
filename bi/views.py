from django.shortcuts import render
from django.db.models import Sum, Avg
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np
import os
from django.conf import settings
import json
from .models import FactSales, FactProfit, FactShipping

class NumpyEncoder(json.JSONEncoder):
    """ Special json encoder for numpy types """
    def default(self, obj):
        if isinstance(obj, (np.integer, np.int_, np.intc, np.intp, np.int8,
            np.int16, np.int32, np.int64, np.uint8,
            np.uint16, np.uint32, np.uint64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float_, np.float16, np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

def get_random_color(alpha=1.0):
    """Helper function to generate random RGBA colors for charts."""
    return f"rgba({np.random.randint(0, 255)}, {np.random.randint(0, 255)}, {np.random.randint(0, 255)}, {alpha})"

# Fungsi untuk mendapatkan prediksi total sales dan data aktual
def get_sales_prediction():
    # Ambil data historis sales dari FactSales
    sales_data = FactSales.objects.values('date__full_date') \
        .annotate(total_sales=Sum('sales_value')) \
        .order_by('date__full_date')

    # Jika tidak ada data historis, return data kosong untuk prediksi
    if not sales_data:
        return {
            'historical_months': [],
            'historical_sales': [],
            'predicted_months': [],
            'predicted_sales': [],
            'actual_sales': [],
        }

    historical_data = [{'month': item['date__full_date'].strftime('%b %Y'), 'sales': item['total_sales']} for item in sales_data]

    # Persiapkan data untuk Linear Regression
    X = np.array([item['total_sales'] for item in historical_data]).reshape(-1, 1)
    y = np.array([item['sales'] for item in historical_data])

    # Pastikan ada data sebelum melanjutkan ke Linear Regression
    if X.shape[0] < 1:
        return {
            'historical_months': [],
            'historical_sales': [],
            'predicted_months': [],
            'predicted_sales': [],
            'actual_sales': [],
        }

    model = LinearRegression()
    model.fit(X, y)

    
    future_months = ['Mar 2015', 'Apr 2015', 'Mar 2016', 'Apr 2016', 'Mar 2017', 'Apr 2017','Mar 2018', 'Apr 2018']
    predicted_sales = model.predict([[item] for item in range(len(historical_data), len(historical_data) + len(future_months))])

    predictions = [{'month': month, 'sales': prediction} for month, prediction in zip(future_months, predicted_sales)]
    
    # Data aktual (menggunakan data manual atau data historis yang ada)
    actual_sales = [
        {'actual_sales': 'actual_sales', 'month': actual_data_points, 'backgroundColor': 'rgba(54, 162, 235, 1)', 'type': 'scatter'},

    ]

    return {
        'historical_months': [item['month'] for item in historical_data],
        'historical_sales': [item['sales'] for item in historical_data],
        'predicted_months': [item['month'] for item in predictions],
        'predicted_sales': [item['sales'] for item in predictions],
        'actual_sales': [item['sales'] for item in actual_sales],  # Memastikan data aktual dikirim
    }

# Fungsi untuk mendapatkan prediksi total profit dan data aktual
def get_profit_prediction():
    profit_data = FactProfit.objects.values('date__full_date') \
        .annotate(total_profit=Sum('profit_value')) \
        .order_by('date__full_date')

    # Pastikan ada data historis
    if not profit_data:
        return {
            'historical_months': [],
            'historical_profit': [],
            'predicted_months': [],
            'predicted_profit': [],
            'actual_profit': [],
        }

    historical_data = [{'month': item['date__full_date'].strftime('%b %Y'), 'profit': item['total_profit']} for item in profit_data]

    # Persiapkan data untuk Linear Regression
    X = np.array([item['total_profit'] for item in historical_data]).reshape(-1, 1)
    y = np.array([item['profit'] for item in historical_data])

    # Pastikan ada data sebelum melanjutkan ke Linear Regression
    if X.shape[0] < 1:
        return {
            'historical_months': [],
            'historical_profit': [],
            'predicted_months': [],
            'predicted_profit': [],
            'actual_profit': [],
        }

    model = LinearRegression()
    model.fit(X, y)

    
    future_months = ['Mar 2015', 'Apr 2015', 'Mar 2016', 'Apr 2016', 'Mar 2017', 'Apr 2017','Mar 2018', 'Apr 2018']
    predicted_profit = model.predict([[item] for item in range(len(historical_data), len(historical_data) + len(future_months))])

    predictions = [{'month': month, 'profit': profit} for month, profit in zip(future_months, predicted_profit)]
    
    # Data aktual profit untuk perbandingan
    actual_profit = [
        {'actual_profit': 'actual_profit', 'month': actual_data_points, 'backgroundColor': 'rgba(54, 162, 235, 1)', 'type': 'scatter'},

    ]

    return {
        'historical_months': [item['month'] for item in historical_data],
        'historical_profit': [item['profit'] for item in historical_data],
        'predicted_months': [item['month'] for item in predictions],
        'predicted_profit': [item['profit'] for item in predictions],
        'actual_profit': [item['profit'] for item in actual_profit],  # Memastikan data aktual dikirim
    }

# Fungsi untuk mendapatkan prediksi total shipping delay dan data aktual
def get_shipping_delay_prediction():
    shipping_data = FactShipping.objects.values('date__full_date') \
        .annotate(avg_delay=Avg('shipping_delay')) \
        .order_by('date__full_date')

    # Pastikan ada data historis
    if not shipping_data:
        return {
            'historical_months': [],
            'historical_delay': [],
            'predicted_months': [],
            'predicted_delay': [],
            'actual_delay': [],
        }

    historical_data = [{'month': item['date__full_date'].strftime('%b %Y'), 'avg_delay': item['avg_delay']} for item in shipping_data]

    # Persiapkan data untuk Linear Regression
    X = np.array([item['avg_delay'] for item in historical_data]).reshape(-1, 1)
    y = np.array([item['avg_delay'] for item in historical_data])

    # Pastikan ada data sebelum melanjutkan ke Linear Regression
    if X.shape[0] < 1:
        return {
            'historical_months': [],
            'historical_delay': [],
            'predicted_months': [],
            'predicted_delay': [],
            'actual_delay': [],
        }

    model = LinearRegression()
    model.fit(X, y)

    # Membuat prediksi hasil model fitting
    future_months = ['Mar 2015', 'Apr 2015', 'Mar 2016', 'Apr 2016', 'Mar 2017', 'Apr 2017','Mar 2018', 'Apr 2018']
    predicted_delay = model.predict([[item] for item in range(len(historical_data), len(historical_data) + len(future_months))])

    predictions = [{'month': month, 'avg_delay': delay} for month, delay in zip(future_months, predicted_delay)]
    
    # Data aktual shipping delay untuk perbandingan
    actual_delay = [
        {'actual_delay': 'actual_delay', 'month': actual_data_points, 'backgroundColor': 'rgba(54, 162, 235, 1)', 'type': 'scatter'},

    ]

    return {
        'historical_months': [item['month'] for item in historical_data],
        'historical_delay': [item['avg_delay'] for item in historical_data],
        'predicted_months': [item['month'] for item in predictions],
        'predicted_delay': [item['avg_delay'] for item in predictions],
        'actual_delay': [item['avg_delay'] for item in actual_delay],  # Memastikan data aktual dikirim
    }

# Fungsi utama untuk menampilkan dashboard
def dashboard(request):
    # Mengambil data prediksi dan aktual
    sales_prediction = get_sales_prediction()
    profit_prediction = get_profit_prediction()
    shipping_delay_prediction = get_shipping_delay_prediction()

    # Menghitung ringkasan data untuk halaman dashboard
    summary_stats = {
        'total_sales': FactSales.objects.aggregate(Sum('sales_value'))['sales_value__sum'],
        'total_profit': FactProfit.objects.aggregate(Sum('profit_value'))['profit_value__sum'],
        'avg_delay': FactShipping.objects.aggregate(Avg('shipping_delay'))['shipping_delay__avg'],
        'total_shipments': FactShipping.objects.count(),
        'total_sales_prediction': sum(sales_prediction['predicted_sales']),
        'total_profit_prediction': sum(profit_prediction['predicted_profit']),
        'total_delay_prediction': sum(shipping_delay_prediction['predicted_delay']),
    }

    # Mengirimkan data ke template
    context = {
        'page_title': 'Dashboard Analisis dan Prediksi Penjualan',
        'summary_stats': summary_stats,
        'sales_prediction': sales_prediction,
        'profit_prediction': profit_prediction,
        'shipping_delay_prediction': shipping_delay_prediction,
    }

    return render(request, 'bi/visualisasi.html', context)