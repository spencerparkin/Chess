// Chess.jsx

class ChessBoardTile extends React.Component {
    constructor( props ) {
        super( props );
    }

    render() {
        var parity = ( this.props.row + this.props.col ) % 2;
        var style = {
            gridRow: this.props.row,
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
                [ 8, 9, 10, 11, 12, 10, 9, 8 ],
                [ 7, 7, 7, 7, 7, 7, 7, 7 ],
                [ 0, 0, 0, 0, 0, 0, 0, 0 ],
                [ 0, 0, 0, 0, 0, 0, 0, 0 ],
                [ 0, 0, 0, 0, 0, 0, 0, 0 ],
                [ 0, 0, 0, 0, 0, 0, 0, 0 ],
                [ 1, 1, 1, 1, 1, 1, 1, 1 ],
                [ 2, 3, 4, 6, 5, 4, 3, 2 ]
            ]
        }
    }

    render() {
        var tile_array = [];
        for( var row = 1; row <= 8; row++ ) {
            for( var col = 1; col <= 8; col++ ) {
                var tile = <ChessBoardTile row={row} col={col} matrix={this.state.matrix}/>;
                tile_array.push( tile );
            }
        }
        return React.createElement( 'div', { id: 'chess_board' }, ...tile_array );
    }
}

ReactDOM.render( <ChessBoard/>, document.getElementById( 'chess_board' ) );