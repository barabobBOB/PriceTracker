from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time


def crawling():
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    baseurl = 'https://www.coupang.com/np/categories/194286?listSize=120&brand=&offerCondition=&filterType=&isPriceRange=false&minPrice=&maxPrice=&page=1&channel=user&fromComponent=N&selectedPlpKeepFilter=&sorter=bestAsc&filter=&component=194186&rating=0'
    driver.get(baseurl)

    # 페이지 로딩 대기
    time.sleep(3)

    items = driver.find_elements(By.CLASS_NAME, 'baby-product-link')
    cnt = 1
    for item in items:
        try:
            title = item.find_element(By.CLASS_NAME, 'name').text.strip()
            price = item.find_element(By.CLASS_NAME, 'price-value').text.strip()
            per_price = item.find_element(By.CLASS_NAME, 'unit-price').text.strip()
            star = item.find_element(By.CLASS_NAME, 'rating').text.strip()
            review_cnt = item.find_element(By.CLASS_NAME, 'rating-total-count').text.strip()

            print(f'상품번호: {cnt}')
            print(f'상품명: {title}')
            print(f'가격: {price}원')
            print(f'100g당 가격: {per_price}')
            print(f'별점: {star}')
            print(f'리뷰수: {review_cnt}')
            print('-' * 50)
            cnt += 1

        except:
            continue

    # 브라우저 종료
    driver.quit()


if __name__ == '__main__':
    crawling()
