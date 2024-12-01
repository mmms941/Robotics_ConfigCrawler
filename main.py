import requests
import threading
import json
import os 
import time
import random
import re
import base64
import geoip2.database
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from datetime import datetime
# مسیر دیتابیس GeoLite2
DB_PATH = "geolite2/GeoLite2-Country.mmdb"

requests.post = lambda url, **kwargs: requests.request(
    method="POST", url=url, verify=False, **kwargs
)
requests.get = lambda url, **kwargs: requests.request(
    method="GET", url=url, verify=False, **kwargs
)

requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

os.system('cls' if os.name == 'nt' else 'clear')

if not os.path.exists('configs.txt'):
    with open('configs.txt', 'w'): pass

def json_load(path):
    with open(path, 'r', encoding="utf-8") as file:
        list_content = json.load(file)
    return list_content
# تابع استخراج کشور از کانفیگ
def get_country_from_config(config_url):
    try:
        # باز کردن دیتابیس
        reader = geoip2.database.Reader(DB_PATH)

        # استخراج IP با استفاده از regex
        pattern = r"@([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)"  # الگو برای IP بعد از @
        match = re.search(pattern, config_url)
        
        if not match:
            return "Unknown", "unknown"  # اگر IP پیدا نشود

        server_ip = match.group(1)  # IP استخراج شده

        # جستجوی کشور بر اساس IP
        response = reader.country(server_ip)
        reader.close()

        # بررسی وجود مقادیر قبل از دسترسی
        country_name = response.country.name if response.country and response.country.name else "Unknown"
        country_code = response.country.iso_code.lower() if response.country and response.country.iso_code else "unknown"
        return country_name, country_code
    except Exception as e:
        print(f"Error in get_country_from_config: {e}")  # لاگ خطا برای اشکال‌زدایی
        return "Unknown", "unknown"  # در صورت بروز هرگونه خطا
def substring_del(string_list):
    list1 = list(string_list)
    list2 = list(string_list)
    list1.sort(key=lambda s: len(s), reverse=False)
    list2.sort(key=lambda s: len(s), reverse=True)
    out = list()
    for s1 in list1:
        for s2 in list2:
            if s1 in s2 and len(s1) < len(s2):
                out.append(s1)
                break
            if len(s1) >= len(s2):
                break
    out = list(set(string_list)-set(out))
    return out

tg_name_json = json_load('tg channels.json')
inv_tg_name_json = json_load('blacklist channels.json')

inv_tg_name_json[:] = [x for x in inv_tg_name_json if len(x) >= 5]
inv_tg_name_json = list(set(inv_tg_name_json)-set(tg_name_json))

thrd_pars = 5
pars_dp = 1

print(f'\nTotal channel names in tg channels.json         - {len(tg_name_json)}')
print(f'Total channel names in blacklist channels.json - {len(inv_tg_name_json)}')

use_inv_tc = 'n'

start_time = datetime.now()

if use_inv_tc == 'y':
    tg_name_json.extend(inv_tg_name_json)
    inv_tg_name_json.clear()
    tg_name_json = list(set(tg_name_json))
    tg_name_json = sorted(tg_name_json)

sem_pars = threading.Semaphore(thrd_pars)

config_all = list()
tg_name = list()
new_tg_name_json = list()

print(f'Try get new tg channels name from proxy configs in configs.txt...')

with open("configs.txt", "r", encoding="utf-8") as config_all_file:
    config_all = config_all_file.readlines()

pattern_telegram_user = r'(?:@)(\w{5,})|(?:%40)(\w{5,})|(?:t\.me\/)(\w{5,})|(?:t\.me%2F)(\w{5,})|(?:t\.me-)(\w{5,})'
pattern_datbef = re.compile(r'(?:data-before=")(\d*)')

for config in config_all:
    if config.startswith('vmess://'):
        try:
            config = base64.b64decode(config[8:]).decode("utf-8")
        except:
            pass
    if config.startswith('ssr://'):
        try:
            config = base64.b64decode(config[6:]).decode("utf-8")
        except:
            pass
    matches_usersname = re.findall(pattern_telegram_user, config, re.IGNORECASE)
    try:
        matches_usersname = re.findall(pattern_telegram_user, base64.b64decode(config).decode("utf-8"), re.IGNORECASE)
    except:
        pass
    
    for index, element in enumerate(matches_usersname):
        if element[0] != '':
            tg_name.append(element[0].lower().encode('ascii', 'ignore').decode())
        if element[1] != '':
            tg_name.append(element[1].lower().encode('ascii', 'ignore').decode())
        if element[2] != '':
            tg_name.append(element[2].lower().encode('ascii', 'ignore').decode())             
        if element[3] != '':
            tg_name.append(element[3].lower().encode('ascii', 'ignore').decode()) 
        if element[4] != '':
            tg_name.append(element[4].lower().encode('ascii', 'ignore').decode())

tg_name[:] = [x for x in tg_name if len(x) >= 5]
tg_name_json[:] = [x for x in tg_name_json if len(x) >= 5]    
tg_name = list(set(tg_name))
print(f'\nFound tg channel names - {len(tg_name)}')
print(f'Total old names        - {len(tg_name_json)}')
tg_name_json.extend(tg_name)
tg_name_json = list(set(tg_name_json))
tg_name_json = sorted(tg_name_json)
print(f'In the end, new names  - {len(tg_name_json)}')

with open('tg channels.json', 'w', encoding="utf-8") as telegram_channels_file:
    json.dump(tg_name_json, telegram_channels_file, indent = 4)

print(f'\nSearch for new names is over - {str(datetime.now() - start_time).split(".")[0]}')

print(f'\nStart Parsing...\n')

def process(i_url):
    sem_pars.acquire()
    html_pages = list()
    cur_url = i_url
    god_tg_name = False
    for itter in range(1, pars_dp + 1):
        while True:
            try:
                response = requests.get(f'https://t.me/s/{cur_url}')
            except:
                time.sleep(random.randint(5, 25))
                pass
            else:
                if itter == pars_dp:
                    print(f'{tg_name_json.index(i_url) + 1} of {walen} - {i_url}')
                html_pages.append(response.text)
                last_datbef = re.findall(pattern_datbef, response.text)
                break
        if not last_datbef:
            break
        cur_url = f'{i_url}?before={last_datbef[0]}'

    for page in html_pages:
        soup = BeautifulSoup(page, 'html.parser')
        code_tags = soup.find_all(class_='tgme_widget_message_text')
        time_tags = soup.find_all(class_='tgme_widget_message_date')  # استخراج تگ‌های مربوط به زمان

        for code_tag, time_tag in zip(code_tags, time_tags):
            code_content2 = str(code_tag).split('<br/>')
            time_content = time_tag.find('time')['datetime']  # استخراج زمان ارسال پیام

            # تبدیل زمان به فرمت دلخواه (YYYY/MM/DD HH:MM)
            time_obj = datetime.fromisoformat(time_content.replace('Z', ''))  # تبدیل به شیء datetime
            formatted_time = time_obj.strftime('%Y/%m/%d %H:%M')  # فرمت دلخواه

            for code_content in code_content2:
                if any(proto in code_content for proto in ["vless://", "ss://", "vmess://", "trojan://", "tuic://"]):
                    codes.append((re.sub(htmltag_pattern, '', code_content), formatted_time))  # ذخیره کانفیگ و زمان ارسال
                    new_tg_name_json.append(i_url)
                    god_tg_name = True
    if not god_tg_name:
        inv_tg_name_json.append(i_url)
    sem_pars.release()

htmltag_pattern = re.compile(r'<.*?>')

codes = list()

walen = len(tg_name_json)
for url in tg_name_json:
    threading.Thread(target=process, args=(url,)).start()
    
while threading.active_count() > 1:
    time.sleep(1)

print(f'\nParsing completed - {str(datetime.now() - start_time).split(".")[0]}')

print(f'\nStart check and remove duplicate from parsed configs...')

codes = list(set(codes))

processed_codes = list()

for idx, (config, time_sent) in enumerate(codes, start=1):  # حالا codes شامل (config, time_sent) است
    part = config  # فقط کانفیگ را می‌گیریم، نه tuple

    # حالا می‌توانیم روی part که یک رشته است، از re.sub استفاده کنیم
    part = re.sub('%0A', '', part)
    part = re.sub('%250A', '', part)
    part = re.sub('%0D', '', part)
    part = requests.utils.unquote(requests.utils.unquote(part)).strip()
    part = re.sub(' ', '', part)
    part = re.sub(r'\x00', '', part)
    part = re.sub(r'\x01', '', part)
    part = re.sub('amp;', '', part)
    part = re.sub('�', '', part)
    part = re.sub('fp=firefox', 'fp=chrome', part)
    part = re.sub('fp=safari', 'fp=chrome', part)
    part = re.sub('fp=edge', 'fp=chrome', part)
    part = re.sub('fp=360', 'fp=chrome', part)
    part = re.sub('fp=qq', 'fp=chrome', part)
    part = re.sub('fp=ios', 'fp=chrome', part)
    part = re.sub('fp=android', 'fp=chrome', part)
    part = re.sub('fp=randomized', 'fp=chrome', part)
    part = re.sub('fp=random', 'fp=chrome', part)

    # حالا برای هر نوع کانفیگ پردازش را انجام می‌دهیم
    if "vmess://" in part:
        part = f'vmess://{part.split("vmess://")[1]}'
        processed_codes.append(part.strip())
        continue
    elif "vless://" in part:
        part = f'vless://{part.split("vless://")[1]}'
        if "@" in part and ":" in part[8:]:
            processed_codes.append(part.strip())
        continue
    elif "ss://" in part:
        part = f'ss://{part.split("ss://")[1]}'
        if ';;' in part: 
            part = re.sub(';;', ';', part)
        processed_codes.append(part.strip())
        continue
    elif "trojan://" in part:
        part = f'trojan://{part.split("trojan://")[1]}'
        if "@" in part and ":" in part[9:]:
            processed_codes.append(part.strip())
        continue
    elif "tuic://" in part:
        part = f'tuic://{part.split("tuic://")[1]}'
        if ":" in part[7:] and "@" in part:
            processed_codes.append(part.strip())
        continue
    elif "hysteria://" in part:
        part = f'hysteria://{part.split("hysteria://")[1]}'
        if ":" in part[11:] and "=" in part:
            processed_codes.append(part.strip())
        continue
    elif "hysteria2://" in part:
        part = f'hysteria2://{part.split("hysteria2://")[1]}'
        if "@" in part and ":" in part[12:]:
            processed_codes.append(part.strip())
        continue
    elif "hy2://" in part:
        part = f'hy2://{part.split("hy2://")[1]}'
        if "@" in part and ":" in part[6:]:
            processed_codes.append(part.strip())
        continue
    elif "juicity://" in part:
        part = f'juicity://{part.split("juicity://")[1]}'
        processed_codes.append(part.strip())
        continue
    elif "nekoray://" in part:
        part = f'nekoray://{part.split("nekoray://")[1]}'
        processed_codes.append(part.strip())
        continue
    elif "sn://" in part:
        part0 = f'sn://{part.split("sn://")[1]}'
        part1 = f'husi://{part.split("sn://")[1]}'
        part2 = f'exclave://{part.split("sn://")[1]}'
        processed_codes.append(part0.strip())
        processed_codes.append(part1.strip())
        processed_codes.append(part2.strip())        
        continue        
    elif "husi://" in part:
        part1 = f'husi://{part.split("husi://")[1]}'
        part0 = f'sn://{part.split("husi://")[1]}'
        part2 = f'exclave://{part.split("husi://")[1]}'
        processed_codes.append(part0.strip())
        processed_codes.append(part1.strip())
        processed_codes.append(part2.strip())
        continue
    elif "exclave://" in part:
        part2 = f'exclave://{part.split("exclave://")[1]}'
        part0 = f'sn://{part.split("exclave://")[1]}'
        part1 = f'husi://{part.split("exclave://")[1]}'
        processed_codes.append(part0.strip())
        processed_codes.append(part1.strip())
        processed_codes.append(part2.strip())
        continue
    elif "ulink://" in part:
        part = f'ulink://{part.split("ulink://")[1]}'
        processed_codes.append(part.strip())
        continue        
    elif "socks4://" in part:
        part = f'socks4://{part.split("socks4://")[1]}'
        if ":" in part[9:]:
            processed_codes.append(part.strip())
        continue
    elif "socks5://" in part:
        part = f'socks5://{part.split("socks5://")[1]}'
        if ":" in part[9:]:
            processed_codes.append(part.strip())
        continue
    elif "socks://" in part:
        part = f'socks://{part.split("socks://")[1]}'
        if ":" in part[8:]:
            processed_codes.append(part.strip())
        continue
    elif "naive+" in part:
        part = f'naive+{part.split("naive+")[1]}'
        if ":" in part[13:] and "@" in part:
            processed_codes.append(part.strip())
        continue
    elif "wireguard://" in part:
        part = f'wireguard://{part.split("wireguard://")[1]}'
        processed_codes.append(part.strip())
        continue
    elif "wg://" in part:
        part = f'wg://{part.split("wg://")[1]}'
        processed_codes.append(part.strip())
        continue


print(f'\nTrying to delete corrupted configurations...') 

processed_codes = list(set(processed_codes))
processed_codes = [x for x in processed_codes if (len(x)>13) and (("…" in x and "#" in x) or ("…" not in x))]
new_processed_codes = list()
for x in processed_codes:
    if x[-2:] == '…»':
        x=x[:-2]
    if x[-1:] == '…':
        x=x[:-1]
    if x[-1:] == '»':
        x=x[:-1]
    if x[-2:-1] == '%':
        x=x[:-2]
    if x[-1:] == '%':
        x=x[:-1]
    if x[-1:] == '`':
        x=x[:-1]        
    new_processed_codes.append(x.strip())
processed_codes = list(set(new_processed_codes))

processed_codes = substring_del(processed_codes)
processed_codes = list(set(processed_codes))
processed_codes = sorted(processed_codes)

print(f'\nDelete tg channels that not contains proxy configs...')

new_tg_name_json = list(set(new_tg_name_json))
new_tg_name_json = sorted(new_tg_name_json)

print(f'\nRemaining tg channels after deletion - {len(new_tg_name_json)}')

inv_tg_name_json = list(set(inv_tg_name_json))
inv_tg_name_json = sorted(inv_tg_name_json)

print(f'\nSave new tg channels.json, blacklist channels.json and configs.txt...')

with open('tg channels.json', 'w', encoding="utf-8") as telegram_channels_file:
    json.dump(new_tg_name_json, telegram_channels_file, indent = 4)

with open('blacklist channels.json', 'w', encoding="utf-8") as inv_telegram_channels_file:
    json.dump(inv_tg_name_json, inv_telegram_channels_file, indent = 4)

with open("configs.txt", "w", encoding="utf-8") as file:
    for code in processed_codes:
        file.write(code.encode("utf-8").decode("utf-8") + "\n")

# ایجاد فایل HTML برای نمایش کانفیگ‌ها
processed_configs = []

# برای هر کانفیگ و زمان ارسال، اطلاعات مربوطه ذخیره می‌شود
for idx, (config, time_sent) in enumerate(codes, start=1):  # حالا codes شامل کانفیگ و زمان است
    config_type = ""
    if config.startswith("vless://"):
        config_type = "vless"
    elif config.startswith("vmess://"):
        config_type = "vmess"
    elif config.startswith("hysteria2://") or config.startswith("hy2://"):
        config_type = "hysteria2"
    elif config.startswith("ss://"):
        config_type = "ss"
    elif config.startswith("trojan://"):
        config_type = "trojan"
    elif config.startswith("wireguard://"):
        config_type = "wireguard"
    else:
        config_type = "unknown"

    country, country_code = get_country_from_config(config)
    # ذخیره کانفیگ‌ها به همراه زمان ارسال
    processed_configs.append((idx, config, config_type, country, country_code, time_sent))

html_content = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Configs List</title>
    <style>
        /* تنظیم فونت Iranyekan */
        @font-face {
            font-family: 'Iranyekan';
            src: url('assets/Yekan.woff2') format('woff2'),
                 url('assets/Yekan.woff') format('woff');
            font-weight: normal;
            font-style: normal;
        }

        body {
            font-family: 'Tahoma', sans-serif;
            background-color: #00203F; /* تغییر رنگ پس‌زمینه */
            color: #00203F; /* تغییر رنگ متن */
            margin: 20px;
        }

        h1 {
            font-family: 'Iranyekan', sans-serif; /* تغییر فونت h1 */
            text-align: center; /* وسط‌چین کردن */
            color: #ADEFD1;
            margin-bottom: 20px;
        }

        .filter-container {
            text-align: center;
            margin-bottom: 20px;
            font-family: 'Iranyekan', sans-serif; /* تغییر فونت */
            color: #ADEFD1; /* تغییر رنگ */
        }

        .filter-container label {
            margin-left: 10px; /* فاصله بین متن و فیلتر */
        }

        .filter-container select {
            padding: 10px;
            font-size: 16px;
            border: 1px solid #ccc;
            border-radius: 4px;
        }

        .container {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            justify-content: center;
        }

        .config-card {
            background-color: #ADEFD1; /* تغییر رنگ پس‌زمینه */
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            width: 220px;
            text-align: center;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            display: flex;
            flex-direction: column;
            justify-content: space-between; /* Aligns the content and buttons properly */
        }

        .config-card h3 {
            font-size: 18px;
            margin-bottom: 10px;
        }

        .config-card img {
            width: 25px;
            height: 20px;
            margin-right: 5px;
            vertical-align: middle;
        }

        .config-card .type {
            font-weight: bold;
            margin-bottom: 10px;
        }

        .config-card .config {
            font-size: 14px;
            margin-bottom: 10px;
            word-break: break-word;
        }

        .k2-copy-button svg {
            margin-right: 10px;
            vertical-align: middle; /* Align svg properly with the text */
        }

        .k2-copy-button {
            font-family: 'Iranyekan', sans-serif; /* تغییر فونت دکمه‌ها به Iranyekan */
            height: 45px;
            width: 155px;
            color: #fff;
            background: #265df2;
            outline: none;
            border: none;
            border-radius: 8px;
            font-size: 17px;
            font-weight: 400;
            margin: 8px 0;
            cursor: pointer;
            transition: all 0.4s ease;
            align-self: center; /* Center the button in the card */
        }

        .k2-copy-button:hover {
            background: #2ECC71;
        }

        @media (max-width: 480px) {
            .k2-copy-button {
                width: 100%;
            }
        }
    </style>
</head>
<body>
    <h1> پروژه جمع‌آوری کانفیگ از تلگرام</h1>
    <div class="filter-container">
        <label for="filter-country">مرتب‌سازی براساس کشور:</label>
        <select id="filter-country" onchange="applyFilters()">
            <option value="all">All</option>
"""

# ساختن لیست کشورها برای فیلتر
countries = sorted(set([country for _, _, _, country, _, _ in processed_configs]))

for country in countries:
    html_content += f'<option value="{country}">{country}</option>\n'

html_content += """
        </select>
        <label for="filter-type">مرتب‌سازی براساس نوع:</label>
        <select id="filter-type" onchange="applyFilters()">
            <option value="all">All</option>
            <option value="vless">VLESS</option>
            <option value="vmess">VMESS</option>
            <option value="hysteria2">Hysteria2</option>
            <option value="ss">Shadowsocks</option>
            <option value="trojan">Trojan</option>
            <option value="wireguard">WireGuard</option>
        </select>
        <label for="filter-time">مرتب‌سازی براساس زمان ارسال:</label>
        <select id="filter-time" onchange="applyFilters()">
            <option value="asc">Ascending</option>
            <option value="desc">Descending</option>
        </select>
    </div>
    <div class="container">
"""

# اضافه کردن کارت‌ها برای هر کانفیگ
for idx, config, config_type, country, country_code, time_sent in processed_configs:
    # اگر کشور نامشخص باشد، پیش‌فرض ایران است
    if country_code == "unknown":
        country = "Unknown"
        country_code = "aq"
    flag_url = f"https://flagcdn.com/w40/{country_code}.png"
    html_content += f"""
        <div class="config-card" data-type="{config_type}" data-country="{country}" data-time="{time_sent}">
            <h3>
                <img src="{flag_url}" alt="{country} Flag">
                {country}
            </h3>
            <div class="type">{config_type.upper()}</div>
            <div class="config" title="{config}">{config}</div>
            <div class="time">زمان ارسال: {time_sent}</div> <!-- نمایش زمان ارسال -->
            <button class="k2-copy-button" id="k2button-{idx}" onclick="copyToClipboard('{config}', {idx})">
                کپی کردن
            </button>
        </div>
    """
html_content += """
    </div>
    <script>
        // تابع کپی کردن متن
        function copyToClipboard(text, idx) {
            navigator.clipboard.writeText(text).then(() => {
                // تغییر رنگ و متن دکمه
                const button = document.getElementById("k2button-" + idx);
                button.style.backgroundColor = "#2ECC71"; // سبز
                button.innerText = "با موفقیت کپی شد"; // تغییر متن

                // بعد از 3 ثانیه به حالت اول برگرداندن
                setTimeout(() => {
                    button.style.backgroundColor = "#265df2"; // رنگ آبی
                    button.innerText = "کپی کردن"; // تغییر متن
                }, 3000);
            }).catch(err => {
                console.log('Error:', err);
            });
        }

        // تابع کلی برای اعمال فیلترها
        function applyFilters() {
            const filterCountry = document.getElementById('filter-country').value.toLowerCase();
            const filterType = document.getElementById('filter-type').value.toLowerCase();
            const filterTime = document.getElementById('filter-time').value.toLowerCase();
            const cards = document.querySelectorAll('.config-card');

            // گرفتن مقادیر از data-attributes
            cards.forEach(card => {
                const cardCountry = card.getAttribute('data-country').toLowerCase();
                const cardType = card.getAttribute('data-type').toLowerCase();
                const cardTime = card.getAttribute('data-time');  // زمان ارسال در قالب YYYY/MM/DD HH:MM

                // مقایسه با فیلتر کشور و نوع
                const matchesCountry = (filterCountry === 'all' || cardCountry === filterCountry);
                const matchesType = (filterType === 'all' || cardType === filterType);

                // مقایسه زمان ارسال
                const cardDate = new Date(cardTime);  // تبدیل زمان به تاریخ

                let matchesTime = false;
                if (filterTime === 'asc') {
                    matchesTime = cardDate <= new Date();  // برای ascending تاریخ‌های قدیمی‌تر نمایش داده شوند
                } else if (filterTime === 'desc') {
                    matchesTime = cardDate >= new Date();  // برای descending تاریخ‌های جدیدتر نمایش داده شوند
                }

                // نمایش یا پنهان کردن کارت‌ها بر اساس فیلترها
                if (matchesCountry && matchesType && matchesTime) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        }
    </script>
</body>
</html>
"""


# ذخیره فایل HTML
with open("index.html", "w", encoding="utf-8") as html_file:
    html_file.write(html_content)
print(f'\nHTML file (index.html) has been created.')
print(f'\nTime spent - {str(datetime.now() - start_time).split(".")[0]}')
#print(f'\nTime spent - {timedelta(seconds=int((datetime.now() - start_time).total_seconds()))}')

print(f'\n...FINISH...')
