# Vietnam Lottery Data Fetcher

Công cụ tự động thu thập dữ liệu xổ số từ ba miền của Việt Nam (Bắc, Trung, Nam).

## Tính năng

- Thu thập kết quả xổ số Miền Bắc (XSMB)
- Thu thập kết quả xổ số Miền Nam (XSMN)
- Thu thập kết quả xổ số Miền Trung (XSMT)
- Lưu trữ dữ liệu dưới dạng DataFrame
- Hỗ trợ thu thập dữ liệu theo khoảng thời gian

## Yêu cầu hệ thống

- Python 3.9 trở lên
- Các thư viện Python được liệt kê trong `requirements.txt`

## Cài đặt

1. Clone repository này về máy:
```bash
git clone https://github.com/[username]/vietnam-lottery.git
cd vietnam-lottery
```

2. Cài đặt các thư viện cần thiết:
```bash
pip install -r requirements.txt
```

## Cách sử dụng

### Thu thập dữ liệu

Script chính `fetch.py` cho phép thu thập dữ liệu từ cả ba miền. Bạn có thể chỉ định ngày bắt đầu và ngày kết thúc để thu thập dữ liệu.

Ví dụ để thu thập dữ liệu:

```python
from datetime import date
from src.fetch import fetch_xsmb, fetch_xsmn, fetch_xsmt

# Thu thập dữ liệu xổ số Miền Bắc
start_date = date(2023, 1, 1)
end_date = date(2023, 12, 31)
fetch_xsmb(start_date, end_date)

# Thu thập dữ liệu xổ số Miền Nam
fetch_xsmn(start_date, end_date)

# Thu thập dữ liệu xổ số Miền Trung
fetch_xsmt(start_date, end_date)
```

## Cấu trúc dự án

```
vietnam-lottery/
├── requirements.txt    # Các thư viện Python cần thiết
├── src/
│   ├── fetch.py       # Script chính để thu thập dữ liệu
│   ├── lotterymb.py   # Module xử lý xổ số Miền Bắc
│   ├── lotterymn.py   # Module xử lý xổ số Miền Nam
│   └── lotterymt.py   # Module xử lý xổ số Miền Trung
```

## Thư viện sử dụng

- beautifulsoup4: Phân tích cú pháp HTML
- cloudscraper: Bypass các protection của website
- numpy: Xử lý số liệu
- pandas: Xử lý và lưu trữ dữ liệu
- pydantic: Kiểm tra và xác thực dữ liệu

## Đóng góp

Mọi đóng góp đều được hoan nghênh. Vui lòng tạo issue hoặc pull request nếu bạn muốn cải thiện dự án.

## License

[Thêm thông tin về license của dự án]
