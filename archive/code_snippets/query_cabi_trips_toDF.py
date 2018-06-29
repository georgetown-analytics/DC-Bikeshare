import pandas as pd
import util_functions as uf


# Connect to AWS
uf.set_env_path()
conn, cur = uf.aws_connect()

# Query cabi trips
df = pd.read_sql("""SELECT * from cabi_trips LIMIT 10""", con=conn)

print(df)
print(df.dtypes)
