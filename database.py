import pyodbc

# Cấu hình kết nối SQL Server
DB_CONFIG = {
    "server": "CHAUNGUYENPHAT",
    "database": "DATN_FASHION_SHOP",
    "username": "sa",
    "password": "123",
    "driver": "{ODBC Driver 17 for SQL Server}"
}

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
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            p.id AS product_id,
            p.created_at, p.created_by, p.updated_at, p.updated_by,
            p.base_price, p.is_active, p.status, 
            p.promotion_id, p.review_id,

            pt.id AS translation_id,
            pt.name, pt.description, pt.material, pt.care,
            pt.language_id,

            v.id AS variant_id,
            v.sale_price,
            av_color.value_name AS color,
            av_color.value_img AS color_image,
            av_size.value_name AS size

        FROM dbo.products p
        LEFT JOIN dbo.products_translations pt ON pt.product_id = p.id
        LEFT JOIN dbo.product_variants v ON v.product_id = p.id
        LEFT JOIN dbo.attributes_values av_color ON v.color_value_id = av_color.id
        LEFT JOIN dbo.attributes_values av_size ON v.size_value_id = av_size.id
        WHERE p.is_active = 1
    """)

    rows = cursor.fetchall()
    conn.close()

    products_by_language = {}

    for row in rows:
        (
            product_id, created_at, created_by, updated_at, updated_by,
            base_price, is_active, status, promotion_id, review_id,
            translation_id, name, description, material, care, language_id,
            variant_id, sale_price, color, color_image, size
        ) = row

        product_info = {
            "product_id": product_id,
            "created_at": created_at,
            "created_by": created_by,
            "updated_at": updated_at,
            "updated_by": updated_by,
            "base_price": base_price,
            "is_active": is_active,
            "status": status,
            "promotion_id": promotion_id,
            "review_id": review_id,
            "translation_id": translation_id,
            "name": name.strip() if name else "Không rõ",
            "description": description if description else "Không có mô tả",
            "material": material if material else "Không rõ",
            "care": care if care else "Không có thông tin",
            "language_id": language_id,
            "variants": [],
        }

        # Tạo biến thể nếu có
        if variant_id:
            variant_info = {
                "variant_id": variant_id,
                "sale_price": sale_price,
                "color": color,
                "color_image": color_image,
                "size": size
            }
            product_info["variants"].append(variant_info)

        if language_id not in products_by_language:
            products_by_language[language_id] = {}

        # Ghép biến thể nếu sản phẩm đã tồn tại
        if product_id in products_by_language[language_id]:
            products_by_language[language_id][product_id]["variants"].extend(product_info["variants"])
        else:
            products_by_language[language_id][product_id] = product_info

    # Đưa về list thay vì dict theo product_id
    for lang_id in products_by_language:
        products_by_language[lang_id] = list(products_by_language[lang_id].values())

    return products_by_language
