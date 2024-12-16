# Voice Service
**Voice Service** -- это программный модуль мультимодальной диалогой системы, входящий в состав дистрибутива dream_voice, используемый для генерации текстовых подписей (аннотаций) к аудиофайлам поддерживаемых форматов (mp3 и wav) и формирования ответов на вопросы, связанные в полученным изображение.

## Запуск 
Для запуска программного моделя fromage_service необходимо в корневой директории выполнить следующие команды:
```sh
docker-compose -f docker-compose.yml -f assistant_dists/dream_voice/docker-compose.override.yml -f assistant_dists/dream_voice/dev.yml -f assistant_dists/dream_voice/proxy.yml up --build voice-service
```

## Тестирование

Для запуска тестирования программного моделя voice_service необходимо в корневой директории выполнить следующие команды:

```sh
bash tests/test_launch_audio.sh
bash tests/test_voice_service.sh
```
