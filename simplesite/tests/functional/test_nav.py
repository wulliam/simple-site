from simplesite.tests import *

class TestNavController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='nav', action='index'))
        # Test response...
