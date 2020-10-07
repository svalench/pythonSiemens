# pythonSiemens
# Модуль опроса контролееров ф Siemens  с веб интерфесом
## Описание
#### Предназначен для сбора данных с плк сименс. За основу вязт модуль Snap7-python который запускает каждый новый опрос в новом потоке, а конфигурация происходит через Flask.
## Установка
#### Склонте проект.
`git clone https://github.com/svalench/pythonSiemens.git`
### Установите пакет Snap7
### Ссылка  [тут](https://python-snap7.readthedocs.io/en/latest/installation.html)
#### Устновите зависимости
`pip3 -r requiremens.txt`


## Подключение к БД
Для того чтобы настроить подключение к БД необходимо открыть файл `settings.py` и изменить на свою следующие поля в словаре DB:
1. driver (проверено только на Postgre) postgre или sqlite3
2. dbName - название базы
3. host - хост базы (только для Postgre)
4. port - порт (только для Postgre)
5. user - пользователь в базе  (только для Postgre)
6. pass - пароль указанного выше пользователя (только для Postgre)

## Использование
#### Запустите файл main
`python3 main.py`
### Запустится локальный сервер Flask
#### [localhost:5000](http://localhost:5000)
### Данный для входа лежат в файле settings.py `USERNAME` и `PASSWORD`
##### Далее Вы увидите стартувую странцу на которой можно настроить новые подключения на вкладке `config file`. 
#### Нажав на кнопку `add connection` Вы сможете создать новое подключение и перезапустите все уже запущенные потоки. (Далее любое действие с конфигурационным файлом перезапускает все потоки).
####  Для этого нужно будет заполнить форму со следующими данными:
1. название подключения
2. тип плк (пока поддерживается только сименс)
3. IP адрес плк
4. Линейку (Rack) (можно псмотреть в Hardware проекта)
5. Слот плк (смотри так же в hardware)
6. Время между запросами к ПЛК
7. Время ожидание между неудавшимися подключениями

#### Нажав на кнопку `Remove`  Вы удалите данное подключение и все точки к нему привязанные.
#### Нажав на кнопку `add point to plc` вы перйдете на страницу с формой в которые нужно внести такие данные как :
1. название таблицы
2. тип данных
3. адрес DB в плк
4. сдвиг по DB

#### После их заполнение произойдет перезапуск всех подключений. (Это нужно чтобы подтянуть изменения)
