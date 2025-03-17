import requests
import time
from langchain_core.prompts import ChatPromptTemplate
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from database import get_all_products

# Kết nối với Qdrant
QDRANT_HOST = "https://bcde43c2-f65a-4b07-8724-000a34d547ca.us-east4-0.gcp.cloud.qdrant.io"
client = QdrantClient(url=QDRANT_HOST, api_key="API")
model = SentenceTransformer("all-MiniLM-L6-v2")

COLLECTION_NAME = "product_vectors"

class ProductCache:
    def __init__(self, refresh_time=300):  # Làm mới mỗi 5 phút
        self.products_info = {}
        self.last_refresh = 0
        self.refresh_time = refresh_time

    def get_products(self):
        if not self.products_info or time.time() - self.last_refresh > self.refresh_time:
            print("🔄 Refreshing product data from database...")
            self.products_info = get_all_products()
            self.last_refresh = time.time()
        return self.products_info
    

class ChatTogether:
    product_cache = ProductCache()
        
    def __init__(self):
        self.api_key = "your_together_ai_api_key"
        self.model = "meta-llama/Meta-Llama-3-8B-Instruct-Turbo"
        self.products_info = ChatTogether.product_cache.get_products()

    def chat(self, user_input, language_id=1):
        lang_map = {1: "vnd/vi", 2: "usd/en", 3: "jpy/jp"}
        lang_path = lang_map.get(language_id, "usd/en")

        query_vector = model.encode(user_input).tolist()

        search_results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            query_filter=None,
            limit=5,
            with_payload=True
        )

        if not search_results or len(search_results) == 0:
            return self.ask_together_ai(user_input, language_id)

        response = "Dưới đây là các sản phẩm phù hợp:\n"
        for result in search_results:
            product = result.payload
            if "name" in product:
                product_url = f"http://localhost:4200/client/{lang_map.get(product.get('language_id', 2), 'usd/en')}/product?name={product.get('name', '').replace(' ', '%20')}"
                response += f"\n🔹 {product.get('name', 'Không rõ')} - Giá: {product.get('price', 'Chưa có giá')} VND\nXem tại: {product_url}\n"

        return response

    def ask_together_ai(self, user_input, language_id):
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        messages = [{"role": "user", "content": user_input}]
        payload = {"model": self.model, "messages": messages, "temperature": 0.7}

        try:
            response = requests.post("https://api.together.ai/v1/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as e:
            return f"⚠ Lỗi gọi API Together AI: {e}"

    def get_prompt(self):
        """Tạo prompt để AI hiểu danh sách sản phẩm từ database."""
        self.products_info = ChatTogether.product_cache.get_products()  # Cập nhật dữ liệu trước khi tạo prompt

        product_descriptions = ""
        for lang, products in self.products_info.items():
            title = {
                1: "--- Sản phẩm tiếng Việt ---",
                2: "--- Products in English ---",
                3: "--- 日本語の商品 ---"
            }.get(lang, "--- Products ---")

            product_descriptions += f"\n{title}\n"
            for product in products:
                if isinstance(product, dict):
                    product_descriptions += (
                        f"\n- {product.get('name', 'Không rõ')}: "
                        f"{product.get('description', 'Không có mô tả')}, "
                        f"Giá: {product.get('price', 'Chưa có giá')} VND."
                    )

        return f"""Bạn là trợ lý bán hàng thông minh của cửa hàng trực tuyến. Hãy giúp khách hàng bằng cách:
1. Giới thiệu về sản phẩm mà chúng tôi bán.
2. Gợi ý sản phẩm dựa trên nhu cầu của khách hàng.
3. Nếu khách hàng hỏi về sản phẩm, hãy kiểm tra danh sách có sẵn và cung cấp thông tin chi tiết.
Danh sách sản phẩm có trong database:
{product_descriptions}

Hãy trả lời ngắn gọn, chuyên nghiệp và thân thiện!"""
