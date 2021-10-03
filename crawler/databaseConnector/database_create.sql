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
