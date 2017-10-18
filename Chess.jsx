// Chess.jsx

var RepopulateGameDropdown = function() {
    $.getJSON( 'game_list', {}, function( json_data ) {
        if( json_data.error ) {
            alert( json_data.error );
        } else {
            game_dropdown.setState( { game_list: json_data.game_list } );
            // Does setState(...) return after rendering is complete?
            // If not, this doesn't really make sense.
            RefreshGame();
        }
    } );
}

var OnNewButtonClicked = function() {
    var game_name = prompt( 'Please enter a name for your new game.', '' );
    if( game_name ) {
        $.getJSON( 'new_game', { 'game_name' : game_name }, function( json_data ) {
            if( json_data.error ) {
                alert( json_data.error );
            } else {
                RepopulateGameDropdown();
            }
        } );
    }
}

var OnDeleteButtonClicked = function() {
    var game_dropdown = document.getElementById( 'game' );
    var game_name = game_dropdown.options[ game_dropdown.selectedIndex ].text;
    $.getJSON( 'delete_game', { 'game_name' : game_name }, function( json_data ) {
        if( json_data.error ) {
            alert( json_data.error );
        } else {
            RepopulateGameDropdown();
        }
    } );
}

var RefreshGame = function() {
    var game_dropdown = document.getElementById( 'game' );
    var game_name = game_dropdown.options[ game_dropdown.selectedIndex ].text;
    $.getJSON( 'game_state', { 'game_name' : game_name }, function( json_data ) {
        if( json_data.error ) {
            alert( json_data.error );
        } else {
            chess_board.setState( json_data.game_state );
        }
    } );
}

var OnRefreshButtonClicked = function() {
    RefreshGame();
}

var OnPlayerDropdownChanged = function() {
    var player_dropdown = document.getElementById( 'player_dropdown' );
    var playing_as = parseInt( player_dropdown.options[ player_dropdown.selectedIndex ].value );
    chess_board.setState( { playing_as: playing_as } );
}

class GameDropdown extends React.Component {
    constructor( props ) {
        super( props );
        this.state = {
            game_list: []
        }
        RepopulateGameDropdown();
    }

    OnGameSelectChanged() {
        RefreshGame();
    }

    render() {
        var option_list = [];
        for( var i = 0; i < this.state.game_list.length; i++ ) {
            var game_name = this.state.game_list[i];
            var option = <option value="{game_name}">{game_name}</option>;
            option_list.push( option );
        }
        return React.createElement( 'select', { id: 'game', onChange: this.OnGameSelectChanged }, ...option_list );
    }
}

class ChessBoardTile extends React.Component {
    constructor( props ) {
        super( props );
    }

    render() {
        var parity = ( this.props.row + this.props.col ) % 2;
        var style = {
            gridRow: this.props.flip ? ( 9 - this.props.row ) : this.props.row,
            gridColumn: this.props.col
        };
        var tileClass = 'tile ';
        if( parity === 0 ) {
            tileClass += 'white_tile';
        } else {
            tileClass += 'black_tile';
        }
        var i = this.props.row - 1;
        var j = this.props.col - 1;
        var id = i.toString() + '_' + j.toString();
        var tile_occupants = [];
        var occupant = this.props.matrix[i][j];
        if( occupant !== 0 ) {
            var occupant_image = this.getOccupantImage( occupant );
            var occupant_div = <img draggable={true} className="occupant" src={'images/' + occupant_image + '.png'} width={100} height={100}></img>;
            tile_occupants.push( occupant_div );
        }
        return React.createElement( 'div', { id: id, style: style, className: tileClass }, ...tile_occupants );
    }

    getOccupantImage( occupant ) {
        var imageMap = [
            undefined,
            'white_pawn',
            'white_rook',
            'white_knight',
            'white_bishop',
            'white_queen',
            'white_king',
            'black_pawn',
            'black_rook',
            'black_knight',
            'black_bishop',
            'black_queen',
            'black_king'
        ];
        return imageMap[ occupant ];
    }
}

class ChessBoard extends React.Component {
    constructor( props ) {
        super( props );
        this.state = {
            matrix: [
                [ 0, 0, 0, 0, 0, 0, 0, 0 ],
                [ 0, 0, 0, 0, 0, 0, 0, 0 ],
                [ 0, 0, 0, 0, 0, 0, 0, 0 ],
                [ 0, 0, 0, 0, 0, 0, 0, 0 ],
                [ 0, 0, 0, 0, 0, 0, 0, 0 ],
                [ 0, 0, 0, 0, 0, 0, 0, 0 ],
                [ 0, 0, 0, 0, 0, 0, 0, 0 ],
                [ 0, 0, 0, 0, 0, 0, 0, 0 ]
            ],
            whose_turn: undefined,
            playing_as: 0
        }
    }

    render() {
        var flip = false;
        if( this.state.playing_as === 2 /* both */ ) {
            if( this.state.whose_turn === 1 /* black */ ) {
                flip = true;
            }
        } else {
            if( this.state.playing_as === 1 /* black */ ) {
                flip = true;
            }
        }
        var tile_array = [];
        for( var row = 1; row <= 8; row++ ) {
            for( var col = 1; col <= 8; col++ ) {
                var tile = <ChessBoardTile row={row} col={col} matrix={this.state.matrix} flip={flip}/>;
                tile_array.push( tile );
            }
        }
        var style = { border: '5px solid black' };
        var chess_board_div = React.createElement( 'div', { id: 'chess_board', style: style }, ...tile_array );
        var whose_turn = '';
        if( this.state.whose_turn !== undefined ) {
            whose_turn = 'It is ' + ( this.state.whose_turn === 0 ? 'white' : 'black' ) + "'s turn.";
            if( this.state.playing_as === this.state.whose_turn ) {
                whose_turn += '  It is your turn.';
            } else if( this.state.playing_as === 2 /* both */ ) {
                whose_turn += '  Your are both white and black.  Take the turn.';
            } else {
                whose_turn += '  It is not yet your turn.';
            }
        } else {
            whose_turn = "It is no one's turn yet.";
        }
        style = { width: '800px' };
        var whose_turn_div = <center><p style={style}>{whose_turn}</p></center>;
        return React.createElement( 'div', null, whose_turn_div, chess_board_div );
    }
}

var chess_board = ReactDOM.render( <ChessBoard/>, document.getElementById( 'chess_board' ) );
var game_dropdown = ReactDOM.render( <GameDropdown/>, document.getElementById( 'game_dropdown_span' ) );