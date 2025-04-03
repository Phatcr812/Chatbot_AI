import requests
import urllib.parse
import re
import random
from langchain_core.messages import HumanMessage, AIMessage
from database import get_all_products, get_connection


class TogetherLLM:
    def __init__(self, api_key="tgp_v1_pBfE1wXKZ6Sm-oHiiILbg_ySNpW1Avgo8gQZ32siQ98", model="mistralai/Mistral-7B-Instruct-v0.1"):
        self.api_key = api_key
        self.model = model

    def generate(self, messages):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7
        }

        response = requests.post("https://api.together.xyz/v1/chat/completions", headers=headers, json=payload)

        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return f"⚠ Lỗi gọi Together AI: {response.text}"


class SimpleChatbot:
    def detect_language(self, text):
        try:
            lang = detect(text)
            return "vi" if lang == "vi" else "en"
        except:
            return "vi"
    
    def __init__(self):
        self.llm = TogetherLLM()
        self.products_data = get_all_products()
        self.available_colors = set()
        self.available_sizes = set()
        self.color_vn_to_en = {
            "đen": "black", "trắng": "white", "xanh": "blue", "nâu": "brown", "hồng": "pink",
            "tím": "purple", "vàng": "yellow", "xám": "gray", "xanh navy": "navy", "đỏ": "red",
        }
        self.load_attributes_from_db()

    def load_attributes_from_db(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value_name, attribute_id FROM dbo.attributes_values")
        rows = cursor.fetchall()
        conn.close()

        for name, attr_id in rows:
            name = name.strip().lower()
            if attr_id == 1:
                self.available_sizes.add(name)
            elif attr_id == 2:
                self.available_colors.add(name)

    def extract_filters_from_input(self, text):
        keyword = ""
        color = None
        min_price = None
        max_price = None

        text = text.lower()
        words = text.split()

        # Tìm keyword trong tên sản phẩm (tự do)
        for w in words:
            for p_list in self.products_data.values():
                for p in p_list:
                    if w in p.get("name", "").lower():
                        keyword = w
                        break

        # Tìm màu (việt hoàc anh)
        for w in words:
            vn_color = self.color_vn_to_en.get(w)
            if w in self.available_colors or (vn_color and vn_color in self.available_colors):
                color = w
                break

        # Tìm khoảng giá
        price_numbers = re.findall(r"\d+[.,]?\d*\s*(tr|triệu|k|nghìn|ngàn)?", text)
        price_values = []
        for p in price_numbers:
            match = re.match(r"(\d+[.,]?\d*)\s*(tr|triệu|k|nghìn|ngàn)?", p)
            if match:
                num = float(match.group(1).replace(",", "."))
                unit = match.group(2)
                if unit in ["tr", "triệu"]:
                    num *= 1_000_000
                elif unit in ["k", "nghìn", "ngàn"]:
                    num *= 1_000
                price_values.append(int(num))

        if len(price_values) == 1:
            min_price = price_values[0] - 500_000
            max_price = price_values[0] + 500_000
        elif len(price_values) >= 2:
            min_price, max_price = sorted(price_values[:2])

        return {
            "keyword": keyword,
            "color": color,
            "min_price": min_price,
            "max_price": max_price
        }

    def filter_products(self, filters, language_id=1):
        keyword = filters["keyword"]
        color = filters["color"]
        min_price = filters["min_price"]
        max_price = filters["max_price"]

        result = []
        for p in self.products_data.get(language_id, []):
            name = p["name"].lower()
            desc = p.get("description", "").lower()

            # So khớp keyword
            keyword_matched = keyword in name if keyword else True

            # So khớp màu
            color_matched = True
            if color:
                color_vn = self.color_vn_to_en.get(color, color)
                color_in_variants = any(
                    color_vn in v.get("color", "").lower() for v in p.get("variants", [])
                )
                color_in_name = color in name or color in desc
                color_matched = color_in_variants or color_in_name

            # So khớp giá
            price_matched = True
            price_candidates = []
            for v in p.get("variants", []):
                sale_price = v.get("sale_price")
                if sale_price and isinstance(sale_price, (int, float)):
                    price_candidates.append(sale_price)
            if not price_candidates:
                base_price = p.get("base_price", 0)
                if isinstance(base_price, (int, float)):
                    price_candidates.append(base_price)
            if min_price is not None and max_price is not None:
                price_matched = any(min_price <= price <= max_price for price in price_candidates)

            if keyword_matched and color_matched and price_matched:
                result.append(p)

        return result[:5]

    def build_product_response(self, products):
        lines = []
        for product in products:
            name = product["name"]
            encoded_name = urllib.parse.quote(name)
            link = f"http://localhost:4200/client/usd/en/product?name={encoded_name}&isActive=true&page=0&size=10&sortBy=id&sortDir=asc"
            lines.append(f"- {name}\n🔗 {link}\n")
        return "\n".join(lines)

    def chat(self, user_input, chat_history):
        filters = self.extract_filters_from_input(user_input)
        matching = self.filter_products(filters)

        # Trường hợp có keyword => đang nhắc đến sản phẩm => đưa gợi ý
        if filters["keyword"] and matching:
            intros = [
                "🎉 Dưới đây là một số sản phẩm phù hợp với nhu cầu của bạn:",
                "✨ Gợi ý một vài sản phẩm bạn có thể quan tâm:",
                "🛍️ Một số lựa chọn chúng tôi tìm thấy dựa trên điều bạn đã nói:"
            ]
            intro = random.choice(intros)
            return intro + "\n\n" + self.build_product_response(matching)

        # Ngược lại, không nói rõ về sản phẩm => giao tiếp bình thường
        messages = [
            {"role": "system", "content": """
                  Bạn là một chuyên gia chăm sóc khách hàng của trang web brand với nhiều năm kinh nghiệm, luôn thấu hiểu nhu cầu của khách hàng và biết cách giải quyết vấn đề một cách chuyên nghiệp, tận tâm. Hãy đóng vai là đại diện hỗ trợ của Brand. Nhiệm vụ của bạn là:
                    1. Giải quyết vấn đề một cách nhanh chóng, hiệu quả, và mang lại trải nghiệm tốt nhất cho khách hàng.
                    2. Duy trì thái độ tích cực, thân thiện, nhưng vẫn đảm bảo tính chuyên nghiệp.
                    3. Cung cấp các giải pháp thực tế, sáng tạo và phù hợp với từng tình huống cụ thể.
                    4. Đưa ra hướng dẫn rõ ràng, dễ hiểu để khách hàng cảm thấy được hỗ trợ tối đa.
                Hãy giúp tôi xử lý tình huống của khách hàng. Đưa ra lời phản hồi chi tiết, đầy đủ và mang lại sự hài lòng cao nhất cho khách hàng.
                """}
        ]
        for msg in chat_history:
            if isinstance(msg, HumanMessage):
                messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                messages.append({"role": "assistant", "content": msg.content})

        messages.append({"role": "user", "content": user_input})
        return self.llm.generate(messages)


def handle_input(chatbot: SimpleChatbot, user_input, chat_history):
    result = chatbot.chat(user_input, chat_history)
    chat_history.extend([
        HumanMessage(content=user_input),
        AIMessage(content=result),
    ])
    return result, chat_history
