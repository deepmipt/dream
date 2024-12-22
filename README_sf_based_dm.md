# Программный компонент с алгоритмом эффективного управления взаимодействием диалоговой системы открытого домена и пользователей и выделения дискурсных структур в ходе беседы с ними

Программный компонент с алгоритмом управления взаимодействием диалоговой системы открытого домена и пользователями, а также выделением дискурсных структур в ходе беседы служит для выбора наиболее подходящего ответа диалоговой системы на основе анализа абстрактных намерений  – речевых функций. Данный компонент выполняет следующие функции: 
- анализ входящих реплик, гипотез для ответа и аннотаций к ним, включающих анализ абстрактных намерений;
- фильтрация токсичных ответов, оценивание реплик-кандидатов для ответа;
- выбор финального варианта на основе оценки. 
Анализ дискурсных структур основан на теории речевых функций, согласно которой каждой реплике присваивается один из 16 тегов, обозначающих абстрактные намерения. 

## Начало работы
Перед началом работы необходимо убедиться в том, что:
- в текущей директории есть файл .env_secret, предназначенный для хранения персональной информации. При отсутствии данного файла необходимо создать пустой файл .env_secret;
- в файле .env_secret указаны OPENAI_API_KEY, OPENAI_API_BASE;
- в текущем окружении установлена библиотека requests.

## Запуск
Для запуска данного программмного компонента необходимо запустить следующую команду в корневой директории:
```
docker-compose -f docker-compose.yml -f assistant_dists/dream_ranking_and_sf_based_dm/docker-compose.override.yml -f assistant_di
sts/dream_ranking_and_sf_based_dm/proxy.yml -f assistant_dists/dream_ranking_and_sf_based_dm/dev.yml up --build --force-recreate
```

## Тестирование
Для тестирования на время работы компонента и формат входных и выходных данных необходимо запустить компонент, перейти в директорию компонента 'response_selectors/ranking_and_sf_based_response_selector' и из нее запустить следующую команду:
```
python test.py
```
Эффективность работы данного программного компонента оценивается с помощью фреймворка LLM-Eval на основе большой языковой модели gpt3.5-turbo. В рамках подхода LLM-Eval диалоги оцениваются по нескольким параметрам по шкале от 0 до 5. С помощью модели сравниваются диалоги на одинаковые темы, полученные в ходе общения пользователя с диалоговой системой с данным программным компонентом и без него. Перед началом тестирования убедитесь, что в окружении заданы переменные OPENAI_API_KEY и OPENAI_API_BASE.

Для тестирования на время работы компонента и формат входных и выходных данных необходимо запустить компонент, перейти в директорию компонента 'response_selectors/ranking_and_sf_based_response_selector' и из нее запустить следующую команду:
```
python test_data_quality.py
```

Для тестирования на время восстановления после отказа необходимо остановить Docker-контейнер с компонентом и из директории компонента 'response_selectors/ranking_and_sf_based_response_selector' запустить следующую команду:
```
bash test_launch_time.sh