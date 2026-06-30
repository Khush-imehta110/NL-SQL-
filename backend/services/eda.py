import pandas as pd
import numpy as np

def get_duplicate_info(df: pd.DataFrame) -> dict:
    duplicate_count = df.duplicated().sum()
    return {
        "duplicate_rows": int(duplicate_count),
        "duplicate_percentage": round((duplicate_count / len(df)) * 100, 2)
    }

def get_unique_counts(df: pd.DataFrame) -> list:
    result = []
    for col in df.columns:
        result.append({
            "column": col,
            "unique_values": int(df[col].nunique()),
            "sample_values": str(df[col].dropna().unique()[:5].tolist())
        })
    return result

def get_outliers(df: pd.DataFrame) -> list:
    result = []
    numeric_cols = df.select_dtypes(include="number").columns
    for col in numeric_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        outlier_count = int(((df[col] < lower) | (df[col] > upper)).sum())
        result.append({
            "column": col,
            "outlier_count": outlier_count,
            "outlier_percentage": round((outlier_count / len(df)) * 100, 2),
            "lower_bound": round(lower, 2),
            "upper_bound": round(upper, 2)
        })
    return result

def get_data_quality_score(df: pd.DataFrame) -> dict:
    total_cells = df.shape[0] * df.shape[1]
    missing_cells = df.isnull().sum().sum()
    duplicate_rows = df.duplicated().sum()
    numeric_cols = df.select_dtypes(include="number").columns
    
    total_outliers = 0
    for col in numeric_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        outliers = ((df[col] < Q1 - 1.5*IQR) | (df[col] > Q3 + 1.5*IQR)).sum()
        total_outliers += outliers

    missing_score = max(0, 40 * (1 - missing_cells / total_cells))
    duplicate_score = max(0, 30 * (1 - duplicate_rows / len(df)))
    outlier_score = max(0, 30 * (1 - total_outliers / (len(df) * max(len(numeric_cols), 1))))
    
    total_score = round(missing_score + duplicate_score + outlier_score)
    
    if total_score >= 80:
        grade = "Excellent"
        color = "green"
    elif total_score >= 60:
        grade = "Good"
        color = "orange"
    else:
        grade = "Needs Cleaning"
        color = "red"

    return {
        "score": total_score,
        "grade": grade,
        "color": color,
        "missing_score": round(missing_score),
        "duplicate_score": round(duplicate_score),
        "outlier_score": round(outlier_score)
    }

def get_correlation(df: pd.DataFrame) -> dict:
    numeric_df = df.select_dtypes(include="number")
    if numeric_df.shape[1] < 2:
        return {}
    corr = numeric_df.corr().round(2)
    return {
        "columns": corr.columns.tolist(),
        "values": corr.values.tolist()
    }