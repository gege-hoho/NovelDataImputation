create table user
(
    user               INTEGER not null
        primary key autoincrement,
    username           TEXT    not null,
    gender             TEXT,
    location           TEXT,
    joined_date        TEXT,
    food_crawl_time    TEXT,
    friends_crawl_time TEXT,
    profile_crawl_time TEXT,
    has_public_diary   int,
    age                int
);

create unique index user_username_uindex
    on user (username);

create table meal_item
(
    meal_item integer not null
            primary key autoincrement,
    name      text not null,
    quick_add  int not null default 0,
    calories  int,
    carbs     int,
    fat       int,
    protein   int,
    cholest   int,
    sodium    int,
    sugars    int,
    fiber     int
);

create unique index meal_item_name_quickadd_uindex
    on meal_item (name, quick_add);

create table meal_history
(
    user      integer not null
        references user,
    meal_item integer not null
        references meal_item,
    date      text    not null,
    meal      text    not null
);

create table meal_statistics
(
    user    int
        references user,
    time    int,
    entries int
);

create table meal_history_flat
(
    meal_history_quick integer not null
            primary key autoincrement,
    date      text    not null,
    meal      text    not null,
    user      int
        references user,
    name      text not null,
    quick_add int not null default 0,
    calories  int,
    carbs     int,
    fat       int,
    protein   int,
    cholest   int,
    sodium    int,
    sugars    int,
    fiber     int
);
create index meal_history_flat_index
    on meal_history_flat (name);

