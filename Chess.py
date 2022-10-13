# Chess.py

import os
import cherrypy
import pymongo
import json
import copy
import random
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
            [ self.WHITE_ROOK, self.WHITE_KNIGHT, self.WHITE_BISHOP, self.WHITE_QUEEN, self.WHITE_KING, self.WHITE_BISHOP, self.WHITE_KNIGHT, self.WHITE_ROOK ]
        ]
        self.whose_turn = self.WHITE_PLAYER;
        self.move_count = 0
        self.move_history = []
        self.move_history_location = 0

    def Serialize( self ):
        data = {
            'matrix' : self.matrix,
            'whose_turn' : self.whose_turn,
            'move_history' : self.move_history,
            'move_history_location' : self.move_history_location
        }
        return data

    def Deserialize( self, data ):
        self.matrix = data[ 'matrix' ]
        self.whose_turn = data[ 'whose_turn' ]
        self.move_history = data[ 'move_history' ]
        self.move_history_location = data[ 'move_history_location' ]

    def ColorOfOccupant( self, occupant ):
        if occupant >= 1 and occupant <= 6:
            return self.WHITE_PLAYER
        elif occupant >= 7 and occupant <= 12:
            return self.BLACK_PLAYER
        return None

    def ValidMove( self, move, whose_turn = None ):
        # TODO: Ugh...En passant?!  How are we going to implement this move?
        # TODO: Another rule not observed here is that of stale-mate.  And perhaps more generally,
        #       the king is not allowed to move into a position where it would be in check, I think.
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
            if not castling:
                if abs( row_diff ) > 1 or abs( col_diff ) > 1:
                    raise Exception( 'The king cannot move that far.' )
                # Ugh...is this going to infinitely recurse in some cases?  E.g., two kings right next to each other?
                threat_list = self.ThreatListToLocation( move_target, self.WHITE_PLAYER if whose_turn == self.BLACK_PLAYER else self.WHITE_PLAYER )
                if len( threat_list ) > 0:
                    raise Exception( 'The king cannot put itself in check.' )
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
            first_rank = 6 if source_occupant == self.WHITE_PAWN else 1
            if ( row_diff == 1 * sign or row_diff == 2 * sign ) and col_diff == 0 and target_color is not None:
                raise Exception( 'Pawns can only attack on diagonals.' )
            if row_diff == 2 * sign and col_diff == 0:
                if move_source[0] != first_rank:
                    raise Exception( 'A pawn can only move 2 tiles from the first rank.' )
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
                for i in range( 0, self.move_history_location ):
                    prev_move = self.move_history[i]
                    if prev_move[ 'move' ][ 'source' ][0] == 7 and prev_move[ 'move' ][ 'source' ][1] == 4:
                        raise Exception( 'A king can only castle if it has never before moved.' )
                    # TODO: The rook involved must not have previously moved.
                # TODO: The king cannot be in check, nor can castling put it in check.
            elif source_occupant == self.BLACK_KING and target_occupant == self.BLACK_ROOK:
                for i in range( 0, self.move_history_location ):
                    prev_move = self.move_history[i]
                    if prev_move[ 'move' ][ 'source' ][0] == 0 and prev_move[ 'move' ][ 'source' ][1] == 4:
                        raise Exception( 'A king can only castle if it has never before moved.' )
                    # TODO: The rook involved must not have previously moved.
                # TODO: The king cannot be in check, nor can castling put it in check.
        return castling

    def MakeMove( self, move, manage_history = True ):
        castling = self.ValidMove( move )
        promotion = False
        move_source = move[ 'source' ]
        move_target = move[ 'target' ]
        capture = self.EMPTY
        if not castling:
            occupant = self.matrix[ move_source[0] ][ move_source[1] ]
            if occupant == self.WHITE_PAWN and move_target[0] == 0:
                occupant = self.WHITE_QUEEN # TODO: They should actually get to choose between this and other pieces.
                promotion = True
            elif occupant == self.BLACK_PAWN and move_target[0] == 7:
                occupant = self.BLACK_QUEEN # TODO: Again, they should actually get to choose here.
                promotion = True
            capture = self.matrix[ move_target[0] ][ move_target[1] ]
            self.matrix[ move_target[0] ][ move_target[1] ] = occupant
            self.matrix[ move_source[0] ][ move_source[1] ] = self.EMPTY
        else:
            self.matrix[ move_source[0] ][ move_source[1] ] = self.EMPTY
            self.matrix[ move_target[0] ][ move_target[1] ] = self.EMPTY
            if move_source[0] == 7:
                occupant = self.WHITE_KING
                capture = self.WHITE_ROOK
                if move_target[1] == 7: # White king castles right side.
                    self.matrix[7][6] = self.WHITE_KING
                    self.matrix[7][5] = self.WHITE_ROOK
                elif move_target[1] == 0: # White king castles left side.
                    self.matrix[7][2] = self.WHITE_KING
                    self.matrix[7][3] = self.WHITE_ROOK
            elif move_source[0] == 0:
                occupant = self.BLACK_KING
                capture = self.BLACK_ROOK
                if move_target[1] == 7: # Black king castles right side.
                    self.matrix[0][6] = self.BLACK_KING
                    self.matrix[0][5] = self.BLACK_ROOK
                elif move_target[1] == 0: # Black king castles left side.
                    self.matrix[0][2] = self.BLACK_KING
                    self.matrix[0][3] = self.BLACK_ROOK
        self.whose_turn = self.WHITE_PLAYER if self.whose_turn == self.BLACK_PLAYER else self.BLACK_PLAYER
        if manage_history:
            while self.move_history_location < len( self.move_history ):
                del self.move_history[ self.move_history_location ]
            self.move_history.append( { 'move' : move, 'capture' : capture, 'actor' : occupant, 'castling' : castling, 'promotion' : promotion } )
            self.move_history_location += 1

    def UnmakeMove( self, move_data ):
        move = move_data[ 'move' ]
        move_source = move[ 'source' ]
        move_target = move[ 'target' ]
        if not move_data[ 'castling' ]:
            if not move_data[ 'promotion' ]:
                self.matrix[ move_source[0] ][ move_source[1] ] = self.matrix[ move_target[0] ][ move_target[1] ]
            else:
                color = self.ColorOfOccupant( self.matrix[ move_target[0] ][ move_target[1] ] )
                if color == self.WHITE_PLAYER:
                    self.matrix[ move_source[0] ][ move_source[1] ] = self.WHITE_PAWN
                elif color == self.BLACK_PLAYER:
                    self.matrix[ move_source[0] ][ move_source[1] ] = self.BLACK_PAWN
            if move_data[ 'capture' ]:
                self.matrix[ move_target[0] ][ move_target[1] ] = move_data[ 'capture' ]
            else:
                self.matrix[ move_target[0] ][ move_target[1] ] = self.EMPTY
            color = self.ColorOfOccupant( move_data[ 'actor' ] )
            self.whose_turn = self.WHITE_PLAYER if color == self.WHITE_PLAYER else self.BLACK_PLAYER
        else:
            if move_source[0] == 7:
                self.whose_turn = self.WHITE_PLAYER
                if move_target[1] == 7: # White king castles right side.
                    self.matrix[7][6] = self.EMPTY
                    self.matrix[7][5] = self.EMPTY
                elif move_target[1] == 7: # White king castled left side.
                    self.matrix[7][2] = self.EMPTY
                    self.matrix[7][3] = self.EMPTY
            elif move_source[0] == 0:
                self.whose_turn = self.BLACK_PLAYER
                if move_target[1] == 7: # Black king castled right side.
                    self.matrix[0][6] = self.EMPTY
                    self.matrix[0][5] = self.EMPTY
                elif move_target[1] == 0: # Black king castled left side.
                    self.matrix[0][2] = self.BLACK_KING
                    self.matrix[0][3] = self.BLACK_ROOK
            self.matrix[ move_source[0] ][ move_source[1] ] = move_data[ 'actor' ]
            self.matrix[ move_target[0] ][ move_target[1] ] = move_data[ 'capture' ]

    def ChangeBoardPosition( self, location ):
        while self.move_history_location != location:
            if self.move_history_location < location:
                self.MakeMove( self.move_history[ self.move_history_location ][ 'move' ], False )
                self.move_history_location += 1
            elif self.move_history_location > location:
                self.move_history_location -= 1
                self.UnmakeMove( self.move_history[ self.move_history_location ] )

    def EveryTileLocation( self ):
        for i in range( 0, 8 ):
            for j in range( 0, 8 ):
                try:
                    yield [ i, j ]
                except GeneratorExit:
                    return

    def GenerateValidMovesForLocation( self, source_loc ):
        for target_loc in self.EveryTileLocation():
            move = { 'source' : source_loc, 'target' : target_loc }
            try:
                self.ValidMove( move )
                yield move
            except GeneratorExit:
                return
            except: # TODO: Really should catch specific "invalid move" exception here.
                pass

    def GenerateAllValidMoves( self ):
        for source_loc in self.EveryTileLocation():
            try:
                yield from self.GenerateValidMovesForLocation( source_loc )
            except GeneratorExit:
                return

    def GenerateKillMoveList( self, source_loc ):
        valid_move_list = [ move for move in self.GenerateValidMovesForLocation( source_loc ) ]
        kill_move_list = [ move for move in valid_move_list if self.matrix[ move[ 'target' ][0] ][ move[ 'target' ][1] ] != self.EMPTY ]
        return kill_move_list

    def ThreatListToLocation( self, target_loc, whose_turn ):
        threat_list = []
        for source_loc in self.EveryTileLocation():
            if self.ColorOfOccupant( self.matrix[ source_loc[0] ][ source_loc[1] ] ) == whose_turn:
                move = { 'source' : source_loc, 'target' : target_loc }
                try:
                    self.ValidMove( move, whose_turn )
                    threat_list.append( source_loc )
                except:
                    pass
        return threat_list

    def Metric( self ):
        # This metric is by Claude E. Shannon.
        # How good the position is for white is how positive a metric we get.
        # How good the position is for black is how negative a matrix we get.
        counts = [ 0 for i in range( 13 ) ]
        for location in self.EveryTileLocation():
            occupant = self.matrix[ location[0] ][ location[1] ]
            counts[ occupant ] += 1
        sum = 0.0
        sum += 200.0 * float( counts[ self.WHITE_KING ] - counts[ self.BLACK_KING ] )
        sum += 9.0 * float( counts[ self.WHITE_QUEEN ] - counts[ self.BLACK_QUEEN ] )
        sum += 3.0 * float( counts[ self.WHITE_BISHOP ] - counts[ self.BLACK_BISHOP ] )
        sum += 3.0 * float( counts[ self.WHITE_KNIGHT ] - counts[ self.BLACK_KNIGHT ] )
        sum += float( counts[ self.WHITE_PAWN ] - counts[ self.BLACK_PAWN ] )
        # TODO: sum -= 0.5 * ( D-D' + S-S' + I-I' ) # doubled, blocked & isolated pawns
        # This mobility part of the sum may make the difference between putting the player
        # in check versus putting the player in check-mate, because it is not legal for the
        # king to move into a position that puts it in check.  I've seen the computer pass
        # up an opportunity to put the player in check-mate.  I might also just look for
        # the check-mate condition here and then add a big score for that.
        # TODO: sum += 0.1 * ( M-M' ) + ... # mobility (the number of legal moves per piece?)
        return sum

# No real need for a common base.  We can use duck-typing, but I like a common base out of principle.
class Database(object):
    def __init__(self):
        pass

class MongoDatabase(Database):
    def __init__(self):
        self.mongo_client = None
        try:
            database_uri = 'mongodb://heroku_8m3rxx28:jdsoru7vb5dq6m3q5c4klcu0ba@ds121665.mlab.com:21665/heroku_8m3rxx28'
            self.mongo_client = pymongo.MongoClient(database_uri)
            self.database = self.mongo_client['heroku_8m3rxx28']
            collection_names = self.database.collection_names()
            if not 'game_collection' in collection_names:
                self.database.create_collection('game_collection')
            self.game_collection = self.database['game_collection']
        except:
            self.mongo_client = None

    def find_game(self, game_name):
        return self.game_collection.find_one({'game_name': game_name})

    def insert_game(self, game_name, game_data):
        game_doc = {
            'game_name' : game_name,
            'game_data' : game_data
        }
        self.game_collection.insert_one(game_doc)

    def delete_game(self, game_name):
        self.game_collection.delete_one({'game_name': game_name})

    def get_game_list(self):
        cursor = self.game_collection.find({})
        game_list = [game_doc['game_name'] for game_doc in cursor]
        return game_list

    def update_game(self, game_name, game_data):
        result = self.game_collection.update_one( { 'game_name': game_name }, { '$set' : { 'game_data' : game_data } } )
        result = None

class CacheDatabase(Database):
    def __init__(self):
        self.game_collection = {}

    def find_game(self, game_name):
        return self.game_collection[game_name] if game_name in self.game_collection else None

    def insert_game(self, game_name, game_data):
        self.game_collection[game_name] = game_data

    def delete_game(self, game_doc):
        if game_doc in self.game_collection:
            del self.game_colletion[game_doc]

    def get_game_list(self):
        return [game_name for game_name in self.game_collection]

    def udpate_game(self, game_name, game_data):
        self.game_collection[game_name] = game_data

class ChessApp( object ):
    def __init__( self, root_dir, mongo_backed ):
        self.root_dir = root_dir
        if mongo_backed:
            self.db = MongoDatabase()
        else:
            self.db = CacheDatabase()

    @cherrypy.expose
    def default( self, **kwargs ):
        cherrypy.response.headers['Content-Type'] = 'text/html'
        cherrypy.response.headers['cache-control'] = 'no-store'
        return cherrypy.lib.static.serve_file( root_dir + '/Chess.html', content_type='text/html' )

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def new_game( self, **kwargs ):
        game_name = kwargs[ 'game_name' ]
        game_doc = self.db.find_game(game_name)
        if game_doc:
            return { 'error' : 'A game by the name "%s" already exists.' % game_name }
        game_data = ChessGame().Serialize()
        self.db.insert_game(game_name, game_data)
        return {}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def delete_game( self, **kwargs ):
        game_name = kwargs[ 'game_name' ]
        game_doc = self.db.find_game(game_name)
        if not game_doc:
            return { 'error' : 'A game by the name "%s" could not be found.' % game_name }
        result = self.db.delete_game(game_name)
        return {}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def game_list( self, **kwargs ):
        game_list = self.db.get_game_list()
        return { 'game_list' : game_list }

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def game_state( self, **kwargs ):
        try:
            game_name = kwargs[ 'game_name' ]
            game_doc = self.db.find_game(game_name)
            if not game_doc:
                return { 'error' : 'A game by the name "%s" could not be found.' % game_name }
        except Exception as ex:
            return { 'error': str(ex) }
        return { 'game_state': game_doc[ 'game_data' ] }

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def whose_turn( self, **kwargs ):
        game_name = kwargs[ 'game_name' ]
        game_doc = self.db.find_game(game_name)
        if game_doc:
            return { 'whose_turn' : game_doc[ 'game_data' ][ 'whose_turn' ] }
        return {}

    def GetGameFromPayload( self ):
        content_length = cherrypy.request.headers[ 'Content-Length' ]
        payload = cherrypy.request.body.read( int( content_length ) )
        payload = payload.decode( 'utf-8' )
        payload = json.loads( payload )
        game_name = payload[ 'game_name' ]
        game_doc = self.db.find_game(game_name)
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
            game_name = payload['game_name']
            self.db.update_game(game_name, game_data)
        except Exception as ex:
            return { 'error' : str(ex) }
        return {}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def make_computer_move( self, **kwargs ):
        try:
            game_name = kwargs[ 'game_name' ]
            game_doc = self.db.find_game(game_name)
            game = ChessGame()
            game.Deserialize( game_doc[ 'game_data' ] )
            computer_player = ComputerPlayer()
            move = computer_player.DetermineReasonableMove( game )
            game.MakeMove( move )
            game_data = game.Serialize()
            self.db.update_game(game_name, game_data)
        except Exception as ex:
            return { 'error' : str(ex) }
        return {}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def all_valid_moves( self, **kwargs ):
        try:
            game, payload = self.GetGameFromPayload()
            valid_move_list = [ move for move in game.GenerateValidMovesForLocation( payload[ 'location' ] ) ]
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

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def change_board_location( self, **kwargs ):
        try:
            game, payload = self.GetGameFromPayload()
            game.ChangeBoardPosition( payload[ 'location' ] )
            game_data = game.Serialize()
            game_name = payload['game_name']
            self.db.update_game(game_name, game_data)
        except Exception as ex:
            return { 'error': str(ex) }
        return {}

class ComputerPlayer( object ):
    MINIMIZER = 0
    MAXIMIZER = 1

    def __init__( self ):
        pass

    # Here we implement the mini-max algorithm with what I think might be valid alpha-beta pruning.
    def DetermineReasonableMove( self, game ):
        seed = int( time.time() )
        random.seed( seed )
        try:
            move = self.CalculateReasonableMove( game )
        except Exception as ex:
            error = str(ex)
            error = None
        return move

    # TODO: Is alpha-beta pruning enough for us to go to max_depth of 4?  If not, we might have to use threads.
    #       Many situations not caught by depth 3 are handled by depth 4.  One of them is a possible check mate,
    #       as I'm sure is the case with many others.
    # TODO: I'm not sure if this re-write made the computer dumber or even dumber than that.
    #       First of all, if we remove the alpha-beta optimization (by commenting out the appropriate lines),
    #       is this a valid implementation of mini-max?  Second, is the algorithm still correct when we put
    #       the optimization back in?  One way to test this may be to run it twice: once with and once without
    #       the optimization code enabled.  Do we always get the same result?
    # TODO: Have option for choosing between depth 3 and depth 4?  (Easy vs. hard?)
    def CalculateReasonableMove( self, game, parent_bound = None, max_depth = 4, depth = 1 ):
        if depth == max_depth:
            return game.Metric()
        else:
            type = -1
            if game.whose_turn == ChessGame.WHITE_PLAYER:
                type = self.MAXIMIZER
            elif game.whose_turn == ChessGame.BLACK_PLAYER:
                type = self.MINIMIZER
            child_bound = None
            optimal_metric = 0
            if type == self.MAXIMIZER:
                optimal_metric = -999999
            elif type == self.MINIMIZER:
                optimal_metric = 999999
            if depth == 1:
                best_move_list = []
            for move in game.GenerateAllValidMoves():
                game_copy = copy.deepcopy( game )
                game_copy.MakeMove( move )
                metric = self.CalculateReasonableMove( game_copy, child_bound, max_depth, depth + 1 )
                if ( type == self.MAXIMIZER and metric > optimal_metric ) or ( type == self.MINIMIZER and metric < optimal_metric ):
                    optimal_metric = metric
                    child_bound = optimal_metric
                    if depth == 1:
                        best_move_list = [ move ]
                    if parent_bound is not None:
                        if ( type == self.MAXIMIZER and metric > parent_bound ) or ( type == self.MINIMIZER and metric < parent_bound ):
                            break # We have discovered that this branch is now not worth processing further!!
                elif depth == 1 and metric == optimal_metric:
                    best_move_list.append( move )
            if depth > 1:
                return optimal_metric
            i = random.randint( 0, len( best_move_list ) - 1 )
            return best_move_list[i]

if __name__ == '__main__':

    root_dir = os.path.dirname( os.path.abspath( __file__ ) )
    port = int( os.environ.get( 'PORT', 5100 ) )

    app = ChessApp( root_dir, False )

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