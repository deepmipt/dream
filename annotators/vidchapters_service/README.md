# Video Service
**Video_service** -- это программный модуль мультимодальной диалогой системы, входящий в состав дистрибутива dream_multimodal, используемый для генерации подписей (аннотаций) к видеофайлам в форматах mp4.

<!-- Список и функкциональность основных файлов -->

## Запуск 
Для запуска программного моделя fromage_service необходимо в корневой директории выполнить следующие команды:
```sh
docker-compose -f docker-compose.yml -f assistant_dists/dream_multimodal/docker-compose.override.yml -f assistant_dists/dream_multimodal/dev.yml -f assistant_dists/dream_multimodal/proxy.yml up --build vidchapters-service
```

## Тестирование

Для запуска тестирования программного моделя fromage_service необходимо в корневой директории выполнить следующие команды:

```sh
bash tests/test_video.sh
```
