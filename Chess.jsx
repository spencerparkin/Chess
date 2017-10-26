// Chess.jsx

var GetGameName = function() {
    let game_dropdown = document.getElementById( 'game' );
    let game_name = undefined;
    if( game_dropdown.options.length > 0 ) {
        game_name = game_dropdown.options[ game_dropdown.selectedIndex ].text;
    }
    return game_name;
}

var RepopulateGameDropdown = function() {
    $.getJSON( 'game_list', {}, function( json_data ) {
        if( json_data.error ) {
            alert( json_data.error );
        } else {
            game_dropdown.setState( { game_list: json_data.game_list } );
            // Does setState(...) return after rendering is complete?
            // If not, this doesn't really make sense.  Instead of getting
            // the game name from the rendered drop-down, we should actually
            // be getting it from the state of the drop-down component.
            // This removes the race condition.
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
    var game_name = GetGameName();
    if( confirm( 'Delete game by the name "' + game_name + '"?' ) ) {
        $.getJSON( 'delete_game', { 'game_name' : game_name }, function( json_data ) {
            if( json_data.error ) {
                alert( json_data.error );
            } else {
                RepopulateGameDropdown();
            }
        } );
    }
}

var RefreshGame = function() {
    var game_name = GetGameName();
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

var MakeMove = function( move ) {
    var game_name = GetGameName();
    $.ajax( {
        url: 'make_move',
        data: JSON.stringify( { 'game_name' : game_name, 'move' : move, 'playing_as' : chess_board.state.playing_as } ),
        contentType: 'application/json',
        type: 'POST',
        success: function( json_data ) {
            if( json_data.error ) {
                alert( json_data.error );
            } else {
                RefreshGame();
                if( document.getElementById( 'computer_respond_checkbox' ).checked ) {
                    $( '#ajax_wait' ).show();
                    $.getJSON( 'make_computer_move', { 'game_name' : game_name }, function() {
                        if( json_data.error ) {
                            alert( json_data.error );
                        } else {
                            RefreshGame();
                        }
                        $( '#ajax_wait' ).hide();
                    } );
                }
            }
        }
    } );
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

var highlighted_tile_id = undefined; // Ick!  A global!
var valid_move_list = undefined; // Ugh...and another.

var GetLocationFromId = function( id ) {
    var loc = /([0-9])_([0-9])/g.exec( id );
    if( loc === null ) {
        return null;
    }
    return [ parseInt( loc[1] ), parseInt( loc[2] ) ];
}

var IsLocationInList = function( given_loc, location_list ) {
    for( var i = 0; i < location_list.length; i++ ) {
        var loc = location_list[i];
        if( loc[0] === given_loc[0] && loc[1] === given_loc[1] ) {
            return true;
        }
    }
    return false;
}

class ChessBoardTile extends React.Component {
    constructor( props ) {
        super( props );
    }

    OnDragStart( evt ) {
        if( evt.target.tagName === 'IMG' ) {
            valid_move_list = undefined;
            var source_id = evt.target.parentElement.id;
            evt.dataTransfer.setData( 'source_id', source_id );
            var source_loc = GetLocationFromId( source_id );
            $.ajax( {
                url: 'all_valid_moves',
                data: JSON.stringify( { game_name: GetGameName(), location: source_loc } ),
                contentType: 'application/json',
                type: 'POST',
                success: function( json_data ) {
                    valid_move_list = json_data.valid_move_list.map( move => move.target );
                }
            } );
        } else {
            // Don't allow drag somehow?
        }
    }

    OnDragOver( evt ) {
        evt.preventDefault(); // I'm not sure what the default does, but we probably want to prevent it.
    }

    OnDrop( evt ) {
        evt.preventDefault();
        var move = {
            source: GetLocationFromId( evt.dataTransfer.getData( 'source_id' ) ),
            target: GetLocationFromId( ( evt.target.tagName === 'IMG' ) ? evt.target.parentElement.id : evt.target.id )
        }
        MakeMove( move );
    }

    OnDragEnd( evt ) {
        this.ClearHighlightedTile();
    }

    ClearHighlightedTile() {
        if( highlighted_tile_id !== undefined ) {
            var tile_div = document.getElementById( highlighted_tile_id );
            tile_div.classList.remove( 'tile_move_good' );
            tile_div.classList.remove( 'tile_move_bad' );
            highlighted_tile_id = undefined;
        }
    }

    OnDragEnter( evt ) {
        this.ClearHighlightedTile();
        var tile_div = ( evt.target.tagName === 'IMG' ) ? evt.target.parentElement : evt.target;
        var target_id = tile_div.id;
        var target_loc = GetLocationFromId( target_id );
        if( valid_move_list !== undefined ) {
            if( IsLocationInList( target_loc, valid_move_list ) ) {
                tile_div.classList.add( 'tile_move_good' );
            } else {
                tile_div.classList.add( 'tile_move_bad' );
            }
            highlighted_tile_id = tile_div.id;
        }
    }

    render() {
        var parity = ( this.props.row + this.props.col ) % 2;
        var style = {
            gridRow: this.props.flip ? ( 9 - this.props.row ) : this.props.row,
            gridColumn: this.props.flip ? ( 9 - this.props.col ) : this.props.col
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
            var occupant_div = <img draggable={true} onDragStart={this.OnDragStart.bind(this)} className="occupant" src={'images/' + occupant_image + '.png'} width={100} height={100}></img>;
            tile_occupants.push( occupant_div );
        }
        return React.createElement( 'div', {
            id: id,
            style: style,
            className: tileClass,
            onDrop: this.OnDrop.bind(this),
            onDragOver: this.OnDragOver.bind(this),
            onDragEnter: this.OnDragEnter.bind(this),
            onDragEnd: this.OnDragEnd.bind(this),
            ref: 'tile'
        }, ...tile_occupants );
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

var LocationToNotation = function( loc ) {
    let file_array = [ 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h' ];
    let rank = 8 - loc[0];
    let file = file_array[ loc[1] ];
    return file + rank.toString();
}

var MoveToNotation = function( move ) {
    let piece_array = [ 'Pawn', 'Rook', 'Knight', 'Bishop', 'Queen', 'King' ];
    let i = move.actor < 7 ? move.actor - 1 : move.actor - 7;
    let piece_name = piece_array[i];
    let result = piece_name + ' at ' + LocationToNotation( move.move.source );
    if( move.capture ) {
        i = move.capture < 7 ? move.capture - 1 : move.capture - 7;
        piece_name = piece_array[i];
        result += ' takes ' + piece_name + ' at ';
    } else {
        result += ' moves to ';
    }
    result += LocationToNotation( move.move.target );
    return result; // TODO: Say something different for castling?
}

class ChessBoardHistoryBox extends React.Component {
    constructor( props ) {
        super( props );
        this.scroll_div = undefined;
    }

    // TODO: How do we click to have the last item applied?  Maybe have some |< < > >| buttons?
    OnItemClicked( evt ) {
        let id = evt.target.id;
        let loc = /history_box_item_([0-9]+)/g.exec( id );
        loc = parseInt( loc[1] );
        $.ajax( {
            url: 'change_board_location',
            data: JSON.stringify( { game_name: GetGameName(), location: loc } ),
            contentType: 'application/json',
            type: 'POST',
            success: function( json_data ) {
                if( json_data.error ) {
                    alert( json_data.error );
                } else {
                    RefreshGame();
                }
            }
        } );
    }

    ScrollToBottom() {
        let box_div = this.refs.box;
        if( this.scroll_div !== undefined ) {
            let element = document.getElementById( this.scroll_div.props.id );
            if( element ) {
                element.scrollIntoView( true );
            }
        } else {
            box_div.scrollTop = box_div.scrollHeight;
        }
    }

    componentDidMount() {
        this.ScrollToBottom();
    }

    componentDidUpdate() {
        this.ScrollToBottom();
    }

    render() {
        let move_history = this.props.move_history;
        let item_anchor_array = [];
        let i = 0;
        move_history.map( move => {
            let classStr = 'history_box_item';
            if( i === this.props.move_history_location ) {
                classStr += ' history_box_item_highlighted';
            }
            if( i % 2 === 1 ) {
                classStr += ' history_box_item_odd';
            }
            let item_div = <a id={"history_box_item_"+i.toString()} className={classStr}>{MoveToNotation(move)}</a>;
            item_anchor_array.push( item_div );
            if( i === this.props.move_history_location ) {
                this.scroll_div = item_div;
            }
            i++;
        } );
        return React.createElement( 'div', { id: "history_box", onClick: this.OnItemClicked.bind(this), ref: 'box' }, ...item_anchor_array );
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
            playing_as: 0,
            move_history: [],
            move_history_location: 0
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
        var whose_turn_div = <p style={style}>{whose_turn}</p>;
        var computer_checkbox = <p style={style}><input id="computer_respond_checkbox" type="checkbox"></input><label htmlFor="computer_respond_checkbox">Have computer respond.</label></p>;
        var history_box_div = <ChessBoardHistoryBox move_history={this.state.move_history} move_history_location={this.state.move_history_location}/>;
        var container_div = React.createElement( 'div', { style: { float: 'left', display: 'flex' } }, chess_board_div, history_box_div );
        return React.createElement( 'div', null, whose_turn_div, container_div, computer_checkbox );
    }
}

var chess_board = ReactDOM.render( <ChessBoard/>, document.getElementById( 'chess_board' ) );
var game_dropdown = ReactDOM.render( <GameDropdown/>, document.getElementById( 'game_dropdown_span' ) );

setInterval( function() {
    if( chess_board.state.whose_turn === 0 /* white */ || chess_board.state.whose_turn === 1 /* black */ ) {
        if( chess_board.state.playing_as !== 2 /* both */ && chess_board.state.playing_as !== chess_board.state.whose_turn ) {
            var game_name = GetGameName();
            $.getJSON( 'whose_turn', { 'game_name' : game_name }, function( json_data ) {
                if( json_data.whose_turn !== undefined && json_data.whose_turn === chess_board.state.playing_as ) {
                    RefreshGame();
                }
            } );
        }
    }
}, 1000 );

/* TODO: Fix this code.
var mouseover_tile_observable_array = [];
for( var i = 0; i < 8; i++ ) {
    for( var j = 0; j < 8; j++ ) {
        var id = i.toString() + '_' + j.toString();
        var tile = $( '#' + id );
        // It might be bad practice to do this on React-generated elements.
        // I may be able to get away with it, though, because the elements don't go stale.
        var observable$ = Rx.Observable.fromEvent( tile, 'mouseover' );
        mouseover_tile_observable_array.push( observable$ );
    }
}

// TODO: Use a catch here to be more resiliant?
Rx.Observable.merge( ...mouseover_tile_observable_array )
    .filter( evt => {
        var loc = GetLocationFromId( evt.currentTarget.id );
        return ( loc !== null ) ? true : false;
    } ).map( evt => {
        var loc = GetLocationFromId( evt.currentTarget.id );
        return loc;
    } ).switchMap( loc => {
        return Rx.Observable.fromPromise( $.ajax( {
            url: 'all_kill_moves',
            data: JSON.stringify( { game_name: GetGameName(), location: loc } ),
            contentType: 'application/json',
            type: 'POST'
        } ).promise() );
    } ).map( json_data => {
        return json_data.kill_move_list.map( move => move.target );
    } ).subscribe( target_list => {
        for( var i = 0; i < 8; i++ ) {
            for( var j = 0; j < 8; j++ ) {
                var id = i.toString() + '_' + j.toString();
                var tile = $( '#' + id );
                if( IsLocationInList( [ i, j ], target_list ) ) {
                    tile.addClass( 'tile_piece_checked' );
                } else {
                    tile.removeClass( 'tile_piece_checked' );
                }
            }
        }
    },
    error => {
        console.log( error );
    } ).catch( error => {
        return [];
    } );*/