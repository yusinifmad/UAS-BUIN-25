from django.db import models

# Tabel dim_category_name
class DimCategory(models.Model):
    category_name_id = models.IntegerField(unique=True)
    category_name = models.CharField(max_length=255)

    def __str__(self):
        return self.category_name

# Tabel dim_date
class DimDate(models.Model):
    date_id = models.IntegerField(unique=True)
    date_time = models.DateTimeField()
    full_date = models.CharField(max_length=100)
    day = models.IntegerField()
    month = models.IntegerField()
    year = models.IntegerField()

    def __str__(self):
        return self.full_date

# Tabel dim_order_region (ini sudah benar menggunakan DimOrderRegion)
class DimOrderRegion(models.Model):
    order_region_id = models.IntegerField(unique=True)
    order_region_name = models.CharField(max_length=255)
    
    def __str__(self):
        return self.order_region_name

# Tabel dim_shipping_mode
class DimShippingMode(models.Model):
    shipping_mode_id = models.IntegerField(unique=True)
    shipping_mode_name = models.CharField(max_length=255)

    def __str__(self):
        return self.shipping_mode_name

# Tabel fact_profit
class FactProfit(models.Model):
    profit_fact_id = models.AutoField(primary_key=True)
    date = models.ForeignKey(DimDate, on_delete=models.CASCADE)
    shipping_mode = models.ForeignKey(DimShippingMode, on_delete=models.CASCADE)
    order_region = models.ForeignKey(DimOrderRegion, on_delete=models.CASCADE)
    category = models.ForeignKey(DimCategory, on_delete=models.CASCADE)
    profit_value = models.FloatField()

    def __str__(self):
        return f"{self.category} - {self.profit_value}"

# Tabel fact_sales
class FactSales(models.Model):
    sales_fact_id = models.AutoField(primary_key=True)
    date = models.ForeignKey(DimDate, on_delete=models.CASCADE)
    shipping_mode = models.ForeignKey(DimShippingMode, on_delete=models.CASCADE)
    order_region = models.ForeignKey(DimOrderRegion, on_delete=models.CASCADE)
    category = models.ForeignKey(DimCategory, on_delete=models.CASCADE)
    sales_value = models.FloatField()

    def __str__(self):
        return f"{self.category} - {self.sales_value}"

# Tabel fact_shipping
class FactShipping(models.Model):
    shipping_fact_id = models.AutoField(primary_key=True)
    date = models.ForeignKey(DimDate, on_delete=models.CASCADE)
    shipping_mode = models.ForeignKey(DimShippingMode, on_delete=models.CASCADE)
    order_region = models.ForeignKey(DimOrderRegion, on_delete=models.CASCADE)
    shipping_delay = models.FloatField()
    is_late = models.BooleanField()

    def __str__(self):
        return f"Delay: {self.shipping_delay}, Late: {self.is_late}"
