# Программный компонент для системы формирования персональности бота: для создания графового представления персоны бота

Программный компонент для создания графового представления персоны бота состоит из:

- модуля `property-extraction`: для извлечения сущностей из высказываний в виде триплетов
- модуля `custom-entity-linking`: для связывания ранее упоминавшихся сущностей с их идентификаторами в базе знаний
- модуля `bot-knowledge-memorizer`: для создания графа знаний бота и добавления в него новых сущностей
- генеративного навыка `bot-knowledge-prompted-skill`: примера демонстрации работы программного компонента для создания графового представления персоны бота на базе платформы DeepPavlov Dream

## Запуск и тестирование программного компонента для создания графового представления персоны бота

Запуск и тестирование модуля `property-extraction` описаны в файле [README_integration.md](/README_integration.md)

Запуск и тестирование модуля `custom-entity-linking` описаны в файле [README_user_persona_in_knowledge_graphs.md](/README_user_persona_in_knowledge_graphs.md)

Для запуска и тестирования модуля `bot-knowledge-memorizer` необходимо выполнить следующую команду из корневой директории:

```
bash tests/test_bot_km.sh
```

Для тестирования работы программного компонента графового представления персоны бота на примере генеративного навыка `bot-knowledge-prompted-skill` необходимо собрать дистрибутив `dream_bot_kg_prompted` на базе платформы DeepPavlod Dream с помощью команды из корневой директории:

```
docker-compose -f docker-compose.yml -f assistant_dists/dream_bot_kg_prompted/docker-compose.override.yml -f assistant_dists/dream_bot_kg_prompted/dev.yml up --build
```

Затем в отдельной вкладке терминала начать диалог с ботом с помощью команды из корневой директории:

```
docker-compose exec agent python -m deeppavlov_agent.run agent.channel=cmd agent.pipeline_config=assistant_dists/dream_bot_kg_prompted/pipeline_conf.json
```