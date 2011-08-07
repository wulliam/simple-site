import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to

from simplesite.lib.base import BaseController, render
import simplesite.lib.helpers as h

log = logging.getLogger(__name__)

class AccountController(BaseController):

    def index(self):
        # Return a rendered template
        #return render('/account.mako')
        # or, return a response
        return 'Hello World'
    
    def signinagain(self):
        request.environ['paste.auth_tkt.logout_user']()
        return render('/derived/account/signin.html').replace('FORM_ACTION', h.url_for('signin'))

    def signin(self):
        #for key, value in request.environ.items():
        #    log.info("key:%s - value:%s" % (key, value))
        if not request.environ.get('REMOTE_USER'):
            # This triggers the AuthKit middleware into displaying the sign-in form
            abort(401)
        else:
            return render('/derived/account/signedin.html')

    def signout(self):
        # The actual removal of the AuthKit cookie occurs when the response passes
        # through the AuthKit middleware, we simply need to display a page
        # confirming the user is signed out
        return render('/derived/account/signedout.html')