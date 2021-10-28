import logging
import os
from telegram import Update, ForceReply, ChatAction, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler, CallbackQueryHandler
from random import randint, shuffle
import requests
import xmltodict

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

MAIN = 0
INPUT_TEXT = 1
SELECT_USER = 2


# Define a few command handlers. These usually take the two arguments update and context.
def start(update: Update, context: CallbackContext) -> int:
    
    user = update.message.from_user
    
    update.message.reply_text(
        text=f'Bienvenido {user.first_name}! ¿Que deseas hacer?',        
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(text='Listar juegos', callback_data='select_user')],
            [InlineKeyboardButton(text='Saluda', callback_data='saluda')],
            [InlineKeyboardButton(text='Sortea', callback_data='sortea')]
        ])
    )

    return MAIN

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
    context.bot.send_message(chat_id=update.effective_chat.id,text=get_shuffle_users())

def get_shuffle_users() -> str:
    """genera una lista desordenada"""    
    users_list = ['juane','juank','matias','mauro']
    
    shuffle(users_list)  
    users_list = [ '{0}. {1}'.format(i+1,users_list[i]) for i in range(len(users_list))]  
    users_string = "\n".join(users_list)

    return users_string

def saluda_command_handler(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Dime tu nombre:')
    return INPUT_TEXT

def saluda_callback_handler(update: Update, context: CallbackContext) -> int:    
    query = update.callback_query
    query.answer()

    query.edit_message_text(
        text='Dime tu nombre:'
    )
    return INPUT_TEXT

def list_users_callback_handler (update: Update, context: CallbackContext) -> int:
    users = ['maurocor','juankazon','maticepe','juanecasla']

    query = update.callback_query
    query.answer()

    buttons = []
    for user in  users:
        buttons.append([InlineKeyboardButton(text=f'{user}', callback_data=f'user_{user}')])

    reply_markup = InlineKeyboardMarkup(buttons)

    query.edit_message_text(            
        text=f'Seleccione un usuario:'
    )

    query.edit_message_reply_markup(            
        reply_markup=reply_markup
    )

    return SELECT_USER

def input_text(update: Update, context: CallbackContext) -> int:
    text = update.message.text

    chat = update.message.chat
    chat.send_action(
        action=ChatAction.TYPING,
        timeout=None

    )

    saludo = 'Hola {0}\!\n'.format(text)

    update.message.reply_text(saludo, parse_mode='MarkdownV2')

    return ConversationHandler.END

def user_collection_callback_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    user = query.data[5:]

    game_list = get_bgg_collection_by_user(user)

    text = f'Juegos de {user}:\n\n'    
    for game in game_list:
        text += '[{name}]({url_game})\n'.format(name=game['name'],url_game=game['url_game'])

    query.edit_message_text(            
        text=text,
        parse_mode='Markdown'
    )

    return ConversationHandler.END

def get_bgg_collection_by_user(user) -> list:
    """ get bgg collection by user - filter own"""
    game_list = []           
    url = "https://www.boardgamegeek.com/xmlapi/collection/{user}?own=1".format(user=user)        
    response = requests.get(url)
    data = xmltodict.parse(response.content)
    
    for item in data['items']['item']:
        bgg_id = item['@objectid']
        url_game =  f'https://boardgamegeek.com/boardgame/{bgg_id}'
        game_list.append({
            'name': item['name']['#text'],
            'thumbnail': item['thumbnail'],
            'owner': user,
            'url_game': url_game
            })
    
    return game_list

def sortea_callback_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    query.edit_message_text(            
        text=get_shuffle_users(),
        parse_mode='Markdown'
    )

    return ConversationHandler.END

def main() -> None:
    """Start the bot."""

    # Create the Updater and pass it your bot's token.    
    token = os.environ['TOKEN']    
    updater = Updater( token )

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    #dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("mesa", mesa))
    dispatcher.add_handler(CommandHandler("sortea", sortea))
 

    dispatcher.add_handler(ConversationHandler(
        entry_points=[
            CommandHandler('start', start)
        ],

        states={
            MAIN:[
                CallbackQueryHandler(pattern='saluda', callback=saluda_callback_handler),
                CallbackQueryHandler(pattern='sortea', callback=sortea_callback_handler),
                CallbackQueryHandler(pattern='select_user', callback=list_users_callback_handler),
            ],
            SELECT_USER:[
                CallbackQueryHandler(pattern='user_', callback=user_collection_callback_handler),
            ],
            INPUT_TEXT: [
                MessageHandler(Filters.text, callback=input_text)
            ]
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