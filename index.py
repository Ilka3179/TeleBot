import requests
from deepface import DeepFace
import os

url_one = 'https://fotografias.antena3.com/clipping/cmsimages02/2020/11/03/5CAA8016-0DC6-4CF5-AB3C-6CC6F4176122/58.jpg'
url_two = 'https://i.pinimg.com/originals/11/5f/5f/115f5f75089500e4dea2096744fc2312.jpg'

responce_one = requests.get(url_one)
responce_two = requests.get(url_two)

current_path = os.path.dirname(os.path.abspath(__file__))
photos_path = os.path.join(current_path, 'photos')

photos1 = os.path.join(photos_path, 'phote_one.jpg')
photos2 = os.path.join(photos_path, 'phote_two.jpg')

with open(photos1, 'wb') as file:
    file.write(responce_one.content)

with open(photos2, 'wb') as file:
    file.write(responce_two.content)


result = DeepFace.verify(photos1, photos2)

print(result)