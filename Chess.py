# Chess.py

import os
import cherrypy
import pymongo
import json
import copy

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
            [ self.WHITE_ROOK, self.WHITE_KNIGHT, self.WHITE_BISHOP, self.WHITE_QUEEN, self.WHITE_KING, self.WHITE_BISHOP, self.WHITE_KNIGHT, self.WHITE_ROOK ]
        ]
        self.whose_turn = self.WHITE_PLAYER;
        self.move_count = 0
        self.move_history = [] # TODO: How history in page.  Offer undo/redo?  That shouldn't be hard.

    def Serialize( self ):
        data = {
            'matrix' : self.matrix,
            'whose_turn' : self.whose_turn,
            'move_history' : self.move_history
        }
        return data

    def Deserialize( self, data ):
        self.matrix = data[ 'matrix' ]
        self.whose_turn = data[ 'whose_turn' ]
        self.move_history = data[ 'move_history' ]

    def ColorOfOccupant( self, occupant ):
        if occupant >= 1 and occupant <= 6:
            return self.WHITE_PLAYER
        elif occupant >= 7 and occupant <= 12:
            return self.BLACK_PLAYER
        return None

    def ValidMove( self, move, whose_turn = None ):
        if whose_turn is None:
            whose_turn = self.whose_turn
        move_source = move[ 'source' ]
        move_target = move[ 'target' ]
        # Notice that here we're also making sure that the coordinates are in bound by trying to use them on the matrix.
        source_occupant = self.matrix[ move_source[0] ][ move_source[1] ]
        target_occupant = self.matrix[ move_target[0] ][ move_target[1] ]
        if move_source[0] == move_target[0] and move_source[1] == move_target[1]:
            raise Exception( 'Zero-length moves not allowed.' )
        if source_occupant == self.EMPTY:
            raise Exception( 'No piece to move.' )
        source_color = self.ColorOfOccupant( source_occupant )
        if source_color != whose_turn:
            raise Exception( 'Piece cannot be moved on this turn.' )
        target_color = self.ColorOfOccupant( target_occupant )
        castling = False
        if target_color is not None and target_color == source_color:
            if source_occupant == self.WHITE_KING and target_occupant == self.WHITE_ROOK:
                castling = True
            elif source_occupant == self.BLACK_KING and target_occupant == self.BLACK_ROOK:
                castling = True
            else:
                raise Exception( 'Piece cannot capture one of its own kind.' )
        row_diff = move_target[0] - move_source[0]
        col_diff = move_target[1] - move_source[1]
        if source_occupant == self.WHITE_KING or source_occupant == self.BLACK_KING:
            if abs( row_diff ) > 1 or abs( col_diff ) > 1 and not castling:
                raise Exception( 'The king cannot move that far.' )
        elif source_occupant == self.WHITE_QUEEN or source_occupant == self.BLACK_QUEEN:
            if abs( row_diff ) != 0 and abs( col_diff ) != 0 and abs( row_diff ) != abs( col_diff ):
                raise Exception( 'The queen can only move on diagonals or orthogonals.' )
        elif source_occupant == self.WHITE_BISHOP or source_occupant == self.BLACK_BISHOP:
            if abs( row_diff ) != abs( col_diff ):
                raise Exception( 'Bishops can only move on diagonals.' )
        elif source_occupant == self.WHITE_ROOK or source_occupant == self.BLACK_ROOK:
            if abs( row_diff ) != 0 and abs( col_diff ) != 0:
                raise Exception( 'Rooks can only move on orthogonals.' )
        elif source_occupant == self.WHITE_KNIGHT or source_occupant == self.BLACK_KNIGHT:
            if not( ( abs( row_diff ) == 1 and abs( col_diff ) == 2 ) or ( abs( row_diff ) == 2 and abs( col_diff ) == 1 ) ):
                raise Exception( 'Knights can only move on an L-shape.' )
        elif source_occupant == self.WHITE_PAWN or source_occupant == self.BLACK_PAWN:
            sign = -1 if source_occupant == self.WHITE_PAWN else 1
            first_file = 6 if source_occupant == self.WHITE_PAWN else 1
            if ( row_diff == 1 * sign or row_diff == 2 * sign ) and col_diff == 0 and target_color is not None:
                raise Exception( 'Pawns can only attack on diagonals.' )
            if row_diff == 2 * sign and col_diff == 0:
                if move_source[0] != first_file:
                    raise Exception( 'A pawn can only move 2 tiles from the first file.' )
            elif row_diff == 1 * sign and col_diff == 0:
                pass
            elif row_diff == 1 * sign and abs( col_diff ) == 1:
                if target_color == None:
                    raise Exception( 'A pawn can only move diagonally if it is going to attack.' )
            else:
                raise Exception( 'Pawns can only move orthogonally one tile if advancing, or diagonally one tile if attacking.  In any case, pawns must always move toward the enemy\'s side.' )
        if source_occupant != self.WHITE_KNIGHT and source_occupant != self.BLACK_KNIGHT:
            move_intermediate = copy.copy( move_source )
            row_delta = 1 if row_diff > 0 else ( -1 if row_diff < 0 else 0 )
            col_delta = 1 if col_diff > 0 else ( -1 if col_diff < 0 else 0 )
            move_intermediate[0] += row_delta
            move_intermediate[1] += col_delta
            while move_intermediate != move_target:
                if self.matrix[ move_intermediate[0] ][ move_intermediate[1] ] != self.EMPTY:
                    raise Exception( 'No piece, except for knights, can jump over other pieces.' )
                move_intermediate[0] += row_delta
                move_intermediate[1] += col_delta
        if castling:
            if source_occupant == self.WHITE_KING and target_occupant == self.WHITE_ROOK:
                for prev_move in self.move_history:
                    if prev_move[ 'move' ][ 'source' ][0] == 7 and prev_move[ 'move' ][ 'source' ][1] == 4:
                        raise Exception( 'A king can only castle if it has never before moved.' )
                    # TODO: The rook involved must not have previously moved.
                # TODO: The king cannot be in check, nor can castling put it in check.
            elif source_occupant == self.BLACK_KING and target_occupant == self.BLACK_ROOK:
                for prev_move in self.move_history:
                    if prev_move[ 'move' ][ 'source' ][0] == 0 and prev_move[ 'move' ][ 'source' ][1] == 4:
                        raise Exception( 'A king can only castle if it has never before moved.' )
                    # TODO: The rook involved must not have previously moved.
                # TODO: The king cannot be in check, nor can castling put it in check.
        return castling

    def MakeMove( self, move ):
        castling = self.ValidMove( move )
        move_source = move[ 'source' ]
        move_target = move[ 'target' ]
        capture = self.EMPTY
        if not castling:
            occupant = self.matrix[ move_source[0] ][ move_source[1] ]
            if occupant == self.WHITE_PAWN and move_target[0] == 0:
                occupant = self.WHITE_QUEEN # TODO: They should actually get to choose between this and other pieces.
            elif occupant == self.BLACK_PAWN and move_target[0] == 7:
                occupant = self.BLACK_QUEEN # TODO: Again, they should actually get to choose here.
            capture = self.matrix[ move_target[0] ][ move_target[1] ]
            self.matrix[ move_target[0] ][ move_target[1] ] = occupant
            self.matrix[ move_source[0] ][ move_source[1] ] = self.EMPTY
        else:
            self.matrix[ move_source[0] ][ move_source[1] ] = self.EMPTY
            self.matrix[ move_target[0] ][ move_target[1] ] = self.EMPTY
            if move_source[0] == 7:
                if move_target[1] == 7: # White king castles right side.
                    self.matrix[7][6] = self.WHITE_KING
                    self.matrix[7][5] = self.WHITE_ROOK
                elif move_target[1] == 0: # White king castles left side.
                    self.matrix[7][2] = self.WHITE_KING
                    self.matrix[7][3] = self.WHITE_ROOK
            elif move_source[0] == 0:
                if move_target[1] == 7: # Black king castles right side.
                    self.matrix[0][6] = self.WHITE_KING
                    self.matrix[0][5] = self.WHITE_ROOK
                elif move_target[1] == 0: # Black king castles left side.
                    self.matrix[0][2] = self.WHITE_KING
                    self.matrix[0][3] = self.WHITE_ROOK
        self.whose_turn = self.WHITE_PLAYER if self.whose_turn == self.BLACK_PLAYER else self.BLACK_PLAYER
        self.move_history.append( { 'move' : move, 'capture' : capture } )

    def EveryTileLocation( self ):
        for i in range( 0, 8 ):
            for j in range( 0, 8 ):
                yield [ i, j ]

    def GenerateValidMoveList( self, source_loc ):
        valid_move_list = []
        for target_loc in self.EveryTileLocation():
            move = { 'source' : source_loc, 'target' : target_loc }
            try:
                self.ValidMove( move )
                valid_move_list.append( move )
            except:
                pass
        return valid_move_list

    def GenerateKillMoveList( self, source_loc ):
        valid_move_list = self.GenerateValidMoveList( source_loc )
        kill_move_list = [ move for move in valid_move_list if self.matrix[ move[ 'target' ][0] ][ move[ 'target' ][1] ] != self.EMPTY ]
        return kill_move_list

    def ThreatListToLocation( self, target_loc, whose_turn ):
        threat_list = []
        for source_loc in self.EveryTileLocation():
            move = { 'source' : source_loc, 'target' : target_loc }
            try:
                self.ValidMove( move, whose_turn )
                threat_list.append( source_loc )
            except:
                pass
        return threat_list

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
    def whose_turn( self, **kwargs ):
        game_name = kwargs[ 'game_name' ]
        game_doc = self.game_collection.find_one( { 'game_name' : game_name } )
        if game_doc:
            return { 'whose_turn' : game_doc[ 'game_data' ][ 'whose_turn' ] }
        return {}

    def GetGameFromPayload( self ):
        content_length = cherrypy.request.headers[ 'Content-Length' ]
        payload = cherrypy.request.body.read( int( content_length ) )
        payload = payload.decode( 'utf-8' )
        payload = json.loads( payload )
        game_name = payload[ 'game_name' ]
        game_doc = self.game_collection.find_one( { 'game_name': game_name } )
        if not game_doc:
            raise Exception( 'A game by the name "%s" could not be found.' % game_name )
        game = ChessGame()
        game.Deserialize( game_doc['game_data'] )
        return game, payload

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def make_move( self, **kwargs ):
        try:
            game, payload = self.GetGameFromPayload()
            if game.whose_turn != payload[ 'playing_as' ] and payload[ 'playing_as' ] != 2: # 2 -> Playing as both black and white.
                raise Exception( 'It is not yet your turn.' )
            move = payload[ 'move' ]
            game.MakeMove( move )
            game_data = game.Serialize()
            result = self.game_collection.update_one( { 'game_name': payload[ 'game_name' ] }, { '$set' : { 'game_data' : game_data } } )
            result = None
        except Exception as ex:
            return { 'error' : str(ex) }
        return {}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def all_valid_moves( self, **kwargs ):
        try:
            game, payload = self.GetGameFromPayload()
            valid_move_list = game.GenerateValidMoveList( payload[ 'location' ] )
            return { 'valid_move_list': valid_move_list }
        except Exception as ex:
            return { 'error': str(ex) }

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def all_kill_moves( self, **kwargs ):
        try:
            game, payload = self.GetGameFromPayload()
            kill_move_list = game.GenerateKillMoveList( payload[ 'location' ] )
            return { 'kill_move_list': kill_move_list }
        except Exception as ex:
            return { 'error': str(ex) }

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