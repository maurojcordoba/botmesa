import logging
import os
from telegram import Update, ForceReply, ChatAction
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
from random import randint, shuffle
import requests
import xmltodict

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

INPUT_TEXT = 0

PORT = int(os.environ.get('PORT', 8443))

# Define a few command handlers. These usually take the two arguments update and context.
def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    update.message.reply_markdown_v2(
        fr'Hola {user.mention_markdown_v2()}\!',
        reply_markup=ForceReply(selective=True),
    )


def echo(update: Update, context: CallbackContext) -> None:    
    update.message.reply_text(update.message.text)


def mesa(update: Update, context: CallbackContext) -> None:
    """Sortea el juego de mesa segun bgg collection list"""    
    users = ['maurocor','juankazon','maticepe','juanecasla']
    
    # elige usuario random
    user = users[randint(0,len(users))]
    
    # busca juegos de bgg del usuario
    game_list = []           
    url = "https://www.boardgamegeek.com/xmlapi/collection/{user}?own=1".format(user=user)        
    response = requests.get(url)
    data = xmltodict.parse(response.content)
    
    for item in data['items']['item']:
        game_list.append({'name': item['name']['#text'], 'thumbnail': item['thumbnail'], 'owner': user})
    
    # elige juego random
    shuffle(game_list)
    game = game_list[randint(0,len(game_list)-1)]    

    # contesta en TG
    caption =  "*{name}*\n{owner}".format(name=game['name'],owner=game['owner'])   
    context.bot.sendPhoto(chat_id=update.effective_chat.id, photo = game['thumbnail'] , caption=caption, parse_mode="Markdown")

def sortea(update: Update, context: CallbackContext) -> None:
    """genera una lista desordenada"""    
    users_list = ['juane','juank','matias','mauro']
    
    shuffle(users_list)  
    users_list = [ '{0}. {1}'.format(i+1,users_list[i]) for i in range(len(users_list))]  
    users_string = "\n".join(users_list)

    # contesta en TG        
    context.bot.send_message(chat_id=update.effective_chat.id,text=users_string)

def saluda_command_handler(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Dime tu nombre:')
    return INPUT_TEXT

def input_text(update: Update, context: CallbackContext) -> int:
    text = update.message.text

    chat = update.message.chat
    chat.send_action(
        action=ChatAction.TYPING,
        timeout=None

    )

    saludo = 'Hola {0}!!!!'.format(text)

    update.message.reply_text(saludo)

    return ConversationHandler.END

def main() -> None:
    """Start the bot."""

    # Create the Updater and pass it your bot's token.    
    token = os.environ['TOKEN']    
    updater = Updater( token )

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("mesa", mesa))
    dispatcher.add_handler(CommandHandler("sortea", sortea))

 

    dispatcher.add_handler(ConversationHandler(
        entry_points=[
            CommandHandler('saluda', saluda_command_handler)
        ],

        states={
            INPUT_TEXT: [MessageHandler(Filters.text, callback=input_text)]
        },

        fallbacks=[]
    ))

    # on non command i.e message - echo the message on Telegram    
    #dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))


    # Start the Bot
    updater.start_polling()
 
    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()