import os
import requests
from dotenv import load_dotenv
from random import randint


def download_comic(url, save_path):
    response = requests.get(url)
    response.raise_for_status()

    comic = response.json()
    image_url = comic['img']

    image_response = requests.get(image_url)
    image_response.raise_for_status()

    with open(save_path, 'wb') as file:
        file.write(image_response.content)
    return comic['alt']


def handle_vk_response(response):
    vk_outcome = response.json()
    if 'error' in vk_outcome:
        error_code = vk_outcome['error']['error_code']
        error_msg = vk_outcome['error']['error_msg']
        raise Exception(f"Ошибка VK API (код {error_code}): {error_msg}")
    else:
        return vk_outcome


def get_wall_upload_server(token, group_id):
    url = f'https://api.vk.com/method/photos.getWallUploadServer'
    params = {
        'access_token': token,
        'v': '5.131',
        'group_id': group_id
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    upl_server = handle_vk_response(response)
    return upl_server['response']


def upload_photo_to_server(url, path):
    with open(path, 'rb') as file:
        files = {'photo': file}
        response = requests.post(url, files=files)
    response.raise_for_status()
    photo = response.json()
    return photo


def save_wall_photo(token, group_id, photo_, server_, hash_):
    url = f'https://api.vk.com/method/photos.saveWallPhoto'

    params = {
        'access_token': token,
        'v': '5.131',
    }

    photo = {
        'group_id': group_id,
        'photo': photo_,
        'server': server_,
        'hash': hash_,
    }

    response = requests.post(url, params=params, data=photo)
    response.raise_for_status()
    vk_response = handle_vk_response(response)
    return vk_response['response']


def create_post(token, group_id, attachments_, message):
    url = f'https://api.vk.com/method/wall.post'

    params = {
        'access_token': token,
        'v': '5.131'
    }

    post_payload = {
        'owner_id': f'-{group_id}',
        'attachments': attachments_,
        'message': message
    }

    response = requests.post(url, params=params, data=post_payload)
    response.raise_for_status()
    post = handle_vk_response(response)
    return post['response']


class PhotoNotFoundError(Exception):
    pass


if __name__ == '__main__':
    load_dotenv()
    vk_access_token = os.environ['VK_ACCESS_TOKEN']
    vk_group_id = os.environ['VK_GROUP_ID']
    upload_server = get_wall_upload_server(vk_access_token, vk_group_id)

    upload_url = upload_server['upload_url']

    max_comics = 2808
    comic_num = randint(1, max_comics)
    comic_url = f'https://xkcd.com/{comic_num}/info.0.json'
    comic_alt = download_comic(comic_url, f'comic_{comic_num}.png')
    photo_path = f'comic_{comic_num}.png'

    try:
        upload_response = upload_photo_to_server(upload_url, photo_path)

        if 'photo' in upload_response:
            photo = upload_response['photo']
        else:
            raise PhotoNotFoundError('Фото не найдено')
        server = upload_response['server']
        photo_hash = upload_response['hash']

        save_response = save_wall_photo(vk_access_token, vk_group_id, photo, server, photo_hash)

        attachments = f"photo{save_response[0]['owner_id']}_{save_response[0]['id']}"
        post_response = create_post(vk_access_token, vk_group_id, attachments, comic_alt)
    except PhotoNotFoundError as e:
        print(f"Произошла ошибка: {e}")
    finally:
        os.remove(photo_path)
