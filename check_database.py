"""
PostgreSQL 데이터베이스에서 RAG 관련 테이블 확인
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def check_database():
    """데이터베이스 연결 및 테이블 확인"""
    try:
        # PostgreSQL 연결
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=os.getenv('POSTGRES_PORT', '5432'),
            database=os.getenv('POSTGRES_DB', 'dungeontalk'),
            user=os.getenv('POSTGRES_USER', 'postgres'),
            password=os.getenv('POSTGRES_PASSWORD')
        )
        
        cursor = conn.cursor()
        
        print("=" * 60)
        print("PostgreSQL 데이터베이스 상태 확인")
        print("=" * 60)
        
        # 1. 스키마 확인
        print("\n사용 가능한 스키마:")
        cursor.execute("SELECT schema_name FROM information_schema.schemata ORDER BY schema_name;")
        schemas = cursor.fetchall()
        for schema in schemas:
            print(f"  - {schema[0]}")
        
        # 2. dungeontalk_rag 스키마 테이블 확인
        print("\ndungeontalk_rag 스키마 테이블:")
        cursor.execute("""
            SELECT table_name, table_type 
            FROM information_schema.tables 
            WHERE table_schema = 'dungeontalk_rag'
            ORDER BY table_name;
        """)
        rag_tables = cursor.fetchall()
        
        if rag_tables:
            for table_name, table_type in rag_tables:
                print(f"  - {table_name} ({table_type})")
                
                # 테이블 구조 확인
                cursor.execute(f"""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_schema = 'dungeontalk_rag' AND table_name = '{table_name}'
                    ORDER BY ordinal_position;
                """)
                columns = cursor.fetchall()
                for col_name, data_type, nullable in columns:
                    print(f"    └── {col_name}: {data_type} {'(NULL)' if nullable == 'YES' else '(NOT NULL)'}")
                
                # 데이터 개수 확인
                try:
                    cursor.execute(f'SELECT COUNT(*) FROM dungeontalk_rag."{table_name}";')
                    count = cursor.fetchone()[0]
                    print(f"    └── 데이터 개수: {count}개")
                    
                    # 샘플 데이터 확인 (메타데이터 포함)
                    if count > 0 and table_name == 'documents_with_metadata':
                        cursor.execute(f'SELECT cmetadata FROM dungeontalk_rag."{table_name}" LIMIT 3;')
                        samples = cursor.fetchall()
                        print(f"    └── 샘플 메타데이터:")
                        for i, sample in enumerate(samples, 1):
                            if sample[0]:
                                metadata = sample[0]
                                world_type = metadata.get('world_type', 'Unknown')
                                doc_type = metadata.get('doc_type', 'Unknown')
                                print(f"      {i}. 세계관: {world_type}, 타입: {doc_type}")
                except Exception as e:
                    print(f"    └── 데이터 조회 오류: {e}")
        else:
            print("  테이블 없음")
        
        # 3. public 스키마의 langchain 관련 테이블 확인
        print("\npublic 스키마의 langchain 테이블:")
        cursor.execute("""
            SELECT table_name, table_type 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name LIKE '%langchain%'
            ORDER BY table_name;
        """)
        langchain_tables = cursor.fetchall()
        
        if langchain_tables:
            for table_name, table_type in langchain_tables:
                print(f"  - {table_name} ({table_type})")
                try:
                    cursor.execute(f'SELECT COUNT(*) FROM public."{table_name}";')
                    count = cursor.fetchone()[0]
                    print(f"    └── 데이터 개수: {count}개")
                except Exception as e:
                    print(f"    └── 데이터 조회 오류: {e}")
        else:
            print("  langchain 관련 테이블 없음")
        
        # 4. 전체 데이터베이스 크기
        print("\n데이터베이스 정보:")
        cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()));")
        db_size = cursor.fetchone()[0]
        print(f"  데이터베이스 크기: {db_size}")
        
        conn.close()
        print("\n데이터베이스 확인 완료")
        
    except Exception as e:
        print(f"데이터베이스 연결 오류: {e}")
        return False
    
    return True

if __name__ == "__main__":
    check_database()