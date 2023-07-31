import os
import requests
from dotenv import load_dotenv
from random import randint


def save_comic(url, save_path):
    response = requests.get(url)
    response.raise_for_status()

    comic = response.json()
    image_url = comic['img']

    image_response = requests.get(image_url, stream=True)
    image_response.raise_for_status()

    with open(save_path, 'wb') as file:
        for chunk in image_response.iter_content():
            file.write(chunk)
    return comic['alt']


def get_user_groups(token):
    url = f'https://api.vk.com/method/groups.get?access_token={token}&v=5.131'

    response = requests.get(url)
    data = response.json()

    if 'response' in data and 'items' in data['response']:
        groups = data['response']['items']
        return groups
    else:
        print(f"Failed to retrieve groups. Error message: {data.get('error', 'Unknown error')}")
        return []


def get_wall_upload_server(token, group_id):
    url = f'https://api.vk.com/method/photos.getWallUploadServer?access_token={token}&v=5.131&group_id={group_id}'

    response = requests.get(url)
    data = response.json()
    return data['response']


def upload_photo_to_server(url, path):
    with open(path, 'rb') as file:
        files = {'photo': file}
        response = requests.post(url, files=files)
        data = response.json()

    if 'photo' in data:
        return data
    else:
        print(f"Failed to upload photo. Error message: {data.get('error', 'Unknown error')}")
        return None


def save_wall_photo(token, group_id, photo_, server_, hash_):
    url = f'https://api.vk.com/method/photos.saveWallPhoto?access_token={token}&v=5.131'

    params = {
        'group_id': group_id,
        'photo': photo_,
        'server': server_,
        'hash': hash_,
    }

    response = requests.post(url, data=params)
    response.raise_for_status()
    data = response.json()
    return data['response']


def create_post(token, group_id, attachments_, message):
    url = f'https://api.vk.com/method/wall.post?access_token={token}&v=5.131'

    params = {
        'owner_id': f'-{group_id}',
        'attachments': attachments_,
        'message': message
    }

    response = requests.post(url, data=params)
    response.raise_for_status()
    data = response.json()
    return data['response']


if __name__ == '__main__':
    load_dotenv()
    vk_access_token = os.environ['VK_ACCESS_TOKEN']
    group_id = get_user_groups(vk_access_token)[0]
    upload_server = get_wall_upload_server(vk_access_token, group_id)

    upload_url = upload_server['upload_url']
    album_id = upload_server['album_id']
    user_id = upload_server['user_id']

    comic_num = randint(1, 2808)
    comic_url = f'https://xkcd.com/{comic_num}/info.0.json'
    comic_alt = save_comic(comic_url, f'comics/comic_{comic_num}.png')
    photo_path = f'comics/comic_{comic_num}.png'

    upload_response = upload_photo_to_server(upload_url, photo_path)

    photo = upload_response['photo']
    server = upload_response['server']
    photo_hash = upload_response['hash']

    save_response = save_wall_photo(vk_access_token, group_id, photo, server, photo_hash)

    attachments = f"photo{save_response[0]['owner_id']}_{save_response[0]['id']}"
    post_response = create_post(vk_access_token, group_id, attachments, comic_alt)

    os.remove(photo_path)
