# Программный компонент для создания графового представления персоны пользователя по контексту диалога для английского языка

Программный компонент для создания графового представления персоны пользователя состоит из:

- модуля `property-extraction`: для извлечения сущностей из высказываний в виде триплетов
- модуля `custom-entity-linking`: для связывания ранее упоминавшихся сущностей с их идентификаторами в базе знаний
- модуля `user-knowledge-memorizer`: для создания графа знаний пользователя и добавления в него новых сущностей
- генеративного навыка `knowledge-prompted-skill`: примера демонстрации работы программного компонента для создания графового представления персоны пользователя на базе платформы DeepPavlov Dream

## Запуск программного компонента для создания графового представления персоны пользователя

Запуск модуля `property-extraction` описан в файле [README_integration.md](/README_integration.md)

Для запуска модуля `custom-entity-linking` из корневой директории необходимо выполнить следующую команду, включающую подключение к графами знаний `terminusdb-server`:

```
docker-compose -f docker-compose.yml -f assistant_dists/dream_kg_prompted/docker-compose.override.yml -f assistant_dists/dream_kg_prompted/dev.yml up --build terminusdb-server custom-entity-linking
```

Для запуска модуля `user-knowledge-memorizer` из корневой директории необходимо выполнить следующую команду, включающую подключение к графами знаний `terminusdb-server`:

```
docker-compose -f docker-compose.yml -f assistant_dists/dream_kg_prompted/docker-compose.override.yml -f assistant_dists/dream_kg_prompted/dev.yml up --build terminusdb-server user-knowledge-memorizer-prompted
```


## Тестирование программного компонента для создания графового представления персоны пользователя

Тестирование модуля `property-extraction` описаны в файле [README_integration.md](/README_integration.md)

Для проведения тестирования необходимо установить пакет `requests` следующей командой:

```
pip install requests
```

Также данный компонент требует наличия в корневой директории файлов: 
* `.env`, содержащего proxy url в переменной `OPENAI_BASE_URL` на случай, если сервис большой языковой модели от OpenAI недоступен;
* `.env_secret`, содержащего ключ для сервиса большой языковой модели в переменной `OPENAI_API_KEY`. 

Для тестирования модуля `custom-entity-linking` необходимо выполнить следующую команду из корневой директории:

```
bash tests/test_custom_el.sh
```

Для тестирования модуля `user-knowledge-memorizer` необходимо выполнить следующую команду из корневой директории:

```
bash tests/test_user_km.sh
```

Для тестирования работы программного компонента графового представления персоны пользователя на примере генеративного навыка `knowledge-prompted-skill` необходимо собрать дистрибутив `dream_kg_prompted` на базе фреймворка для разработки многонавыковых ИИ-ассистентов с помощью команды из корневой директории:

```
docker-compose -f docker-compose.yml -f assistant_dists/dream_kg_prompted/docker-compose.override.yml -f assistant_dists/dream_kg_prompted/dev.yml up --build 
```

Затем в отдельной вкладке терминала начать диалог с ботом с помощью команды из корневой директории:

```
docker-compose exec agent python -m deeppavlov_agent.run agent.channel=cmd agent.pipeline_config=assistant_dists/dream_kg_prompted/pipeline_conf.json
```