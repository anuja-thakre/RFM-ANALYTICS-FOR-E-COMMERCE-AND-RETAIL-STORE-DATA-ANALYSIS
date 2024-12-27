
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, max as spark_max, count, sum as spark_sum, when
from pyspark.sql.types import DateType
from datetime import datetime

# Initialize Spark Session
spark = SparkSession.builder.appName("RFM Analysis").getOrCreate()

# Load Dataset
def load_data(file_path):
    return spark.read.csv(file_path, header=True, inferSchema=True)

# Data Cleaning
def clean_data(df):
    df = df.dropna()
    df = df.withColumn("InvoiceDate", col("InvoiceDate").cast(DateType()))
    df = df.filter((col("Quantity") > 0) & (col("UnitPrice") > 0))
    return df

# Calculate RFM Metrics
def calculate_rfm(df, analysis_date):
    analysis_date_lit = lit(analysis_date)
    rfm = df.withColumn("TotalAmount", col("Quantity") * col("UnitPrice")) \
        .groupBy("CustomerID") \
        .agg(
            (spark_max(analysis_date_lit - col("InvoiceDate"))).alias("Recency"),
            count("InvoiceNo").alias("Frequency"),
            spark_sum("TotalAmount").alias("Monetary")
        )
    return rfm

# Assign RFM Scores
def assign_rfm_scores(rfm):
    rfm = rfm.withColumn("R_Score", when(col("Recency") <= 30, 4).when(col("Recency") <= 60, 3).when(col("Recency") <= 90, 2).otherwise(1))
    rfm = rfm.withColumn("F_Score", when(col("Frequency") >= 50, 4).when(col("Frequency") >= 20, 3).when(col("Frequency") >= 10, 2).otherwise(1))
    rfm = rfm.withColumn("M_Score", when(col("Monetary") >= 1000, 4).when(col("Monetary") >= 500, 3).when(col("Monetary") >= 100, 2).otherwise(1))
    rfm = rfm.withColumn("RFM_Score", col("R_Score") + col("F_Score") + col("M_Score"))
    return rfm

# Segment Customers
def segment_customers(rfm):
    rfm = rfm.withColumn("Segment", when(col("RFM_Score") >= 10, "Best Customers")
                         .when(col("RFM_Score") >= 7, "Loyal Customers")
                         .when(col("RFM_Score") >= 5, "Big Spenders")
                         .otherwise("At-Risk"))
    return rfm

# Save Results
def save_results(rfm, output_path):
    rfm.write.csv(output_path, header=True, mode="overwrite")

# Main Workflow
def main():
    # Define file paths
    input_file = "ecommerce_data.csv"
    output_file = "rfm_analysis_output"

    # Define analysis date
    analysis_date = datetime(2024, 12, 31)

    # Workflow Steps
    df = load_data(input_file)
    df = clean_data(df)
    rfm = calculate_rfm(df, analysis_date)
    rfm = assign_rfm_scores(rfm)
    rfm = segment_customers(rfm)
    save_results(rfm, output_file)

    print("RFM Analysis Complete. Results saved to", output_file)

if __name__ == "__main__":
    main()
