# Программный компонент для создания графового представления персоны пользователя по контексту диалога для английского языка

Программный компонент для создания графового представления персоны пользователя состоит из:

- модуля `property-extraction`: для извлечения сущностей из высказываний в виде триплетов
- модуля `custom-entity-linking`: для связывания ранее упоминавшихся сущностей с их идентификаторами в базе знаний
- модуля `user-knowledge-memorizer`: для создания графа знаний пользователя и добавления в него новых сущностей
- генеративного навыка `knowledge-prompted-skill`: примера демонстрации работы программного компонента для создания графового представления персоны пользователя на базе платформы DeepPavlov Dream

## Запуск и тестирование программного компонента для создания графового представления персоны пользователя

Запуск и тестирование модуля `property-extraction` описаны в файле [README_integration.md](/README_integration.md)

Для запуска и тестирования модуля `custom-entity-linking` необходимо выполнить следующую команду из корневой директории:

```
bash tests/test_custom_el.sh
```

Для запуска и тестирования модуля `user-knowledge-memorizer` необходимо выполнить следующую команду из корневой директории:

```
bash tests/test_user_km.sh
```

Для тестирования работы программного компонента графового представления персоны пользователя на примере генеративного навыка `knowledge-prompted-skill` необходимо собрать дистрибутив `dream_kg_prompted` на базе платформы DeepPavlod Dream с помощью команды из корневой директории:

```
docker-compose -f docker-compose.yml -f assistant_dists/dream_kg_prompted/docker-compose.override.yml -f assistant_dists/dream_kg_prompted/dev.yml up --build 
```

Затем в отдельной вкладке терминала начать диалог с ботом с помощью команды из корневой директории:

```
docker-compose exec agent python -m deeppavlov_agent.run agent.channel=cmd agent.pipeline_config=assistant_dists/dream_kg_prompted/pipeline_conf.json
```