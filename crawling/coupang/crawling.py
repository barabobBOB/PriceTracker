from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


class CoupangCrawler:
    def __init__(self, categories_id, max_pages=5):
        self.categories_id = categories_id
        self.max_pages = max_pages
        self.chrome_options = Options()
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    def start_driver(self):
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.chrome_options)

    def crawl_category(self, category_id):
        for page in range(1, self.max_pages + 1):
            self.start_driver()  # 페이지 로드마다 WebDriver 재시작
            baseurl = (f'https://www.coupang.com/np/categories/{category_id}'
                       f'?listSize=120&brand=&offerCondition=&filterType='
                       f'&isPriceRange=false&minPrice=&maxPrice=&channel=user'
                       f'&fromComponent=N&selectedPlpKeepFilter=&sorter=bestAsc&filter=&component=194186&rating=0'
                       f'&page={page}')

            self.driver.get(baseurl)

            try:
                # 특정 요소가 로드될 때까지 대기
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'baby-product-link'))
                )
            except Exception as e:
                print(f"페이지 로드 오류: 카테고리 {category_id}, 페이지 {page}")
                print(f"Error: {e}")
                self.driver.quit()
                break

            items = self.driver.find_elements(By.CLASS_NAME, 'baby-product-link')
            if not items:
                print(f"더 이상 항목이 없습니다: 카테고리 {category_id}, 페이지 {page}")
                self.driver.quit()
                break

            cnt = 1
            for item in items:
                try:
                    number = item.get_attribute('data-product-id')
                    title = item.find_element(By.CLASS_NAME, 'name').text.strip()
                    price = item.find_element(By.CLASS_NAME, 'price-value').text.strip()
                    per_price = item.find_element(By.CLASS_NAME, 'unit-price').text.strip()
                    star = item.find_element(By.CLASS_NAME, 'rating').text.strip()
                    review_cnt = item.find_element(By.CLASS_NAME, 'rating-total-count').text.strip()

                    print(f'카테고리 ID: {category_id}')
                    print(f'페이지 상품 번호: {number}')
                    print(f'페이지 상품 카운트: {cnt}')
                    print(f'상품명: {title}')
                    print(f'가격: {price}원')
                    print(f'100g당 가격: {per_price}')
                    print(f'별점: {star}')
                    print(f'리뷰수: {review_cnt}')
                    print('-' * 50)
                    cnt += 1

                except Exception as e:
                    print(f"상품 정보 추출 오류: {e}")
                    continue

            self.driver.quit()

    def crawl(self):
        for category_id in self.categories_id:
            self.crawl_category(category_id)

    def close(self):
        self.driver.quit()


if __name__ == '__main__':
    categories_id = [
        194286, 194287, 194290, 194291, 194292, 194296, 194302, 194303, 194310, 194311,
        194312, 194313, 194319, 194322, 194324, 194328, 194329, 194330, 194333, 194334,
        194335, 194340, 194341, 194344, 194436, 194437, 194438, 194447, 194448, 194456,
        194460, 194464, 194465, 194476, 194482, 194487, 194488, 194492, 194507, 194514,
        194515, 194520, 194524, 194527, 194539, 194540, 194561, 194562, 194564, 194571,
        194572, 194577, 194578, 194579, 194586, 194587, 194588, 194589, 194590, 194694,
        194695, 194698, 194699, 194700, 194701, 194706, 194707, 194708, 194711, 194712,
        194713, 194730, 194731, 194732, 194733, 194736, 194737, 194738, 194742, 194743,
        194744, 194745, 194746, 194812
    ]

    crawler = CoupangCrawler(categories_id)
    crawler.crawl()
    crawler.close()
