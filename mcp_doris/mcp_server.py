import logging
from typing import List, Dict, Any
import concurrent.futures
import atexit
import mysql.connector
from mysql.connector import errorcode

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from mcp_doris.mcp_env import config

MCP_SERVER_NAME = "mcp-doris"

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(MCP_SERVER_NAME)

QUERY_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=10)
atexit.register(lambda: QUERY_EXECUTOR.shutdown(wait=True))
SELECT_QUERY_TIMEOUT_SECS = 30

load_dotenv()

deps = [
    "mysql-connector-python",
    "python-dotenv",
    "uvicorn",
    "pip-system-certs",
]

mcp = FastMCP(MCP_SERVER_NAME, dependencies=deps)


def create_doris_client():
    """Create a MySQL connection to Apache Doris.
    
    Returns:
        mysql.connector.connection.MySQLConnection: A connection to the Doris database
    """
    client_config = config.get_client_config()
    logger.info(
        f"Creating Doris client connection to {client_config['host']}:{client_config['port']} "
        f"as {client_config['user']} "
        f"(connect_timeout={client_config['connect_timeout']}s, "
        f"connection_timeout={client_config['connection_timeout']}s)"
    )

    try:
        conn = mysql.connector.connect(**client_config)
        # Test the connection
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        cursor.close()
        logger.info(f"Successfully connected to Apache Doris version {version}")
        return conn
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            logger.error("Invalid username or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            logger.error("Database does not exist")
        else:
            logger.error(f"Failed to connect to Doris: {err}")
        raise


@mcp.tool()
def show_databases():
    """List all databases in the Doris instance.
    
    Returns:
        List[str]: A list of database names
    """
    logger.info("Listing all databases")
    conn = create_doris_client()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SHOW DATABASES")
        databases = [row[0] for row in cursor.fetchall()]
        logger.info(f"Found {len(databases)} databases")
        return databases
    finally:
        cursor.close()
        conn.close()


@mcp.tool()
def show_tables(database: str, like: str = None):
    """List all tables in the specified database.
    
    Args:
        database: The database name
        like: Optional pattern to filter table names
        
    Returns:
        List[Dict]: A list of table information dictionaries
    """
    logger.info(f"Listing tables in database '{database}'")
    conn = create_doris_client()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Use the specified database
        cursor.execute(f"USE `{database}`")
        
        # Get tables
        query = "SHOW TABLES"
        if like:
            query += f" LIKE '{like}'"
        cursor.execute(query)
        table_names = [row['Tables_in_' + database] for row in cursor.fetchall()]
        
        tables = []
        for table in table_names:
            logger.info(f"Getting schema info for table {database}.{table}")
            
            # Get table schema
            cursor.execute(f"DESCRIBE `{table}`")
            columns = cursor.fetchall()
            
            # Get create table statement
            cursor.execute(f"SHOW CREATE TABLE `{table}`")
            create_table_result = cursor.fetchone()['Create Table']
            
            # Get table comment if available (extracted from create table statement)
            table_comment = None
            if "COMMENT=" in create_table_result:
                comment_parts = create_table_result.split("COMMENT=")
                if len(comment_parts) > 1:
                    table_comment = comment_parts[1].split("'")[1]
            
            tables.append({
                "database": database,
                "name": table,
                "comment": table_comment,
                "columns": columns,
                "create_table_query": create_table_result,
            })
        
        logger.info(f"Found {len(tables)} tables")
        return tables
    finally:
        cursor.close()
        conn.close()


def execute_query_impl(query: str) -> List[Dict[str, Any]]:
    """Execute a SELECT query against Doris.
    
    Args:
        query: The SQL query to execute
        
    Returns:
        List[Dict]: The query results as a list of dictionaries
    """
    conn = create_doris_client()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        logger.info(f"Query returned {len(rows)} rows")
        return rows
    except Exception as err:
        logger.error(f"Error executing query: {err}")
        return [{"error": f"Error running query: {err}"}]
    finally:
        cursor.close()
        conn.close()


@mcp.tool()
def execute_query(query: str):
    """Run a SELECT query against Doris with timeout protection.
    
    Args:
        query: The SQL query to execute
        
    Returns:
        List[Dict]: The query results
    """
    logger.info(f"Executing SELECT query: {query}")
    
    # Basic validation to ensure it's a SELECT query
    if not query.strip().upper().startswith("SELECT"):
        return {"error": "Only SELECT queries are allowed for security reasons"}
    
    future = QUERY_EXECUTOR.submit(execute_query_impl, query)
    try:
        result = future.result(timeout=SELECT_QUERY_TIMEOUT_SECS)
        return result
    except concurrent.futures.TimeoutError:
        logger.warning(f"Query timed out after {SELECT_QUERY_TIMEOUT_SECS} seconds: {query}")
        future.cancel()
        return {"error": f"Queries taking longer than {SELECT_QUERY_TIMEOUT_SECS} seconds are currently not supported."} 
