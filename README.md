
# :robot: The Emotion Game :cloud:  
  
This project is a simple game made for University of Salerno Cloud computing's course. It use some of Microsoft Azure's services, such as:  

* Azure computer vision service
* Azure Speech-To-Text service
* Azure Bing search service
* Azure virtual machine service
* Azure SQL
* Azure SQL server

Each subscription key can be changed in ```config.yml``` file
  
## :gear: Installation and configuration
First step is clone project and install requirements
```bash
git clone https://github.com/AnItalianMan/TheEmotionGame
```
Go to project folder and run the following command
```bash
pip install -r requirements.txt
```
Set right subscriptions key in ```config.yml``` file

```yml
TelegramBotToken: <bot_telegram_token>
AzureSpeechToken: <Azure_speech_to_text_subscription_key> 
AzureBingToken: <Azure_bing_search_subscription_key>
AzureVisionToken: <Azure_computer_vision_subscription_key>
AzureDatabase:  
  DatabaseServerEndPoint: <Azure_sql_server_endpoint>
  Username: <Azure_sql_server's_username>
  Password: <Azure_sql_server's_password>  
  DatabaseName: <database_name>
```

### :wrench: Create database
Go to Azure SQL panel on Azure control panel and create the database.
This is the script for build database.
```SQL 
CREATE TABLE theemotiongame(
	ChatID INT PRIMARY KEY NOT NULL,
	nickname VARCHAR(255) NOT NULL,
	giocate INT NOT NULL,
	vinte INT NOT NULL
)
```


## :rocket: Run Bot
Go to project folder and run ```app.py``` file
  
```bash
python app.py
```  
  
Project will be executed and the bot been ready to play.
You can go on Telegram bot chat and write ```/start``` to start a game.

## :books: Rules
The game is composed by two players: one will have to send a photo, and the another one will have to send an audio.
The photo must depict a person's emotion. Only italian's word are accepted, for example:
* rabbia (anger)
* disprezzo (contempt)
* disgusto (disgust)
* paura (fear)
* felice (happy)
* neutro (neutral)
* tristezza (sadness)
* sorpreso (surprised)

In the audio you have to try to guess the emotion represented by the photo, so the audio must be contain an emotion form the list above. If you say the wrong emotion, you will be asked to send a new audio.
If the audio contains the right emotion, player who send the audio earn one point. First player who earn 3 point win.

## :iphone: Commands list
* ```/start```: Start a new game
* ```/stop```: Stop the current game if there is a current game
* ```/top```: return a list of top 3 global players

