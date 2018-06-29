import pandas as pd
import util_functions as uf


def load_excel(sheet_name):
    # Load the Data Dictionary spreadsheet
    data_dict = "Data Dictionary.xlsx"
    df = pd.read_excel(data_dict, sheet_name=sheet_name)
    return df.fillna('None')


def load_comments(comment_series, cur):
    '''create execute string that includes full postgres comments for aws
    Ex. Table = comment on [table] anc is '[Description]'
    Ex. Attribute = comment on column [Table].[Field] is '[Description]'
    '''
    comments_string = "".join([comment for comment in comment_series.tolist()])
    cur.execute(comments_string)


if __name__ == "__main__":

    # Connect to AWS
    uf.set_env_path()
    conn, cur = uf.aws_connect()

    # Table Descriptions
    tables_df = load_excel(sheet_name='Tables')
    table_comments = "comment on table " + tables_df['Table'] + " is '" + tables_df['Description'] + "';"
    load_comments(comment_series=table_comments, cur=cur)

    # Field Descriptions
    fields_df = load_excel(sheet_name='Fields')
    field_comments = "comment on column " + fields_df['Table'] + "." + fields_df['Attribute'] + " is '" + fields_df['Description'].str.replace("'", "''") + "';"
    load_comments(comment_series=field_comments, cur=cur)

    # Commit changes to database
    conn.commit()
