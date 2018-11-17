# design

## data model

```text
/users/{}

user_id: "string"
notification: 
    type: "slack"
    incoming_web_hook: "string"
    slack_channel: "string"

/users/{}/monitors/{}

monitor_id: "string"
user_id: "string"
wish_list_url: "string"
threshold:
    points: int
    discount_rate: int
    
/system/queues/users/{}

user_id: "string"
ttl: int
notification: 
    type: "slack"
    incoming_web_hook: "string"
    slack_channel: "string"

/system/queues/monitors/{}

monitor_id: "string"
user_id: "string"
ttl: int
wish_list_url: "string"
threshold:
    points: int
    discount_rate: int
notification: 
    type: "slack"
    incoming_web_hook: "string"
    slack_channel: "string"

/system/queues/items/{}

queue_id: "string"
item_url: "string"
ttl: int
threshold:
    points: int
    discount_rate: int
notification: 
    type: "slack"
    incoming_web_hook: "string"
    slack_channel: "string"


```

## flow

### scheduled event

```puml
@startuml

control event

event -> observer_system: 

database DB_users
database DB_queue_user

observer_system <-- DB_users :data
observer_system --> DB_queue_user: data
@enduml
```

### DB_queue_user

```puml
@startuml

database DB_queue_user

DB_queue_user -> observer_user: Stream
database DB_monitors
database DB_queue_monitor

observer_user <-- DB_monitors :data
observer_user --> DB_queue_monitor: data

DB_queue_user <-- observer_user: delete


@enduml
```


### DB_queue_monitor

```puml
@startuml

database DB_queue_monitor

DB_queue_monitor -> observer_monitor: Stream

observer_monitor <--> amazon.jp: data in wish list

database DB_queue_item

observer_monitor --> DB_queue_item: data

DB_queue_monitor <-- observer_monitor: delete
@enduml
```


### DB_queue_item

```puml
@startuml

database DB_queue_item
DB_queue_item -> observer_item: Stream

database DB_chache_item
observer_item <--> DB_chache_item: data
observer_item <--> amazon.jp: data

actor user
observer_item -> user: notification

observer_item --> DB_queue_item: delete
@enduml
```














