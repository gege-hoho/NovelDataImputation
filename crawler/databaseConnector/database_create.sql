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
    has_public_diary   int
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
    meal      text    not null,
    constraint user_meal_item_pk
        primary key (user, meal_item)
);

