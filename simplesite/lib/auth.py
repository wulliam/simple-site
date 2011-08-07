from authkit.permissions import ValidAuthKitUser
from authkit.permissions import HasAuthKitRole
from authkit.authorize.pylons_adaptors import authorized
from pylons.templating import render_mako as render

is_valid_user = ValidAuthKitUser()
has_delete_role = HasAuthKitRole(['delete'])



def render_signin():
    result = render('/derived/account/signin.html')
    result = result.replace('%', '%%').replace('FORM_ACTION', '%s')
    return result