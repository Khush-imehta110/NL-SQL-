import duckdb

def query_csv(filepath: str, sql: str):
    conn = duckdb.connect()
    conn.execute(f"CREATE VIEW data AS SELECT * FROM read_csv_auto('{filepath}')")
    result = conn.execute(sql).fetchdf()
    return result