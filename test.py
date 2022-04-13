import requests
import time


def create_user(username, id):
    data = {
        "username": username,
        "password": "kissa",
        "steam64": id
    }
    x = requests.post("http://127.0.0.1:8000/users/", json=data)
    return x


def create_lobby(token):
    headers = {"Authorization": "Bearer" + " " + token}
    title = "toimiiko tämä"
    x = requests.post(f"http://16.170.223.242:8000/scrims/scrim/{title}",
                      headers=headers)
    print(x.text)


def join_lobby(token):
    headers = {"Authorization": "Bearer" + " " + token}
    params = {
        "lobby": "reenit"
    }
    x = requests.put("http://16.170.223.242:8000/scrims/join",
                     headers=headers, params=params)
    print(x.text)


def login():
    data = {
        "username": "Tango",
        "password": "kissa"
    }
    x = requests.post("http://16.170.223.242:8000/login", data=data)
    return x


usernames = ["Mike", "Bravo", "Tango", "Fox", "Charlie", "Delta", "Zulu"]
for i, user in enumerate(usernames):
    # user = create_user(user, i)
    # print(user.text)
    print(i)
    time.sleep(5)
    if i >= 4:
        print("i == 4")
        break
# auth = login()
# print(auth.json())
# join_lobby(auth.json()["token"])
# create_lobby(auth.json()["token"])
