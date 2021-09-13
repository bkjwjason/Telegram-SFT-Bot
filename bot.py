import logging
import gspread
import os
import pytz
import telegram
import datetime
from oauth2client.service_account import ServiceAccountCredentials
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, ChatAction
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext)
from functools import wraps

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

# Set scope to use when authenticating:
scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/spreadsheets',
         'https://www.googleapis.com/auth/drive.file',
         'https://www.googleapis.com/auth/drive']

path = '/app'

creds = ServiceAccountCredentials.from_json_keyfile_name(path + '/creds.json', scope)

client = gspread.authorize(creds)
sheet = client.open('Record').sheet1
PORT = int(os.environ.get('PORT', '8443'))


my_date = datetime.datetime.now(pytz.timezone('Asia/Singapore')).strftime('%d/%m/%Y')

#FlowChart: SIGN_IN --> CHECKHEALTH --> RANKNAME1 --> RANKNAME2 --> SUBUNIT --> ACTIVITY --> GET_TIME --> CONFIRMATION (IF NON SPORTS AND GAMES) --> SUBMIT --> SIGNOUT
#           SIGN_IN --> CHECKHEALTH --> RANKNAME1 --> RANKNAME2 --> SUBUNIT --> ACTIVITY --> GET_TIME(IF SPORTS, CHOOSE WHICH SPORT) --> SPORTSCONFIRMATION --> CONFIRMATION (IF NON SPORTS AND GAMES) --> SUBMIT --> SIGNOUT
SIGN_IN, CHECKHEALTH, RANKNAME1,RANKNAME2, SUBUNIT, ACTIVITY, SPORTSCONFIRMATION, GET_TIME, CONFIRMATION, SUBMIT, SIGNOUT = range(11)

# Show that bot it "TYPING"
def send_typing_action(func):
    @wraps(func)
    def command_func(update, context, *args, **kwargs):
        context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
        return func(update, context,  *args, **kwargs)

    return command_func

#Dictionary that maps a number to activity
activity_dict = {'1': "Statics", '2': "Run < 3km", '3': "Gym", '4': "Sports and Games"}
sports_dict = {'1' : 'Basketball', '2': 'Football', '3': 'Badminton', '4': 'Floorball', '5': 'Captain\'s ball', '6': 'Ultimate Frisbee'}

# the database in a form of dictionary. The user's ID is used as the key, and value is a list
# of data collected by asking the questions. Each key will have a list of its own, and when the
# user signs out or cancels the conversation, the key-value pair will be deleted.
#User ID is used as the key, and index refers to the specific row that the User's ID is written. Used to edit data when signing out.
userID_savedindex = {}
userID_database = {}

@send_typing_action
def password(update: Update, _: CallbackContext):
    # Ask for password
    update.message.reply_text(
        'Please enter the password: ', reply_markup=ReplyKeyboardRemove()
    )
    return SIGN_IN

@send_typing_action
def start(update: Update, _: CallbackContext):
    if update.message.text == 'Password here':
        #If Password is correct, Start Conversation checks time
        morning_start =  '07:00'
        morning_end = '09:00'
        night_start = '19:00'
        night_end = '22:00'
        now = datetime.datetime.now(pytz.timezone('UTC'))
        singapore_time = now.astimezone(pytz.timezone('Asia/Singapore'))
        check_in_time = singapore_time.strftime("%H:%M")
        if (check_in_time >= morning_start and check_in_time <= morning_end):
            userID = str(update.message.chat_id)
            if userID not in userID_database:
                userID_database[userID] = []
                reply_keyboard = [['Yes', 'No']]
                update.message.reply_text(
                    'Hi! My name is SFT Bot. I will help you sign in for Self Regulated Training. '
                    'Send /cancel to stop talking to me.\n\n'
                    'Would you like to sign in for SFT?\n'
                    'Enter Yes or No.',
                    reply_markup=ReplyKeyboardMarkup(reply_keyboard)
                )
                return CHECKHEALTH
            else:
                update.message.reply_text(
                    'Please sign out from your previous session before starting a new session.'
                )
                ConversationHandler.END

        elif (check_in_time >= night_start and check_in_time <= night_end):
            userID = str(update.message.chat_id)
            if userID not in userID_database:
                userID_database[userID] = []
                reply_keyboard = [['Yes', 'No']]
                update.message.reply_text(
                    'Hi! My name is SFT Bot. I will help you sign in for Self Regulated Training. '
                    'Send /cancel to stop talking to me.\n\n'
                    'Would you like to sign in for SFT?\n'
                    'Enter Yes or No.',
                    reply_markup=ReplyKeyboardMarkup(reply_keyboard)
                )
                return CHECKHEALTH
            else:
                update.message.reply_text(
                    'Please sign out from your previous session before starting a new session.'
                )
                ConversationHandler.END

        else:
            update.message.reply_text(
            'The time now is: ' + str(check_in_time) + '\n\n'
            'It is currently not within SFT Timings. Sign In cancelled. \n\n'
            'SFT Timings are: <b>0700hrs - 0900hrs, and 1900hrs - 2200hrs</b>.', parse_mode='HTML'
            )
            return ConversationHandler.END
    else:
        # Ends conversation when password is wrong
        update.message.reply_text(
            'Wrong password, please reattempt the sign in by /start '
        )
        return ConversationHandler.END

@send_typing_action
def check_health(update: Update, _: CallbackContext):
    # A list of questions for the User to read through before continuing with the form. Sent as a photo.
    # If he says Yes to any of the questions listed, End conversation.
    if update.message.text == 'Yes' or update.message.text == 'yes':
        reply_keyboard = [['Yes', 'No']]
        filename = "/app/parq.png"
        update.message.bot.send_photo(update.message.chat_id,open(filename,'rb'),caption='Questionnaire taken from sportsingapore.gov.sg')
        update.message.reply_text(
        '<b>PHYSICAL ACTIVITY READINESS QUESTIONNAIRE (PAR-Q)</b>\n\n'
        'If any of the above is yes, select \'Yes\'. Otherwise, select \'No\'.', parse_mode='HTML', reply_markup = ReplyKeyboardMarkup(reply_keyboard))
        return RANKNAME1
    
    else:
        update.message.reply_text(
            'Sign In cancelled, Have a nice day!'
        )
        userID = str(update.message.chat_id)
        userID_database.pop(userID,None)
        return ConversationHandler.END

    

@send_typing_action
def rankname1(update: Update, _: CallbackContext):
     # If user says No to all questions on PARQ, Continues Sign in Process, asks for rank and name of Person 1
    if update.message.text == 'No' or update.message.text == 'no':
        update.message.reply_text(
        'What is your rank and name? \n\n'
        'Enter in this format: Rank<space>Name\n'
        'Send /cancel to stop talking to me.\n', reply_markup=ReplyKeyboardRemove() )
        return RANKNAME2

    # If user says Yes to any questions, Quits Sign in Process
    elif update.message.text == 'Yes' or update.message.text == 'yes':
        update.message.reply_text(
        'Please consult your Unit Medical Officer before you commence training. Sign In cancelled.', reply_markup=ReplyKeyboardRemove()
        )
        userID = str(update.message.chat_id)
        userID_database.pop(userID,None)
        return ConversationHandler.END
    else:
        #Non applicable answers
        update.message.reply_text(
        'Please answer Yes or No.', reply_markup=ReplyKeyboardRemove()
        )

@send_typing_action
def rankname2(update: Update, _: CallbackContext):
    #Gets rank and name of 2nd person (the buddy)
    user = update.message.from_user
    logger.info("RankName %s: %s", user.first_name, update.message.text)
    userID = str(update.message.chat_id)
    userID_database[userID].append(str(my_date))
    userID_database[userID].append(update.message.text)
    update.message.reply_text(
    'What is your buddy\'s rank and name?\n'
    'Enter in this format: Rank<space>Name\n'
    'Send /cancel to stop talking to me.\n', reply_markup=ReplyKeyboardRemove() )
    return SUBUNIT

@send_typing_action
def get_subunit(update: Update, _: CallbackContext):
    #If Rankname correct format, continues to get the subunit
    userID = str(update.message.chat_id)
    userID_database[userID].append(update.message.text)
    user = update.message.from_user
    logger.info("%s Buddy Rank and Name: %s", user.first_name, update.message.text)
    reply_keyboard = [['BNHQ', 'ALPHA', 'BRAVO','MEC']]
    update.message.reply_text(
        'What subunit are you from? Please enter in CAPS.\n'
        'Enter one: BNHQ, ALPHA, BRAVO, MEC \n'
        'Send /cancel to stop talking to me.\n',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard),
    )
    return ACTIVITY

@send_typing_action
def activity(update: Update, _: CallbackContext):
    #Appends Subunit to list, and asks for activity
    userID = str(update.message.chat_id)
    userID_database[userID].append(update.message.text)
    reply_keyboard = [['1', '2', '3','4']]
    user = update.message.from_user
    logger.info("Which Subunit? %s: %s", user.first_name, update.message.text)
    update.message.reply_text(
            'What activity would you be doing today?\n'
            'Please choose only one option. \n\n'
            '1: Statics \N{flexed biceps} \n'
            '2: Run (3km) 🏃 \n'
            '3: Gym \U0001F3CB  \n'
            '4: Sports and Games ⛹️ \n'
             'Send /cancel to stop talking to me.',
            reply_markup=ReplyKeyboardMarkup(reply_keyboard),
        )
    return GET_TIME

@send_typing_action
def get_time(update: Update, _: CallbackContext):
    userID = str(update.message.chat_id)
    # IF User chose sports, check which sport you want to play
    if update.message.text == '4':
        reply_keyboard = [['1','2','3','4','5','6']]
        update.message.reply_text(
            'Which sport would you be playing today?\n'
            'Please choose only one option. \n\n'
            '1: Basketball \U0001F3C0 \n'
            '2: Football \N{soccer ball} \n'
            '3: Badminton \U0001F3F8 \n'
            '4: Floorball \U0001F3D1 \n'
            '5: Captain\'s ball \U0001F3D0 \n'
            '6: Ultimate Frisbee  \U0001F94F \n'
            'Send /cancel to stop talking to me.',
            reply_markup=ReplyKeyboardMarkup(reply_keyboard),
        )
        return SPORTSCONFIRMATION

    else:
        # If user chose option 1-3, asks for expected sign out time
        userID = str(update.message.chat_id)
        userID_database[userID].append(activity_dict[update.message.text])
        update.message.reply_text('What is your expected Sign Out Time? \n \n'
                            'Please enter in HH:MM Format.',reply_markup=ReplyKeyboardRemove())
        return CONFIRMATION

@send_typing_action
def sports_confirmation(update: Update, _: CallbackContext):
    #If user chose "4", after getting the specific sport, asks for time, for safety tracking purposes
    userID = str(update.message.chat_id)
    userID_database[userID].append(sports_dict[update.message.text])
    update.message.reply_text('What is your expected Sign Out Time? \n \n'
                            'Please enter in HH:MM Format.',reply_markup=ReplyKeyboardRemove())
    return CONFIRMATION

@send_typing_action
def confirmation(update: Update, _: CallbackContext):
    #check if valid Sign Out time
    morning_start =  '07:00'
    morning_end = '09:00'
    night_start = '19:00'
    night_end = '22:00'
    if (str(update.message.text) >= morning_start and str(update.message.text) <= morning_end):
        #shows the user all of the data that was submitted, to check before submitting onto excel sheet 
        userID = str(update.message.chat_id)
        now = datetime.datetime.now(pytz.timezone('UTC'))
        singapore_time = now.astimezone(pytz.timezone('Asia/Singapore'))
        time_start = singapore_time.strftime("%H:%M")
        userID_database[userID].append(time_start)
        userID_database[userID].append(update.message.text)
        update.message.reply_text('Please check your details before submitting.\n')
        update.message.reply_text(
                    'Date: ' + userID_database[userID][0] + '\n \n'
                    'Rank/Name: ' + userID_database[userID][1] + '\n \n'
                    'Rank/Name of Buddy: ' + userID_database[userID][2] + '\n \n'
                    'Subunit: ' + userID_database[userID][3] + '\n \n'
                    'Activity: ' + str(userID_database[userID][4]) + '\n \n'
                    'Sign In Time: ' + userID_database[userID][5] + '\n \n'
                    'Expected Sign Out Time: ' + userID_database[userID][6])

        reply_keyboard = [['Yes', 'No']]
        update.message.reply_text('Are they correct? \n \n'
                                'Enter Yes or No.',reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard = True)
                )
        return SUBMIT
    elif (str(update.message.text) >= night_start and str(update.message.text) <= night_end):
        #shows the user all of the data that was submitted, to check before submitting onto excel sheet
        userID = str(update.message.chat_id)
        now = datetime.now(pytz.timezone('UTC'))
        singapore_time = now.astimezone(pytz.timezone('Asia/Singapore'))
        time_start = singapore_time.strftime("%H:%M")
        userID_database[userID].append(time_start)
        userID_database[userID].append(update.message.text)
        update.message.reply_text('Please check your details before submitting.\n')
        update.message.reply_text(
                    'Date: ' + userID_database[userID][0] + '\n \n'
                    'Rank/Name: ' + userID_database[userID][1] + '\n \n'
                    'Rank/Name of Buddy: ' + userID_database[userID][2] + '\n \n'
                    'Subunit: ' + userID_database[userID][3] + '\n \n'
                    'Activity: ' + str(userID_database[userID][4]) + '\n \n'
                    'Sign In Time: ' + userID_database[userID][5] + '\n \n'
                    'Expected Sign Out Time: ' + userID_database[userID][6])

        reply_keyboard = [['Yes', 'No']]
        update.message.reply_text('Are they correct? \n \n'
                                'Enter Yes or No.',reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard = True)
                )
        return SUBMIT
    else:
        update.message.reply_text('Please enter an expected Sign Out Timing within SFT Timings in HH:MM format. \n\n'
                                'SFT Timings are: <b>0700hrs - 0900hrs, and 1900hrs - 2200hrs</b>.', parse_mode='HTML'
        )

@send_typing_action
def submit(update: Update, context: CallbackContext):
    #if data is correct --> Yes, then data will be uploaded onto excel
    if update.message.text == 'Yes' or update.message.text == 'yes':
        print(userID_database)
        global userID
        userID = str(update.message.chat_id)
        # Program to add to GOOGLE SHEETS HERE! 
        Date = userID_database[userID][0]
        Person1 = userID_database[userID][1]
        Person2 = userID_database[userID][2]
        SubUnit = userID_database[userID][3]
        Activity = userID_database[userID][4]
        Time_start = userID_database[userID][5]
        Expected_out = userID_database[userID][6]
        client = gspread.authorize(creds)
        sheet = client.open('Record').sheet1
        data = sheet.get_all_records()
        row_to_insert = [Date,Person1,Person2,SubUnit,Activity,Time_start, Expected_out]
        userID_savedindex[userID] = len(data) +2
        sheet.insert_row(row_to_insert, len(data) + 2)
        #inform user that sign in has been completed
        update.message.reply_text(
            '<b>Sign in completed!</b> \n\n'
            'Some Safety Pointers to note: \n\n'
            '1) SFT must be done minimally in pairs and all participants must remain contactable. \n\n'
            '2) Ensure that you are attired in appropriate clothing with orange luminous belt, footwear and protective gear. \n\n'
            '3) Check CAT Status prior to outdoor SFT. \n\n'
            '4) Perform only allowable PT at designated areas. \n\n'
            '5) No high risk/dangerous activity is allowed during SFT. When in doubt, seek permission from PSOs/OCs before execution. \n\n'
            'Stay Safe & have a great workout! \n\n'
            '<b>Enter /end to sign out from SRT</b>', parse_mode= 'HTML', reply_markup=ReplyKeyboardRemove()
        )
        #Sends sign in notification to respective subunit channels on telegram
        if SubUnit == 'BNHQ':
            bot.sendMessage(chat_id = -1001111111111, text = (
                                                        '🏃New Sign In Entry🏃' + '\n\n'
                                                        'Date: ' + Date + '\n'
                                                        'Rank/Name: ' + Person1 + '\n'
                                                        'Rank/Name of Buddy: ' + Person2 + '\n'
                                                        'Activity: ' + Activity + '\n'
                                                        'Sign in Time: ' + Time_start + '\n'
                                                        'Expected Sign out Time: ' + Expected_out
                                                        ) )
        elif SubUnit == 'ALPHA':
            bot.sendMessage(chat_id = -1001111111111, text = (
                                                        '🏃New Sign In Entry🏃' + '\n\n'
                                                        'Date: ' + Date + '\n'
                                                        'Rank/Name: ' + Person1 + '\n'
                                                        'Rank/Name of Buddy: ' + Person2 + '\n'
                                                        'Activity: ' + Activity + '\n'
                                                        'Sign in Time: ' + Time_start + '\n'
                                                        'Expected Sign out Time: ' + Expected_out
                                                        ) )
        elif SubUnit == 'BRAVO':
            bot.sendMessage(chat_id = -1001111111111, text = (
                                                        '🏃New Sign In Entry🏃' + '\n\n'
                                                        'Date: ' + Date + '\n'
                                                        'Rank/Name: ' + Person1 + '\n'
                                                        'Rank/Name of Buddy: ' + Person2 + '\n'
                                                        'Activity: ' + Activity + '\n'
                                                        'Sign in Time: ' + Time_start + '\n'
                                                        'Expected Sign out Time: ' + Expected_out
                                                        ) )
        elif SubUnit == 'MEC':
            bot.sendMessage(chat_id = -1001111111111, text = (
                                                        '🏃New Sign In Entry🏃' + '\n\n'
                                                        'Date: ' + Date + '\n'
                                                        'Rank/Name: ' + Person1 + '\n'
                                                        'Rank/Name of Buddy: ' + Person2 + '\n'
                                                        'Activity: ' + Activity + '\n'
                                                        'Sign in Time: ' + Time_start + '\n'
                                                        'Expected Sign out Time: ' + Expected_out
                                                        ) )
        # If User does not sign out by end of SFT Timing, Bot will send scheduled message
        # Morning SFT Timing
        t1 = datetime.time(9,00, tzinfo = pytz.timezone('Asia/Singapore'))
        context.job_queue.run_daily(notification, t1, days=(0,1,2,3,4,5,6))
        # Night SFT Timing
        t2 = datetime.time(22,00, tzinfo = pytz.timezone('Asia/Singapore'))
        context.job_queue.run_daily(notification, t2, days=(0,1,2,3,4,5,6))
        return ConversationHandler.END

    #if data is not correct --> No, then user will be prompted to restart the form
    elif update.message.text == 'No' or update.message.text == 'no':
        update.message.reply_text(
            'Please restart the sign in by entering /start.'
        )
        userID = str(update.message.chat_id)
        userID_database.pop(userID,None)
        return ConversationHandler.END

# Reminder Message to user if he has not signed out by end of SFT.
def notification(context: CallbackContext):
    if userID in userID_database:
        context.bot.send_message(int(userID), text = "Hi there, it seems like you have forgotten to sign out. Please sign out, and remind your buddy to sign out as well. Thank you!")


@send_typing_action
def check_end(update: Update, _: CallbackContext):
    #if User's ID (key) not inside the dictionary, means no sign in data. 
    userID = str(update.message.chat_id)
    if userID not in userID_database:
        update.message.reply_text(
            'There is no sign in data. You have already signed out. ')
        return ConversationHandler.END

    else:
        reply_keyboard = [['Yes', 'No']]
        # Checks with user if he really wants to sign out
        now = datetime.datetime.now(pytz.timezone('UTC'))
        singapore_time = now.astimezone(pytz.timezone('Asia/Singapore'))
        time_end = singapore_time.strftime("%H:%M")
        update.message.reply_text(
            'The time now is: ' + str(time_end) + '\n'
            'Are you sure you want to sign out?',reply_markup=ReplyKeyboardMarkup(reply_keyboard)
        )
        return SIGNOUT

@send_typing_action
def sign_out(update: Update, _: CallbackContext):
    if update.message.text == 'Yes' or update.message.text == 'yes':
        # PROGRAM TO ADD SIGN OUT TIME TO GOOGLE SHEETS GO HERE
        userID = str(update.message.chat_id)
        now = datetime.datetime.now(pytz.timezone('UTC'))
        singapore_time = now.astimezone(pytz.timezone('Asia/Singapore'))
        time_end = singapore_time.strftime("%H:%M")
        userID_database[userID].append(time_end)
        sheet.delete_rows(userID_savedindex[userID])
        Date = userID_database[userID][0]
        Person1 = userID_database[userID][1]
        Person2 = userID_database[userID][2]
        SubUnit = userID_database[userID][3]
        Activity = userID_database[userID][4]
        Time_start = userID_database[userID][5]
        Expected_out = userID_database[userID][6]
        row_to_insert = [Date,Person1,Person2,SubUnit,Activity,Time_start,Expected_out,time_end]
        sheet.insert_row(row_to_insert, userID_savedindex[userID])
        update.message.reply_text(
            'Sign out completed, have a nice day!\n',reply_markup=ReplyKeyboardRemove()
        )
        #sends sign out notification to respective subunit channels on telegram
        if SubUnit == 'BNHQ':
            bot.sendMessage(chat_id = -1001111111111, text = (
                                                        '😴New Sign Out Entry😴' + '\n\n'
                                                        'Date: ' + Date + '\n'
                                                        'Rank/Name: ' + Person1 + '\n'
                                                        'Rank/Name of Buddy: ' + Person2 + '\n'
                                                        'Activity: ' + Activity + '\n'
                                                        'Sign in Time: ' + Time_start + '\n'
                                                        'Expected Sign out Time: ' + Expected_out + '\n'
                                                        'Sign out Time: '+ time_end
                                                        ) )
        elif SubUnit == 'ALPHA':
            bot.sendMessage(chat_id = -1001111111111, text = (
                                                        '😴New Sign Out Entry😴' + '\n\n'
                                                        'Date: ' + Date + '\n'
                                                        'Rank/Name: ' + Person1 + '\n'
                                                        'Rank/Name of Buddy: ' + Person2 + '\n'
                                                        'Activity: ' + Activity + '\n'
                                                        'Sign in Time: ' + Time_start + '\n'
                                                        'Expected Sign out Time: ' + Expected_out + '\n'
                                                        'Sign out Time: '+ time_end
                                                        ) )
        elif SubUnit == 'BRAVO':
            bot.sendMessage(chat_id = -1001111111111, text = (
                                                        '😴New Sign Out Entry😴' + '\n\n'
                                                        'Date: ' + Date + '\n'
                                                        'Rank/Name: ' + Person1 + '\n'
                                                        'Rank/Name of Buddy: ' + Person2 + '\n'
                                                        'Activity: ' + Activity + '\n'
                                                        'Sign in Time: ' + Time_start + '\n'
                                                        'Expected Sign out Time: ' + Expected_out + '\n'
                                                        'Sign out Time: '+ time_end
                                                        ) )
        elif SubUnit == 'MEC':
            bot.sendMessage(chat_id = -1001111111111, text = (
                                                        '😴New Sign Out Entry😴' + '\n\n'
                                                        'Date: ' + Date + '\n'
                                                        'Rank/Name: ' + Person1 + '\n'
                                                        'Rank/Name of Buddy: ' + Person2 + '\n'
                                                        'Activity: ' + Activity + '\n'
                                                        'Sign in Time: ' + Time_start + '\n'
                                                        'Expected Sign out Time: ' + Expected_out + '\n'
                                                        'Sign out Time: '+ time_end
                                                        ) )
        userID = str(update.message.chat_id)
        userID_database.pop(userID,None)
        print(userID_database)
        return ConversationHandler.END
    else:
        #if no, ends conversation. Pending sign out
        return ConversationHandler.END

@send_typing_action
def correct_format(update: Update, _: CallbackContext):
    #for any errors in submission format, Bot will send this to user.
    update.message.delete()
    update.message.reply_text(
        'It seems like there was an error. \n'
        'Please type it in the appropriate format: \n\n'
        'For Name: Rank <space> Name\n\n'
        'For Subunit: BNHQ/ALPHA/BRAVO/MEC \n\n'
        'For Activity: 1/2/3/4 (Choose one) \n\n '
        'For Time: HH:MM', reply_markup=ReplyKeyboardRemove() )

@send_typing_action
def cancel(update: Update, _: CallbackContext):
    #if user sends /cancel command, ends conversation
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        'Sign in cancelled, have a great day!', reply_markup=ReplyKeyboardRemove()
    )
    userID = str(update.message.chat_id)
    userID_database.pop(userID,None)
    return ConversationHandler.END

@send_typing_action
def delete_msg(update: Update, _: CallbackContext):
    #Bot will delete any unnecessary messages
    update.message.delete()
    update.message.reply_text(
        'Please don\'t send me unnecessary things like GIFs and Stickers, Thank you.')

@send_typing_action
def yesno(update: Update, _: CallbackContext):
    update.message.reply_text(
        'Please input Yes or No. Thank you')
    
def main() -> None:
    #Run Bot
    # Create the Updater and pass it your bot's token.
    print(userID_database)
    TOKEN = os.environ["TOKEN"]
    global bot
    bot = telegram.Bot(token=TOKEN)
    updater = Updater(TOKEN)


    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    start_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start',password)],
        states = {
            SIGN_IN: [MessageHandler(Filters.text, start)],
            CHECKHEALTH:  [MessageHandler(Filters.text, check_health)],
            RANKNAME1: [MessageHandler(Filters.text, rankname1)],
            RANKNAME2: [MessageHandler(Filters.regex('^\w+\s\.*'), rankname2)],
            SUBUNIT: [MessageHandler(Filters.regex('^\w+\s\.*'), get_subunit)],
            ACTIVITY: [MessageHandler(Filters.regex('^BNHQ$|^ALPHA$|^BRAVO$|^MEC$'), activity)],
            GET_TIME: [MessageHandler(Filters.regex('^1$|^2$|^3$|^4$'), get_time)],
            SPORTSCONFIRMATION: [MessageHandler(Filters.regex('^1$|^2$|^3$|^4$|^5$|^6$'), sports_confirmation)],
            CONFIRMATION: [MessageHandler(Filters.regex('\d\d:\d\d'), confirmation)],
            SUBMIT: [MessageHandler(Filters.regex('^Yes$|^yes$|^No$|^no$'), submit)],
                },
        fallbacks=[CommandHandler('cancel', cancel), MessageHandler(Filters.text, correct_format)]
        )


    end_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('end',check_end)],
        states = {SIGNOUT: [MessageHandler(Filters.regex('^Yes$|^yes$|^No$|^no$'), sign_out)]},
        fallbacks=[CommandHandler('cancel', cancel), MessageHandler(Filters.text, yesno)]
    )

    dispatcher.add_handler(MessageHandler(Filters.sticker|Filters.animation|Filters.audio|Filters.document,delete_msg))
    dispatcher.add_handler(start_conv_handler)
    dispatcher.add_handler(end_conv_handler)
    dispatcher.add_handler(CommandHandler('cancel', cancel))


    # Start the Bot
    updater.start_webhook(listen="0.0.0.0",
                          port=PORT,
                          url_path=TOKEN,webhook_url= 'https://yourwebappname.herokuapp.com/' + TOKEN)


    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
