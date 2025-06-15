from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import pandas as pd
import os

dag_path = os.path.dirname(_file_)
raw_data_path = os.path.join(dag_path, 'DataCo.csv')
output_dir = os.path.join(dag_path, 'data', 'output_star_schema')
os.makedirs(output_dir, exist_ok=True)

def extract():
    # Membaca data mentah
    df = pd.read_csv(raw_data_path, sep=';', encoding='utf-8-sig')

    # Menghapus kolom yang tidak diperlukan untuk analisis
    drop_cols = [
        'Customer Email', 'Customer Password', 'Customer Street', 'Product Image',
        'Product Description', 'Latitude', 'Longitude', 'Order Item Cardprod Id',
        'Order Item Id', 'Product Card Id', 'Order Customer Id', 
    ]
    df.drop(columns=drop_cols, inplace=True)

    # Mengonversi kolom tanggal
    df['order date (DateOrders)'] = pd.to_datetime(df['order date (DateOrders)'], errors='coerce')
    df['shipping date (DateOrders)'] = pd.to_datetime(df['shipping date (DateOrders)'], errors='coerce')

    # Menghitung keterlambatan pengiriman
    df['Shipping Delay'] = pd.to_numeric(df['Days for shipping (real)'], errors='coerce') - pd.to_numeric(df['Days for shipment (scheduled)'], errors='coerce')
    df['Is Late'] = df['Shipping Delay'] > 0

    # Menambahkan kolom bulan untuk analisis penjualan bulanan
    df['Order Month'] = df['order date (DateOrders)'].dt.to_period('M').astype(str)
    df['Sales'] = pd.to_numeric(df['Sales'], errors='coerce')
    df['Order Profit Per Order'] = pd.to_numeric(df['Order Profit Per Order'], errors='coerce')

    # Menyimpan data hasil ekstraksi ke file CSV
    df.to_csv(os.path.join(dag_path, 'extracted_supplychain.csv'), index=False)

# Fungsi transform untuk membuat dimensi dan tabel fakta sesuai Star Schema
def transform():
    # Membaca file CSV hasil ekstraksi
    df = pd.read_csv(os.path.join(dag_path, 'extracted_supplychain.csv'), low_memory=False)

    # Mengonversi kolom tanggal
    df['order date (DateOrders)'] = pd.to_datetime(df['order date (DateOrders)'], errors='coerce')
    df['shipping date (DateOrders)'] = pd.to_datetime(df['shipping date (DateOrders)'], errors='coerce')
    df.dropna(subset=['order date (DateOrders)', 'shipping date (DateOrders)'], inplace=True)

    # 1. Dimensi Tanggal
    dim_date = df[['order date (DateOrders)']].drop_duplicates().reset_index(drop=True)
    dim_date['date_id'] = dim_date.index + 1
    dim_date['full_date'] = dim_date['order date (DateOrders)'].dt.date
    dim_date['day'] = dim_date['order date (DateOrders)'].dt.day
    dim_date['month'] = dim_date['order date (DateOrders)'].dt.month
    dim_date['year'] = dim_date['order date (DateOrders)'].dt.year
    dim_date.rename(columns={'order date (DateOrders)': 'date_time'}, inplace=True)
    dim_date['full_date'] = pd.to_datetime(dim_date['full_date'], errors='coerce')
    dim_date = dim_date[['date_id', 'date_time', 'full_date', 'day', 'month', 'year']]
    dim_date.to_csv(os.path.join(output_dir, 'dim_date.csv'), index=False)

    # 2. Dimensi Pelanggan (dim_customer)
    dim_customer = df[['Customer Id', 'Segment', 'cust City', 'order State', 'cust Country']].drop_duplicates().reset_index(drop=True)
    dim_customer['customer_id'] = dim_customer.index + 1
    dim_customer.rename(columns={'Customer Id': 'customer_id', 'Segment': 'segment', 'cust City': 'city', 'order State': 'state', 'cust Country': 'country'}, inplace=True)
    dim_customer.to_csv(os.path.join(output_dir, 'dim_customer.csv'), index=False)

    # 3. Dimensi Produk (dim_product)
    dim_product = df[['Category Name', 'Product Id', 'Department', 'Price']].drop_duplicates().reset_index(drop=True)
    dim_product['product_id'] = dim_product.index + 1
    dim_product.rename(columns={'Category Name': 'category_name', 'Product Id': 'product_id', 'Department': 'department', 'Price': 'price'}, inplace=True)
    dim_product.to_csv(os.path.join(output_dir, 'dim_product.csv'), index=False)

    # 4. Dimensi Mode Pengiriman (dim_shipping_mode)
    dim_shipping_mode = df[['Shipping Mode']].drop_duplicates().reset_index(drop=True)
    dim_shipping_mode['shipping_mode_id'] = dim_shipping_mode.index + 1
    dim_shipping_mode.rename(columns={'Shipping Mode': 'shipping_mode_name'}, inplace=True)
    dim_shipping_mode.to_csv(os.path.join(output_dir, 'dim_shipping_mode.csv'), index=False)

    # 5. Dimensi Wilayah (dim_geography)
    dim_geography = df[['Order Region', 'cust Country', 'order State']].drop_duplicates().reset_index(drop=True)
    dim_geography['geography_id'] = dim_geography.index + 1
    dim_geography.rename(columns={'Order Region': 'region', 'cust Country': 'country', 'order State': 'state'}, inplace=True)
    dim_geography.to_csv(os.path.join(output_dir, 'dim_geography.csv'), index=False)

    # Tabel Fakta Penjualan (fact_sales)
    df_fact = df.copy()
    df_fact = pd.merge(df_fact, dim_date[['date_id', 'full_date']], left_on='order date (DateOrders)', right_on='full_date', how='left')
    df_fact = pd.merge(df_fact, dim_customer[['customer_id', 'segment', 'city', 'state', 'country']], left_on='Customer Id', right_on='customer_id', how='left')
    df_fact = pd.merge(df_fact, dim_product[['product_id', 'category_name', 'department', 'price']], left_on='Product Id', right_on='product_id', how='left')

    fact_sales = df_fact[['date_id', 'customer_id', 'product_id', 'Sales']].copy()
    fact_sales.rename(columns={'Sales': 'sales_value'}, inplace=True)
    fact_sales.insert(0, 'sales_fact_id', range(1, 1 + len(fact_sales)))
    fact_sales.to_csv(os.path.join(output_dir, 'fact_sales.csv'), index=False)

    # Tabel Fakta Keuntungan (fact_profit)
    fact_profit = df_fact[['date_id', 'customer_id', 'product_id', 'Order Profit Per Order']].copy()
    fact_profit.rename(columns={'Order Profit Per Order': 'profit_value'}, inplace=True)
    fact_profit.insert(0, 'profit_fact_id', range(1, 1 + len(fact_profit)))
    fact_profit.to_csv(os.path.join(output_dir, 'fact_profit.csv'), index=False)

    # Tabel Fakta Pengiriman (fact_shipping)
    fact_shipping = df_fact[['date_id', 'customer_id', 'product_id', 'Shipping Delay', 'Is Late']].copy()
    fact_shipping.rename(columns={'Shipping Delay': 'shipping_delay', 'Is Late': 'is_late'}, inplace=True)
    fact_shipping.insert(0, 'shipping_fact_id', range(1, 1 + len(fact_shipping)))
    fact_shipping.to_csv(os.path.join(output_dir, 'fact_shipping.csv'), index=False)

    print("Transform completed.")
    
def load():
    print("Data has been saved to output folder (in transform step). No load step required.")

with DAG(
    dag_id='etl_supplychain_via_airflow',
    start_date=datetime(2025, 1, 1),
    schedule='@daily',
    catchup=False,
    tags=['etl', 'supplychain', 'star_schema']
) as dag:

    t1 = PythonOperator(
        task_id='extract',
        python_callable=extract
    )

    t2 = PythonOperator(
        task_id='transform',
        python_callable=transform
    )

    t3 = PythonOperator(
        task_id='load',
        python_callable=load
    )

    t1 >> t2 >> t3