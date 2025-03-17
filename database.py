import pyodbc
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from sentence_transformers import SentenceTransformer
import uuid

# Cấu hình kết nối SQL Server
DB_CONFIG = {
    "server": "CHAUNGUYENPHAT",
    "database": "DATN_FASHION_SHOP",
    "username": "sa",
    "password": "123",
    "driver": "{ODBC Driver 17 for SQL Server}"
}

# Kết nối với Qdrant
client = QdrantClient(
    url="https://bcde43c2-f65a-4b07-8724-000a34d547ca.us-east4-0.gcp.cloud.qdrant.io",
    api_key="API"
)
model = SentenceTransformer("all-MiniLM-L6-v2")

# Tạo collection nếu chưa có
COLLECTION_NAME = "product_vectors"

def create_qdrant_collection():
    """Tạo collection trong Qdrant nếu chưa tồn tại"""
    existing_collections = client.get_collections().collections
    collection_names = [col.name for col in existing_collections]
    
    if COLLECTION_NAME not in collection_names:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config={"size": 384, "distance": "Cosine"}
        )
        print(f"✅ Collection '{COLLECTION_NAME}' đã được tạo!")
    else:
        print(f"✅ Collection '{COLLECTION_NAME}' đã tồn tại.")

create_qdrant_collection()

def get_connection():
    """Kết nối đến SQL Server"""
    conn = pyodbc.connect(
        f"DRIVER={DB_CONFIG['driver']};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"UID={DB_CONFIG['username']};"
        f"PWD={DB_CONFIG['password']}"
    )
    return conn

def get_all_products():
    """Lấy dữ liệu sản phẩm từ SQL Server"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            pt.name, 
            CAST(pt.description AS NVARCHAR(MAX)),  -- Đảm bảo description là string
            pt.material, 
            pt.care, 
            p.base_price, 
            p.status, 
            p.is_active, 
            pt.language_id, 
            pt.product_id
        FROM 
            products_translations pt
        JOIN 
            products p ON pt.product_id = p.id
        WHERE 
            p.is_active = 1;
    """)
    
    products = cursor.fetchall()
    conn.close()

    if not products:
        return {}

    product_dict = {}
    for row in products:
        name, description, material, care, base_price, status, is_active, language_id, product_id = row

        # Kiểm tra nếu description là None hoặc int, chuyển thành string
        if not isinstance(description, str):
            description = str(description) if description is not None else "Không có mô tả"

        product_info = {
            "id": str(product_id),
            "name": name.strip() if name else "Không rõ",
            "description": description.strip(),  # Luôn đảm bảo là chuỗi
            "material": material.strip() if material else "Không có thông tin",
            "care": care.strip() if care else "Không có thông tin",
            "price": base_price if base_price else "Chưa có giá",
            "status": status.strip() if status else "Không rõ",
            "is_active": bool(is_active)
        }
        
        if language_id not in product_dict:
            product_dict[language_id] = []

        # Đảm bảo `product_info` là dictionary, không phải số nguyên
        if isinstance(product_info, dict):
            product_dict[language_id].append(product_info)
        else:
            print(f"❌ LỖI: `product_info` không phải dictionary! Dữ liệu lỗi: {product_info}")

    return product_dict

def auto_index_new_products():
    """Tự động index sản phẩm mới vào Qdrant."""
    products_dict = get_all_products()
    new_products = []

    for lang, products in products_dict.items():
        for product in products:
            # Kiểm tra xem sản phẩm đã có trong Qdrant chưa
            search_result = client.search(
                collection_name=COLLECTION_NAME,
                query_vector=model.encode(product["description"]).tolist(),
                limit=1
            )
            if not search_result:  # Nếu sản phẩm chưa có, thêm vào danh sách mới
                new_products.append(product)

    if new_products:
        print(f"📢 Tìm thấy {len(new_products)} sản phẩm mới. Đang cập nhật Qdrant...")
        index_products_to_qdrant(new_products)
    else:
        print("✅ Không có sản phẩm mới cần cập nhật.")



def index_products_to_qdrant():
    """Đưa dữ liệu từ SQL Server lên Qdrant"""
    products_dict = get_all_products()

    points = []
    for lang, products in products_dict.items():
        for product in products:
            if not isinstance(product, dict):
                print(f"❌ LỖI: `product` không phải dictionary! Dữ liệu lỗi: {product}")
                continue  # Bỏ qua dữ liệu lỗi

            # Kiểm tra `description` có bị rỗng không
            description = product["description"] if product["description"] else "Không có mô tả"
            
            vector = model.encode(description).tolist()
            points.append(PointStruct(id=str(uuid.uuid4()), vector=vector, payload=product))

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )
    print(f"✅ Đã index {len(points)} sản phẩm vào Qdrant.")



# Chạy để đưa dữ liệu lên Qdrant
index_products_to_qdrant()
