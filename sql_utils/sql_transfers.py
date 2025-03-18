import pandas as pd
from loguru import logger
import os, sys
from contextlib import contextmanager

script_dir = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(script_dir, '..')))  

from sql_utils.sql_connector import connect_to_db

class DBManager:
    """Class to manage database connections and operations"""
    
    def __init__(self):
        self.connections = {}  # Store connections by schema name
    
    def get_connection(self, schema):
        """Get an existing connection or create a new one if needed"""
        if schema not in self.connections:
            self.connections[schema] = connect_to_db(schema)
            logger.info(f"New connection established for schema: '{schema}'")
        return self.connections[schema]
    
    @contextmanager
    def connection_context(self, schema):
        """Context manager for database connections"""
        try:
            engine = self.get_connection(schema)
            yield engine
        except Exception as e:
            logger.error(f"Connection error with schema '{schema}': {str(e)}")
            raise
    
    def insert_df_to_db(self, df, table_name, schema):
        """Insert dataframe to database table"""
        try:
            with self.connection_context(schema) as engine:
                df.to_sql(table_name, engine, schema=schema, if_exists='replace', index=False)
                logger.info(f"Dataframe successfully inserted into schema: '{schema}' as table: '{table_name}'")
        except Exception as e:
            logger.error(f"Error inserting data: {str(e)}.")
    
    def extract_table_to_df(self, table_name, schema):
        """Extract database table to dataframe"""
        try:
            with self.connection_context(schema) as engine:
                full_table_name = f'"{schema}"."{table_name}"'
                df = pd.read_sql(f'SELECT * FROM {full_table_name}', engine)
                logger.info(f"Schema '{schema}': Table '{table_name}' successfully pulled into DataFrame")
                return df
        except Exception as e:
            logger.error(f"Error pulling table: {str(e)}.")
            return None
    
    def extract_multiple_tables(self, table_schema_pairs):
        """
        Extract multiple tables efficiently using the same connection where possible
        
        Args:
            table_schema_pairs: List of tuples in format [(table_name, schema), ...]
        
        Returns:
            Dictionary of dataframes with table_names as keys
        """
        results = {}
        
        # Group by schema to minimize connection switches
        schema_groups = {}
        for table, schema in table_schema_pairs:
            if schema not in schema_groups:
                schema_groups[schema] = []
            schema_groups[schema].append(table)
        
        # Process each schema group
        for schema, tables in schema_groups.items():
            try:
                with self.connection_context(schema) as engine:
                    for table in tables:
                        full_table_name = f'"{schema}"."{table}"'
                        results[table] = pd.read_sql(f'SELECT * FROM {full_table_name}', engine)
                        logger.info(f"Schema '{schema}': Table '{table}' successfully pulled into DataFrame")
            except Exception as e:
                logger.error(f"Error pulling tables from schema '{schema}': {str(e)}")
        
        return results
    
    def close_all_connections(self):
        """Close all open database connections"""
        for schema, engine in self.connections.items():
            try:
                engine.dispose()
                logger.info(f"Connection closed for schema: '{schema}'")
            except Exception as e:
                logger.error(f"Error closing connection for schema '{schema}': {str(e)}")
        self.connections = {}


# Create a singleton instance
db_manager = DBManager()

# Function wrappers for backward compatibility
def insert_df_to_db(df, table_name, schema):
    return db_manager.insert_df_to_db(df, table_name, schema)

def extract_table_to_df(table_name, schema):
    return db_manager.extract_table_to_df(table_name, schema)

def extract_multiple_tables(table_schema_pairs):
    return db_manager.extract_multiple_tables(table_schema_pairs)

def close_all_connections():
    db_manager.close_all_connections()


if __name__ == '__main__':
    data = {
        'name': ['LeBron James', 'Stephen Curry', 'Kevin Duranimal'],
        'team': ['Los Angeles Lakers', 'Golden State Warriors', 'Brooklyn Nets'],
        'position': ['Forward', 'Guard', 'Forward']
    }

    pd.set_option('display.max_columns', None)
    df = pd.DataFrame(data)
    
    # Example using the new interface
    # insert_df_to_db(df, 'players', 'playoffs')
    
    # Example of extracting multiple tables efficiently
    tables_to_extract = [
        ('2023_reg_season_stats', 'per_game_stats'),
        ('2023_playoffs_stats', 'per_game_stats'),
        ('players', 'playoffs')
    ]
    
    # Option 1: Extract individually but reuse connections
    pulled_df = extract_table_to_df('2023_reg_season_stats', 'per_game_stats')
    if pulled_df is not None:
        print(pulled_df.head(15))
    
    # Option 2: Extract multiple tables in one go
    """
    dataframes = extract_multiple_tables(tables_to_extract)
    for table_name, df in dataframes.items():
        if df is not None:
            print(f"\n{table_name} data:")
            print(df.head(5))
    """
    
    close_all_connections()