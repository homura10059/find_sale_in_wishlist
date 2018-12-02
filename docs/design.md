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

### `/system/queues/monitors/{}`

```yaml
wish_list_url: string(Hash Key)
user_id: string(Sort Key)
expired: int(TTL)
threshold:
    points: int
    discount_rate: int
notification: 
    type: "slack"
    incoming_web_hook: string
    slack_channel: string
item_urls:
    - "string"
    - "string"
    - "string"
```

これがdeleteされたら

### `/system/queues/items/{}`

```yaml
item_url: string(Hash Key)
expired: int(TTL)
```



## flow

### director_of_system

```puml
@startuml

control event

event -> director_of_system: 

database users
database queue_monitor

director_of_system <-- users :data
director_of_system --> queue_monitor: data
@enduml
```

### DB_queue_monitor

```puml
@startuml

database queue_monitor

queue_monitor -> worker_monitor: Stream

worker_monitor <--> amazon.jp: data in wish list

database queue_item

worker_monitor --> queue_item: data

@enduml
```

```puml
@startuml

database queue_monitor

queue_monitor <-- queue_monitor: delete from ttl

queue_monitor -> notifier: Stream

database chache_item
notifier <-- chache_item: data


actor user
notifier -> user: notification

@enduml
```


### queue_item

```puml
@startuml

database queue_item
queue_item -> worker_item: Stream
worker_item <-- amazon.jp: data

database chache_item
worker_item --> chache_item: data

worker_item --> queue_item: delete
@enduml
```














