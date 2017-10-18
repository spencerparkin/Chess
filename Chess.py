# Chess.py

import os
import cherrypy

class ChessApp( object ):
    def __init__( self, root_dir ):
        self.root_dir = root_dir

        # TODO: Cache mongo collection here.

    @cherrypy.expose
    def default( self, **kwargs ):
        cherrypy.response.headers['Content-Type'] = 'text/html'
        cherrypy.response.headers['cache-control'] = 'no-store'
        return cherrypy.lib.static.serve_file( root_dir + '/Chess.html', content_type='text/html' )

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