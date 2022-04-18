import json
import time
import requests


def get_data(username: str) -> list:
    URL_GITHUB_REPO = f'https://api.github.com/users/{username}/repos'
    repo = []
    while True:
        time.sleep(1)
        response = requests.get(URL_GITHUB_REPO)
        if response.status_code == 200:
            break
    print('Получен результат.')
    response = response.json()
    for item in response:
        repo.append(item['name'])
    return repo


def repo_write_file(f_name, data):
    with open(f_name, 'w') as f:
        json.dump(data, f, indent=2)


if __name__ == '__main__':

    username = input('Введите имя пользователя: ')
    repositories = get_data(username)
    repo_write_file(f'repo_{username}.json', repositories)

    print(f'Список репозиториев пользователя {username}.')
    for i, val in enumerate(repositories, start=1):
        print(f'№{i}. {val.title()}')
