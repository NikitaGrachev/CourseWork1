import requests
from api_vk import vk_token
import os
import json
from tqdm import tqdm

class VkDownloader:
    def __init__(self, token):
        self.token = token

    def get_photos(self, user_id: str, offset:int=0, count:int=50):
        url = 'https://api.vk.com/method/photos.get'
        params = {'owner_id': user_id,
                  'album_id': 'profile',
                  'access_token': self.token,
                  'v': '5.131',
                  'extended': '1',
                  'photo_sizes': '1',
                  'count': count,
                  'offset': offset
                  }
        res = requests.get(url=url, params=params)
        return res.json()

    def get_all_photos(self, user_id: str, count: int):
        data = self.get_photos(user_id, count=count)
        print(data)
        all_photo_count = data['response']['count']  # Количество всех фотографий профиля
        i = 0
        count = 30
        photos = []  # Список всех загруженных фото
        max_size_photo = {}  # Словарь с парой название фото - URL фото максимального разрешения

        # Создаём папку на компьютере для скачивания фотографий
        if not os.path.exists('images_vk'):
            os.mkdir('images_vk')

        # Проходимся по всем фотографиям
            for photo in data['response']['items']:
                max_size = 0
                photos_info = {}
                # Выбираем фото максимального разрешения и добавляем в словарь max_size_photo
                for size in photo['sizes']:
                    if size['height'] >= max_size:
                        max_size = size['height']
                if photo['likes']['count'] not in max_size_photo.keys():
                    max_size_photo[photo['likes']['count']] = size['url']
                    photos_info['file_name'] = f"{photo['likes']['count']}.jpg"
                else:
                    max_size_photo[f"{photo['likes']['count']} + {photo['date']}"] = size['url']
                    photos_info['file_name'] = f"{photo['likes']['count']}+{photo['date']}.jpg"

                # Формируем список всех фотографий для дальнейшей упаковки в .json

                photos_info['size'] = size['type']
                photos.append(photos_info)

            # Скачиваем фотографии
            for photo_name, photo_url in max_size_photo.items():
                with open('images_vk/%s' % f'{photo_name}.jpg', 'wb') as file:
                    img = requests.get(photo_url)
                    file.write(img.content)

            print(f'Загружено {len(max_size_photo)} фото')
            i += count

    # Записываем данные о всех скачанных фоторафиях в файл .json
        with open("photos.json", "w") as file:
            json.dump(photos, file, indent=4)

class YaUploader:
    def __init__(self, token: str):
        self.token = token
        self.headers = {'Content-Type': 'application/json', 'Authorization': f'OAuth {self.token}'}

    def folder_creation(self, folder_name: str):
        url = f'https://cloud-api.yandex.net/v1/disk/resources/'
        params = {'path': f'{folder_name}',
                  'overwrite': 'false'}
        git = requests.put(url=url, headers=self.headers, params=params)

    def upload(self, file_path: str, folder_name: str, file_name: str):
        url = f'https://cloud-api.yandex.net/v1/disk/resources/upload'
        params = {'path': f'{folder_name}/{file_name}',
                  'overwrite': 'true'}

        # Получение ссылки на загрузку

        response = requests.get(url=url, headers=self.headers, params=params)
        href = response.json().get('href')

        # Загрузка файла
        uploader = requests.put(href, data=open(file_path, 'rb'))

def main():
    user_id = str(input('Введите id пользователя VK: '))
    count = int(input('Введите количество фото для загрузки: '))
    downloader = VkDownloader(vk_token)
    downloader.get_all_photos(user_id, count)

    ya_token = str(input('Введите ваш токен ЯндексДиск: '))
    uploader = YaUploader(ya_token)
    folder_name = str(input('Введите имя папки на Яндекс диске, в которую необходимо сохранить фото: '))
    uploader.folder_creation(folder_name)

    photos_list = os.listdir('images_vk')
    count = 0
    for photo in tqdm(photos_list):
        file_name = photo
        files_path = os.getcwd() + '\images_vk\\' + photo
        result = uploader.upload(files_path, folder_name, file_name)
        count += 1
        print(f'Фотографий загружено на Яндекс диск: {count}')


if __name__ == '__main__':
    main()