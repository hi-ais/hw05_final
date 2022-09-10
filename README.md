# Социальная сеть Yatube

## Описание
Социальная сеть. Учебный проект.

Сообщество для публикаций. Блог с возможностью публикации постов, подпиской на авторов, а также комментированием постов.

## Стек
![python version](https://img.shields.io/badge/Python-3.7-green)
![django version](https://img.shields.io/badge/Django-2.2-green)
![pillow version](https://img.shields.io/badge/Pillow-9.2-green)
![pytest version](https://img.shields.io/badge/pytest-5.3-green)
![requests version](https://img.shields.io/badge/requests-2.22-green)
![sorl-thumbnail version](https://img.shields.io/badge/thumbnail-12.9-green)

## Запуск проекта 
1. Клонируйте репозиторий: 
```git@github.com:hi-ais/hw05_final.git```
2. Установите вируальное окружение:
```python -m venv venv```
```source venv/Scripts/activate```
3. Установите зависимости из файла **requirements.txt**
```pip install -r requirements.txt```
4. В папке с файлом manage.py выполните миграции:
```python manage.py migrate```
5. В папке с файлом manage.py запустите сервер, выполнив команду:
```python manage.py runserver```

