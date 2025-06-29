import requests
from bs4 import BeautifulSoup
import json
import os

TOKEN = os.getenv('TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
LAST_ID_FILE = "last_sent_app.txt"

def read_last_sent_id():
    if not os.path.exists(LAST_ID_FILE):
        return None
    with open(LAST_ID_FILE, "r", encoding="utf-8") as f:
        return f.read().strip()

def write_last_sent_id(app_id):
    with open(LAST_ID_FILE, "w", encoding="utf-8") as f:
        f.write(app_id)

def get_app_icon_url(google_play_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    try:
        response = requests.get(google_play_url, headers=headers, timeout=20)
        if response.status_code != 200:
            return None
        soup = BeautifulSoup(response.text, 'html.parser')
        meta_img = soup.find('meta', property='og:image')
        if meta_img and meta_img.get('content'):
            return meta_img['content']
    except Exception:
        return None
    return None

def send_telegram_photo_with_button(token, chat_id, photo_url, caption, button_text, button_url):
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    keyboard = {
        "inline_keyboard": [[{"text": button_text, "url": button_url}]]
    }
    payload = {
        'chat_id': chat_id,
        'photo': photo_url,
        'caption': caption,
        'parse_mode': 'HTML',  # ضروري لتفعيل التنسيقات
        'reply_markup': json.dumps(keyboard)
    }
    response = requests.post(url, data=payload)
    return response.status_code, response.text

def get_all_apps():
    url = "https://www.app-sales.net/nowfree/"
    response = requests.get(url)
    if response.status_code != 200:
        return []
    soup = BeautifulSoup(response.text, 'html.parser')
    apps = []
    for app in soup.find_all('div', class_='sale-list-item'):
        app_name = app.find('p', class_='app-name').text.strip() if app.find('p', class_='app-name') else "غير متوفر"
        app_dev = app.find('p', class_='app-dev').text.strip() if app.find('p', class_='app-dev') else "غير متوفر"
        link_tag = app.find('div', class_='sale-list-action').find('a')
        app_link = link_tag['href'] if link_tag else None
        price_old_tag = app.find('div', class_='price-old')
        price_old = price_old_tag.text.strip() if price_old_tag else "غير متوفر"
        price_new_tag = app.find('div', class_='price-new')
        price_new = price_new_tag.text.strip() if price_new_tag else "غير متوفر"
        app_id = app_link.split("id=")[-1] if app_link and "id=" in app_link else app_name
        photo_url = get_app_icon_url(app_link) if app_link else None
        apps.append({
            "id": app_id,
            "name": app_name,
            "dev": app_dev,
            "link": app_link,
            "price_old": price_old,
            "price_new": price_new,
            "photo": photo_url
        })
    return apps

def main():
    last_sent_id = read_last_sent_id()
    apps = get_all_apps()
    if not apps:
        print("لم يتم العثور على تطبيقات.")
        return

    # تحديد التطبيقات الجديدة فقط بالترتيب من الأقدم للأحدث
    to_send = []
    if not last_sent_id:
        to_send = apps[::-1]
    else:
        found = False
        for app in reversed(apps):
            if found:
                to_send.append(app)
            elif app["id"] == last_sent_id:
                found = True
        if not found:
            to_send = apps[::-1]

    if not to_send:
        print("لا يوجد تطبيقات جديدة.")
        return

    for app in to_send:
        caption = (
            "\n"
            f"<b>التطبيق:</b> {app['name']} 📱\n"
            f"<b>المطور:</b> {app['dev']} ⚙️\n"
            f"<b>السعر القديم:</b> <del>{app['price_old']}</del> 💰\n"
            f"<b>السعر الحالي:</b> {app['price_new']} 💯\n"
            f"<b>العرض :</b> لفترة محدودة ⏳\n\n"
            f"<b>للدعم :</b> @bidjadraft"
        )
        status_code, response_text = send_telegram_photo_with_button(
            TOKEN, CHANNEL_ID, app["photo"], caption, "حمله الآن", app["link"]
        )
        print(f"تم الإرسال بحالة: {status_code}")
        if status_code == 200:
            write_last_sent_id(app["id"])

if __name__ == "__main__":
    main()
