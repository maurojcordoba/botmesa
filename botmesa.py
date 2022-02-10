import logging
import os
from telegram import Update, ChatAction, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler, CallbackQueryHandler
from random import randint, shuffle
import bgg

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

MAIN = 0
SELECT_USER = 2

users_bgg = ['maurocor','juankazon','maticepe','juanecasla', 'saga_kanon']

# Define a few command handlers. These usually take the two arguments update and context.
def start(update: Update, context: CallbackContext) -> int:
    
    user = update.message.from_user
    
    update.message.reply_text(
        text=f'Bienvenido {user.first_name}! ¿Que deseas hacer?',        
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(text='Listar juegos', callback_data='listajuegos')],            
            [InlineKeyboardButton(text='Sortear jugador', callback_data='sorteajugador')],
            [InlineKeyboardButton(text='Sortear juego', callback_data='sorteajuegos')]
        ])
    )

    return MAIN

def echo(update: Update, context: CallbackContext) -> None:    
    update.message.reply_text(update.message.text)


def sortea(update: Update, context: CallbackContext) -> None:    
    context.bot.send_message(chat_id=update.effective_chat.id,text=obtiene_lista_usuarios_des())

def obtiene_lista_usuarios_des() -> str:
    """genera una lista desordenada"""    
    users_list = ['juane','juank','matias','mauro','cristian']
    
    shuffle(users_list)  
    users_list = [ '{0}. {1}'.format(i+1,users_list[i]) for i in range(len(users_list))]  
    users_string = "\n".join(users_list)

    return users_string

def lista_usuarios_callback_handler (update: Update, context: CallbackContext) -> int:
    
    query = update.callback_query
    query.answer()
    prefijo = query.data
    buttons = []
    for user in users_bgg:
        buttons.append([InlineKeyboardButton(text=f'{user}', callback_data=f'{prefijo}_{user}')])

    # muestro un boton para elegir todos los usuarios
    if prefijo == 'sorteajuegos':
        buttons.append([InlineKeyboardButton(text=f'Todos', callback_data=f'{prefijo}_*')])

    reply_markup = InlineKeyboardMarkup(buttons)

    query.edit_message_text(            
        text=f'Seleccione un usuario:'
    )

    query.edit_message_reply_markup(            
        reply_markup=reply_markup
    )

    return SELECT_USER

def lista_coleccion_callback_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    
    user = query.data.split('_')[1]
    
    game_list = bgg.obtiene_coleccion_por_usuario(user)

    text = f'Juegos de {user}:\n\n'    
    for game in game_list:
        text += '[{name}]({url_game})\n'.format(name=game['name'],url_game=game['url_game'])

    query.edit_message_text(            
        text=text,
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

    return ConversationHandler.END

def sortea_juego_callback_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    user = query.data.split('_')[1]

    # si selecciona Todos        
    if user == '*':        
        user = users_bgg[randint(0,len(users_bgg))]

    # busca los juegos de bgg
    game_list = bgg.obtiene_coleccion_por_usuario(user)

    # elige juego random
    shuffle(game_list)
    game = game_list[randint(0,len(game_list)-1)]    

    # edita el mensaje anterior
    query.edit_message_text(            
        text='*y el ganador es...*',
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

    # contesta con imagen
    caption =  "*{name}*\n{owner}".format(name=game['name'],owner=game['owner'])   
    context.bot.sendPhoto(chat_id=update.effective_chat.id, photo = game['thumbnail'] , caption=caption, parse_mode="Markdown")

    return ConversationHandler.END

def sortea_callback_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    query.edit_message_text(            
        text=obtiene_lista_usuarios_des(),
        parse_mode='Markdown'
    )

    return ConversationHandler.END

def main() -> None:
    """Start the bot."""

    # Create the Updater and pass it your bot's token.        
    #token = os.environ['TOKEN']
    token = os.getenv('TOKEN')
    print (token)
    updater = Updater( token )

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    #dispatcher.add_handler(CommandHandler("start", start))    
    dispatcher.add_handler(CommandHandler("sortea", sortea))
 

    dispatcher.add_handler(ConversationHandler(
        entry_points=[
            CommandHandler('start', start)
        ],

        states={
            MAIN:[                
                CallbackQueryHandler(pattern='^sorteajugador$', callback=sortea_callback_handler),
                CallbackQueryHandler(pattern='^listajuegos$', callback=lista_usuarios_callback_handler),
                CallbackQueryHandler(pattern='^sorteajuegos$', callback=lista_usuarios_callback_handler)
            ],
            SELECT_USER:[
                CallbackQueryHandler(pattern='listajuegos_', callback=lista_coleccion_callback_handler),
                CallbackQueryHandler(pattern='sorteajuegos_', callback=sortea_juego_callback_handler)
            ]
        },

        fallbacks=[]
        )
    )

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