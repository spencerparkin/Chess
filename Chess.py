# Chess.py

import os
import cherrypy
import pymongo
import time

class ChessGame( object ):
    EMPTY = 0
    WHITE_PAWN = 1
    WHITE_ROOK = 2
    WHITE_KNIGHT = 3
    WHITE_BISHOP = 4
    WHITE_QUEEN = 5
    WHITE_KING = 6
    BLACK_PAWN = 7
    BLACK_ROOK = 8
    BLACK_KNIGHT = 9
    BLACK_BISHOP = 10
    BLACK_QUEEN = 11
    BLACK_KING = 12
    WHITE_PLAYER = 0
    BLACK_PLAYER = 1

    def __init__( self ):
        self.matrix = [
            [ self.BLACK_ROOK, self.BLACK_KNIGHT, self.BLACK_BISHOP, self.BLACK_QUEEN, self.BLACK_KING, self.BLACK_BISHOP, self.BLACK_KNIGHT, self.BLACK_ROOK ],
            [ self.BLACK_PAWN, self.BLACK_PAWN, self.BLACK_PAWN, self.BLACK_PAWN, self.BLACK_PAWN, self.BLACK_PAWN, self.BLACK_PAWN, self.BLACK_PAWN ],
            [ self.EMPTY, self.EMPTY, self.EMPTY, self.EMPTY, self.EMPTY, self.EMPTY, self.EMPTY, self.EMPTY ],
            [ self.EMPTY, self.EMPTY, self.EMPTY, self.EMPTY, self.EMPTY, self.EMPTY, self.EMPTY, self.EMPTY ],
            [ self.EMPTY, self.EMPTY, self.EMPTY, self.EMPTY, self.EMPTY, self.EMPTY, self.EMPTY, self.EMPTY ],
            [ self.EMPTY, self.EMPTY, self.EMPTY, self.EMPTY, self.EMPTY, self.EMPTY, self.EMPTY, self.EMPTY ],
            [ self.WHITE_PAWN, self.WHITE_PAWN, self.WHITE_PAWN, self.WHITE_PAWN, self.WHITE_PAWN, self.WHITE_PAWN, self.WHITE_PAWN, self.WHITE_PAWN ],
            [ self.WHITE_ROOK, self.WHITE_KNIGHT, self.WHITE_BISHOP, self.WHITE_KING, self.WHITE_QUEEN, self.WHITE_BISHOP, self.WHITE_KNIGHT, self.WHITE_ROOK ]
        ]
        self.whose_turn = self.WHITE_PLAYER;
        self.move_count = 0

    def Serialize( self ):
        data = {
            'matrix' : self.matrix,
            'whose_turn' : self.whose_turn
        }
        return data

    def Deserialize( self, data ):
        self.matrix = data[ 'matrix' ]
        self.whose_turn = data[ 'whose_turn' ]

    def ValidMove( self, move ):
        pass

    def MakeMove( self, move ):
        pass

class ChessApp( object ):
    def __init__( self, root_dir ):
        self.root_dir = root_dir
        try:
            database_uri = 'mongodb://heroku_8m3rxx28:jdsoru7vb5dq6m3q5c4klcu0ba@ds121665.mlab.com:21665/heroku_8m3rxx28'
            self.mongo_client = pymongo.MongoClient( database_uri )
            self.database = self.mongo_client[ 'heroku_8m3rxx28' ]
            collection_names = self.database.collection_names()
            if not 'game_collection' in collection_names:
                self.database.create_collection( 'game_collection' )
            self.game_collection = self.database[ 'game_collection' ]
        except:
            self.mongo_client = None

    @cherrypy.expose
    def default( self, **kwargs ):
        cherrypy.response.headers['Content-Type'] = 'text/html'
        cherrypy.response.headers['cache-control'] = 'no-store'
        return cherrypy.lib.static.serve_file( root_dir + '/Chess.html', content_type='text/html' )

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def new_game( self, **kwargs ):
        game_name = kwargs[ 'game_name' ]
        game_doc = self.game_collection.find_one( { 'game_name' : game_name } )
        if game_doc:
            return { 'error' : 'A game by the name "%s" already exists.' % game_name }
        game_data = ChessGame().Serialize()
        game_doc = {
            'game_name' : game_name,
            'game_data' : game_data
        }
        result = self.game_collection.insert_one( game_doc )
        return {}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def delete_game( self, **kwargs ):
        game_name = kwargs[ 'game_name' ]
        game_doc = self.game_collection.find_one( { 'game_name': game_name } )
        if not game_doc:
            return { 'error' : 'A game by the name "%s" could not be found.' % game_name }
        result = self.game_collection.delete_one( { 'game_name' : game_name } )
        return {}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def game_list( self, **kwargs ):
        cursor = self.game_collection.find( {} )
        game_list = [ game_doc[ 'game_name' ] for game_doc in cursor ]
        return { 'game_list' : game_list }

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def game_state( self, **kwargs ):
        game_name = kwargs[ 'game_name' ]
        game_doc = self.game_collection.find_one( { 'game_name': game_name } )
        if not game_doc:
            return { 'error' : 'A game by the name "%s" could not be found.' % game_name }
        return { 'game_state': game_doc[ 'game_data' ] }

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def make_move( self, **kwargs ):
        game_name = kwargs[ 'game_name' ]
        game_doc = self.game_collection.find_one( { 'game_name': game_name } )
        if not game_doc:
            return { 'error': 'A game by the name "%s" could not be found.' % game_name }
        game = ChessGame()
        game.Deserialize( game_doc[ 'game_data'] )
        try:
            pass # TODO: Make the move on the game object, reserialize it, then upload it to the database.
        except Exception as ex:
            return { 'error' : str(ex) }
        return {}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def all_valid_moves( self, **kwargs ):
        pass # TODO: Return all valid moves for the given piece.

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def wait_for_turn( self, **kwargs ):
        try:
            game_name = kwargs[ 'game_name' ]
            turn = kwargs[ 'turn' ]
            for i in range( 1000 ):
                game_doc = self.game_collection.find_one( { 'game_name' : game_name } )
                game = ChessGame()
                game.Deserialize( game_doc )
                if game.whose_turn != turn:
                    time.sleep(0.5)
                else:
                    return {}
            else:
                raise Exception( 'timeout' )
        except Exception as ex:
            return { 'error' : str(ex) }

if __name__ == '__main__':
    root_dir = os.path.dirname( os.path.abspath( __file__ ) )
    port = int( os.environ.get( 'PORT', 5100 ) )

    app = ChessApp( root_dir )

    app_config = {
        'global': {
            'server.socket_host': '0.0.0.0',
            'server.socket_port': port,
        },
        '/': {
            'tools.staticdir.root': root_dir,
            'tools.staticdir.on': True,
            'tools.staticdir.dir': '',
        },
    }

    cherrypy.quickstart( app, '/', config = app_config )