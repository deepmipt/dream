# Интеграция фреймворка описания диалога с графами знаний

Интеграция фреймворка описания диалога с графами знаний состоит из:

- модуля `property-extraction`: для извлечения сущностей из высказываний в виде триплетов
- сценарного навыка `travel-italy-skill`: примера интеграции фреймворка с графами знаний, где переход из одного узла в другой осуществляется на основании обнаруженной в высказывании сущности

## Запуск интеграции фреймворка описания диалога с графами знаний

Для запуска модуля `property-extraction` необходимо выполнить следующую команду из корневой директории:

```
docker-compose -f docker-compose.yml -f assistant_dists/dream_kg/docker-compose.override.yml -f assistant_dists/dream_kg/dev.yml up --build property-extraction
```

Для запуска сценарного навыка `travel-italy-skill` в дистрибутиве `dream_kg` фреймворка для разработки многонавыковых ИИ-ассистентов необходимо выполнить следующую команду из корневой директории:

```
docker-compose -f docker-compose.yml -f assistant_dists/dream_kg/docker-compose.override.yml -f assistant_dists/dream_kg/dev.yml up --build
```

## Тестирование интеграции фреймворка описания диалога с графами знаний

Для проведения тестирования необходимо установить пакеты `requests` и `nltk` следующими командами:

```
pip install requests nltk
python -c "import nltk; nltk.download('punkt_tab')"
```

Для тестирования модуля `property-extraction` необходимо выполнить следующую команду из корневой директории:
```
bash tests/test_prop_ex.sh
```

Для тестирования сценарного навыка `travel-italy-skill` необходимо выполнить следующую команду из корневой директории:
```
bash tests/test_travel_italy_skill.sh
```