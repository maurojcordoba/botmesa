import requests, xmltodict

def obtiene_coleccion_por_usuario(user) -> list:
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