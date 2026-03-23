from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, text, inspect, MetaData, Table
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from langchain.tools import Tool
from src.core.config import settings
from src.core.logging import get_logger
from src.core.exceptions import ToolExecutionError

logger = get_logger(__name__)


class SQLTools:
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or settings.DATABASE_URL
        
        try:
            self.engine = create_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=settings.DATABASE_POOL_SIZE,
                max_overflow=settings.DATABASE_MAX_OVERFLOW,
                pool_pre_ping=True
            )
            
            self.SessionLocal = sessionmaker(bind=self.engine)
            self.metadata = MetaData()
            
            logger.info(f"Initialized SQL tools with database: {self._mask_url(self.database_url)}")
            
        except Exception as e:
            logger.error(f"Failed to initialize SQL tools: {str(e)}")
            raise ToolExecutionError("Failed to connect to database", details={"error": str(e)})
    
    def _mask_url(self, url: str) -> str:
        if '@' in url:
            parts = url.split('@')
            return f"{parts[0].split(':')[0]}:***@{parts[1]}"
        return url
    
    def get_schema_info(self) -> Dict[str, Any]:
        try:
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
            
            schema_info = {}
            for table_name in tables:
                columns = inspector.get_columns(table_name)
                schema_info[table_name] = {
                    'columns': [
                        {
                            'name': col['name'],
                            'type': str(col['type']),
                            'nullable': col['nullable']
                        }
                        for col in columns
                    ],
                    'primary_keys': inspector.get_pk_constraint(table_name)['constrained_columns']
                }
            
            logger.info(f"Retrieved schema info for {len(tables)} tables")
            return schema_info
            
        except Exception as e:
            logger.error(f"Error getting schema info: {str(e)}")
            raise ToolExecutionError("Failed to get schema info", details={"error": str(e)})
    
    def execute_query(
        self,
        query: str,
        params: Optional[Dict] = None,
        fetch_results: bool = True
    ) -> Dict[str, Any]:
        if not self._is_safe_query(query):
            raise ToolExecutionError(
                "Unsafe query detected",
                details={"query": query, "reason": "Query contains potentially dangerous operations"}
            )
        
        session = self.SessionLocal()
        try:
            result = session.execute(text(query), params or {})
            
            if fetch_results:
                rows = result.fetchall()
                columns = result.keys() if hasattr(result, 'keys') else []
                
                data = [dict(zip(columns, row)) for row in rows]
                
                logger.info(f"Query executed successfully, returned {len(data)} rows")
                
                return {
                    'success': True,
                    'data': data,
                    'row_count': len(data),
                    'columns': list(columns)
                }
            else:
                session.commit()
                logger.info("Query executed successfully (no fetch)")
                return {
                    'success': True,
                    'message': 'Query executed successfully'
                }
                
        except Exception as e:
            session.rollback()
            logger.error(f"Error executing query: {str(e)}")
            raise ToolExecutionError(
                "Failed to execute query",
                details={"error": str(e), "query": query}
            )
        finally:
            session.close()
    
    def _is_safe_query(self, query: str) -> bool:
        query_lower = query.lower().strip()
        
        dangerous_keywords = ['drop', 'delete', 'truncate', 'alter', 'create', 'insert', 'update']
        
        for keyword in dangerous_keywords:
            if keyword in query_lower.split():
                return False
        
        return True
    
    def get_table_sample(self, table_name: str, limit: int = 5) -> List[Dict]:
        try:
            query = f"SELECT * FROM {table_name} LIMIT {limit}"
            result = self.execute_query(query)
            return result['data']
        except Exception as e:
            logger.error(f"Error getting table sample: {str(e)}")
            raise ToolExecutionError(
                "Failed to get table sample",
                details={"error": str(e), "table": table_name}
            )
    
    def generate_sql_from_natural_language(self, question: str, schema_info: Dict) -> str:
        from langchain_openai import ChatOpenAI
        
        llm = ChatOpenAI(
            model=settings.MODEL_NAME,
            temperature=0,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        schema_str = self._format_schema_for_prompt(schema_info)
        
        prompt = f"""Given the following database schema:

{schema_str}

Generate a SQL query to answer this question: {question}

Requirements:
- Use only SELECT statements
- Return only the SQL query without explanation
- Ensure the query is safe and read-only
- Use proper JOIN conditions if multiple tables are needed

SQL Query:"""
        
        try:
            response = llm.invoke(prompt)
            sql_query = response.content.strip()
            
            if sql_query.startswith('```sql'):
                sql_query = sql_query.split('```sql')[1].split('```')[0].strip()
            elif sql_query.startswith('```'):
                sql_query = sql_query.split('```')[1].split('```')[0].strip()
            
            logger.info(f"Generated SQL query from natural language")
            return sql_query
            
        except Exception as e:
            logger.error(f"Error generating SQL: {str(e)}")
            raise ToolExecutionError(
                "Failed to generate SQL query",
                details={"error": str(e), "question": question}
            )
    
    def _format_schema_for_prompt(self, schema_info: Dict) -> str:
        schema_lines = []
        for table_name, table_info in schema_info.items():
            schema_lines.append(f"\nTable: {table_name}")
            schema_lines.append("Columns:")
            for col in table_info['columns']:
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                schema_lines.append(f"  - {col['name']} ({col['type']}) {nullable}")
            if table_info['primary_keys']:
                schema_lines.append(f"Primary Keys: {', '.join(table_info['primary_keys'])}")
        
        return '\n'.join(schema_lines)
    
    def get_langchain_tools(self) -> List[Tool]:
        schema_info = self.get_schema_info()
        
        def query_database(question: str) -> str:
            try:
                sql_query = self.generate_sql_from_natural_language(question, schema_info)
                result = self.execute_query(sql_query)
                return str(result['data'])
            except Exception as e:
                return f"Error: {str(e)}"
        
        def get_schema() -> str:
            return self._format_schema_for_prompt(schema_info)
        
        return [
            Tool(
                name="query_database",
                func=query_database,
                description="Execute a natural language query against the SQL database. "
                           "Input should be a question in natural language. "
                           "Returns the query results as a list of dictionaries."
            ),
            Tool(
                name="get_database_schema",
                func=get_schema,
                description="Get the schema information of the database including tables, "
                           "columns, types, and relationships. Use this to understand "
                           "the database structure before querying."
            )
        ]
