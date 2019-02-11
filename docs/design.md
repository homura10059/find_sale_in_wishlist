# design

## data model

### `/users/{}`

```yaml
user_id: string(Hash Key)
monitors:
    -
    wish_list_url: string
    threshold:
        points: int
        discount_rate: int
    notification:
        type: "slack"
        incoming_web_hook: string
        slack_channel: string
    -
    wish_list_url: string
    threshold:
        points: int
        discount_rate: int
    notification:
        type: "slack"
        incoming_web_hook: string
        slack_channel: string
```

### `/items/{}`

```yaml
'url': url
'book_title': book_title
'latest':
    'discount_rate': discount_rate
    'discount_price': discount_price
    'loyalty_points': loyalty_points
    'price': price
    'updated': time
'best':
    'discount_rate': discount_rate
    'discount_price': discount_price
    'loyalty_points': loyalty_points
    'price': price
    'updated': time

```

## flow

### director_of_system

```puml
@startuml

control event
database users

event -> director_of_system:


director_of_system --> users :request
director_of_system <-- users :data
director_of_system --> notifier: data
... paralle request ...
director_of_system --> notifier: data
@enduml
```
``

### notifier

```puml
@startuml
director_of_system -> notifier: data

notifier -> worker_of_item: request
... paralle request ...
notifier -> worker_of_item: request

...
... wait response ...
...

notifier <- worker_of_item: book_data
... paralle responce ...
notifier <- worker_of_item: book_data


actor user
notifier -> user: notification

@enduml
```


### worker_of_item

```puml
@startuml


notifier -> worker_of_item: request
worker_of_item <-- amazon.jp: data

database chache_item
worker_of_item --> chache_item: data

worker_of_item --> notifier: book_data
@enduml
```














