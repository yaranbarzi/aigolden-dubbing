# AI Dubbing Tool (ابزار دوبله هوشمند)

ابزاری برای دوبله خودکار ویدیو با استفاده از هوش مصنوعی

## پیش‌نیازها

1. نصب Python 3.x
   - از [سایت رسمی پایتون](https://www.python.org/downloads/) دانلود و نصب کنید
   - در هنگام نصب گزینه "Add Python to PATH" را فعال کنید

2. نصب FFmpeg
   - برای Windows: 
     - نصب [Chocolatey](https://chocolatey.org/install)
     - اجرای دستور: `choco install ffmpeg`
   - برای Linux:
     - `sudo apt update && sudo apt install ffmpeg`
   - برای Mac:
     - نصب [Homebrew](https://brew.sh/)
     - اجرای دستور: `brew install ffmpeg`

3. نصب Rubberband
   - برای Windows: `choco install rubberband-cli`
   - برای Linux: `sudo apt install rubberband-cli`
   - برای Mac: `brew install rubberband`

## نصب و راه‌اندازی

1. دانلود پروژه:
```bash
git clone https://github.com/yaranbarzi/aigolden-dubbing
cd aigolden-dubbing
```

2. نصب کتابخانه‌های مورد نیاز:
```bash
pip install -r requirements.txt
```

3. اجرای برنامه:
```bash
python app.py
```

4. باز کردن مرورگر و رفتن به آدرس نمایش داده شده (معمولاً http://127.0.0.1:7860)

## نحوه استفاده

1. در تب اول: آپلود ویدیو یا وارد کردن لینک یوتیوب
2. در تب دوم: استخراج متن با Whisper یا آپلود زیرنویس
3. در تب سوم: ترجمه متن با هوش مصنوعی یا آپلود ترجمه
4. در تب چهارم: انتخاب صدا و تولید گفتار
5. در تب پنجم: ساخت ویدیوی نهایی با دوبله

## نکات مهم

- برای ترجمه با هوش مصنوعی نیاز به API Key گوگل دارید
- حتماً FFmpeg و Rubberband را قبل از اجرای برنامه نصب کنید
- در صورت بروز مشکل، از تب Cleanup برای پاکسازی فایل‌های قبلی استفاده کنید

## پشتیبانی از زبان‌ها

- فارسی (FA)
- انگلیسی (EN)
- عربی (AR)
- چینی (ZH)
- فرانسوی (FR)
- آلمانی (DE)
- ایتالیایی (IT)
- ژاپنی (JA)
- کره‌ای (KO)
- روسی (RU)
- اسپانیایی (ES)
