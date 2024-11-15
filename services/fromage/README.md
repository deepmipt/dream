# Fromage Service
**Fromage Service** -- это программный модуль мультимодальной диалогой системы, входящий в состав дистрибутива dream_multimodal, используемый для генерации подписей (аннотаций) к изображениям в поддерживаемых форматах (jpg и png) и формирования ответов на вопросы, связанные в полученным изображение.

В состав программного модуля также входит программный модуль **Video_service**, используемый для генерации подписей (аннотаций) к видеофайлам в форматах mp4.

<!-- Список и функкциональность основных файлов -->

## Запуск 
Для запуска программного моделя fromage_service необходимо в корневой директории выполнить следующие команды:
```sh
docker-compose -f docker-compose.yml -f assistant_dists/dream_multimodal/docker-compose.override.yml -f assistant_dists/dream_multimodal/dev.yml -f assistant_dists/dream_multimodal/proxy.yml up --build fromage
```

## Тестирование

Для запуска тестирования программного моделя fromage_service необходимо в корневой директории выполнить следующие команды:

```sh
bash tests/test_launch_vision.sh
bash tests/test_fromage.sh
```
