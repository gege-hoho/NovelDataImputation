# Crawler

The crawler can be configured using `config.json` and `secret.json`.

2. `cd crawler`
3. Create a file named `secret.json` and copy over the content of `secret_example.json`
4. Fill in an MFP username, password and e-mail into `secrets.json`.
5. Configure the crawler in `config.json`
6. Create logs folder`mkdir logs` and database backup folder `mkdir databaseBackups`
7. install SQLite3`sudo apt install sqlite3` and `pip3 -r requirements.txt`
8. Create empty DB `sqlite3 databaseConnector/mfp.db < databaseConnector/database_create.sql`
9. The crawler is started using `python3 main.py`

### Config
* `mode`: 
  * `friends`: crawl friends from uncrawled users aswell as their profile information
  * `diaries`: crawl diaries from uncrawled users which has a public diary
  * `diaries-test`: crawl diaries but start with `initial-users` no matter if they're already crawled
* `sleep-time`: how long should the crawler sleep
* `database-path`: path to the sqllite database file
* `database-backup-folder`: folder in which database backups should be stored
* `initial-users`: list of usernames which will be added to the db at start
* `friend-page-limit`: max number of friend pages requested for one profile
* `log-level`: one of python logging log levels e.g. INFO or DEBUG
* `crawler-timeout`: maximum wait time in seconds for a request made by the crawler
* `crawler-max-retries`: maximum time of retrying if a request timeout before exiting
* `database-backup-time`: time interval in hours at which backups from the database will be created

# BRITS
## Data export from Database to BRITS
The data in the SQLite database is in no format that can be used by BRITS.
Two scripts are responsible for this. Both are located in the `preProcessor` folder.
### prerequisites
* Have python packages installed:  pytorch, nltk, gensim
* Have SQLite3 installed
* Have a crawled database
* Have the food classification model folder (with bigram model, word2vec model and classifier)
  * Download here: https://syncandshare.lrz.de/getlink/fiXhWt3aXmHZeEZJDFEzXvTG/models.zip
  * Or train self in FoodItemClassification3.ipynb and WordEmbeddingModel.ipynb

### classifier.py
`classifier.py` contains a pytorch model representation of the `FoodClassificationCnnModel`,
trained in the FoodClassification3 Notebook. It also contains a wrapper, that handles the initialisation
of the Pytorch model and allows for classification of food items based on the bigram model and the word2vec model:
```python
# path to a folder containing: 
# the bigrammodel: bigram_model.pkl
# the word2vec model: mymodel
# the classification model: model93.2
model_folder = "./" 
classy = Classifier(model_folder)

cat = classy.classify("Homemade - Grilled Turkey Burger") # gets category as number
cat = classy.get_cat_name(cat) # convert to category name
print(cat)# -> Meat/Poultry/Other Animals

# or only do tokenization and bigram detection
tokens = classy.preprocess("Powerade - Zero - Fruit Punch (32 Fl oz)") 		
print(tokens) # -> [powerade zero, fruit punch] 
# and do the embedding
classy.embedd(tokens) #-> list of 300 dimensional token vectors
```

### export.py
`export.py` extract only full meal sequences from the db. 
A sequence is full if the day has at least 1600 kcal and breakfast, lunch and dinner
Sequences are stored and outputted in a pickle file.
#### arguments
1. number of users to request from database
2. folderpath to food classification model folder
3. path to database file
4. pickle output path
#### example
`python3 export.py 20 "data/models" "/home/gregor/Uni/Masterarbeit/preProcessor/data/mfp.db" "test.pickle"`

### converttobrits.py
`converttobrits.py` converts the pickle exported from `export.py` 
and creates the dataformat used in the `BRITS` notebook in order to train
the imputation model.

It creates two files: `brits_test.pickle` and `brits_train.pickle`, with both having
the same format:
```json
[
  {
    "forward": [
      {
        "values": [1.0, -11.02,...],
        "masks": [1.0,1.0,..],
        "deltas": [1.0,1.0,...],
        "eval_masks": [0.0,0.0,...],
        "evals": [1.0, 4.23,...]
      },
      ...
    ],
    "backward": [...]
  },
  {...}
]
```
Each file contains a list of n dictionaries for n samples in the test/train set.
Each dictionary contains `forward` and `backward` entries. `backward` is as `forward` but reversed.
`forward` and `backward` is a list of 28 entries for one sequence. Each entry in the sequence has:
* `values`: values with artificial missing set to 0 (mealtype,calories,carbs,fat,protein,cholest,sodium,sugar,fiber,weekday)
* `evals`: like values but without artificial gaps
* `masks`: indicate if value is missing (1 for present, 0 for missing)
* `deltas`: timesteps since last present value (1 if last value was present, 2 if one before was missing,...)
* `eval_masks`: 1 if `evals` is present and values is missing, 0 if `value` is present

The script can take several arguments

positional arguments:
*  input: Pickle file used as input
*  output: Folderpath were to put the output files

optional arguments:
*  --user_id [USER_ID]: Only weeks of a specific user-id are extracted or -1 (default)
*  --non_norm [NON_NORM]: If true export as non normalized
*  --max_cat [MAX_CAT]: Number of categories to be exported per sequence entry or 0 (default)
*  --only_max_user [ONLY_MAX_USER]: If true only entries of the user with the most entries is exported
*  --limit_data_per_user [LIMIT_DATA_PER_USER]: Max number of weeks for one user exported or -1 for unlimited (default)
*  --missing [MISSING]: Percentage of missing meals 0.1(default)
*  --train [TRAIN]: Percentage of meals in train set 0.9(default)
*  --limit_categories [LIMIT_CATEGORIES]: only take the most used x cateogries (default 30)
*  --skip_over_cals [SKIP_OVER_CALS]: skip weeks with meals over x calories or -1 (default)

The files from the output path are then used in the BRITS Notebook.
