### Config
* `mode`: 
  * `friends`: crawl friends from uncrawled users aswell as their profile information
  * `diaries`: crawl diaries from uncrawled users which has a public diary
  * `diaries-test`: crawl diaries but start with `initial-users` no matter if there arleady crawled
* `sleep-time`: how long should the crawler sleep
* `database-path`: path to the sqllite database file
* `database-backup-folder`: folder in which database backups should be stored
* `initial-users`: list of usernames which will be added to the db at start
* `friend-page-limit`: max number of friend pages requested for one profile
* `log-level`: one of python logging log levels e.g. INFO or DEBUG
* `crawler-timeout`: maximum wait time in seconds for a request made by the crawler
* `crawler-max-retries`: maximum time of retrying if a request timeout before exiting