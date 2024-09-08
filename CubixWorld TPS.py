import requests
import time
import threading
from PIL import Image, ImageDraw, ImageFont
from pystray import Icon, Menu, MenuItem
from functools import partial
import sys

# URL для получения мониторинга серверов
API_URL = "https://cubixworld.net/api/monitoring"

# Функция для получения данных о серверах
def fetch_server_data():
    response = requests.get(API_URL)
    if response.status_code == 200:
        return response.json()['servers']
    else:
        return None

# Функция для получения TPS выбранного сервера
def get_tps(main_server, sub_server_num):
    data = fetch_server_data()
    if data and main_server in data and sub_server_num in data[main_server]['servers']:
        return round(data[main_server]['servers'][sub_server_num]['tps'])  # Округляем до целого числа
    return "N/A"

# Функция для обновления иконки
def update_icon(icon, main_server, sub_server_num):
    while icon.visible:
        tps = get_tps(main_server, sub_server_num)
        image = create_image(tps)
        icon.icon = image
        time.sleep(1)  # обновляем каждые 10 секунд

# Функция для создания изображения с TPS
def create_image(tps):
    # Создание прозрачной картинки с TPS
    width = 64
    height = 64
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))  # Прозрачный фон
    draw = ImageDraw.Draw(image)

    # Определяем цвет в зависимости от TPS
    if isinstance(tps, int):
        if tps > 15:
            color = "green"
        elif 10 <= tps <= 15:
            color = "orange"
        else:
            color = "red"
    else:
        color = "white"
        tps = "N/A"

    # Прорисовка текста TPS на картинке
    font = ImageFont.truetype("arial", 56)  # Увеличенный и толстый шрифт
    text = str(tps)

    # Получаем размеры текста
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Центрируем текст на картинке с вертикальной поправкой
    position = ((width - text_width) // 2, (height - text_height) // 2 - 5)  # Добавляем -5 для вертикального центрирования
    draw.text(position, text, fill=color, font=font)

    return image

# Функция для изменения сервера
def change_server(icon, main_server, sub_server_num, *args):
    icon.menu = create_menu(icon, main_server, sub_server_num)
    icon.update_menu()
    threading.Thread(target=update_icon, args=(icon, main_server, sub_server_num), daemon=True).start()

# Функция для создания меню
def create_menu(icon, current_main_server, current_sub_server_num):
    data = fetch_server_data()
    items = []
    
    if data:
        for main_server_name, main_server_data in data.items():
            for sub_server_num, sub_server_data in main_server_data['servers'].items():
                menu_label = f"{main_server_name} {sub_server_num} (TPS: {round(sub_server_data['tps'])})"
                # Используем partial для корректной передачи аргументов
                items.append(
                    MenuItem(
                        menu_label,
                        partial(change_server, icon, main_server_name, sub_server_num),
                        checked=lambda item, ms=main_server_name, ss=sub_server_num: ms == current_main_server and ss == current_sub_server_num
                    )
                )
    
    # Добавляем кнопку выхода
    items.append(MenuItem("Выйти", exit_app))
    
    return Menu(*items)

# Функция для выхода из программы
def exit_app(icon, item):
    icon.stop()  # Останавливаем иконку

# Главная функция
def main():
    data = fetch_server_data()
    
    if not data:
        print("Не удалось получить данные с сервера.")
        return

    # Выбираем первый сервер по умолчанию
    default_main_server = list(data.keys())[0]
    default_sub_server_num = list(data[default_main_server]['servers'].keys())[0]
    
    # Создаем иконку
    icon = Icon("Cubix TPS", create_image("N/A"))
    
    # Создаем меню с выбором серверов
    icon.menu = create_menu(icon, default_main_server, default_sub_server_num)
    
    # Запускаем обновление иконки в отдельном потоке
    threading.Thread(target=update_icon, args=(icon, default_main_server, default_sub_server_num), daemon=True).start()
    
    # Показываем иконку в трее
    icon.run()

if __name__ == "__main__":
    main()
