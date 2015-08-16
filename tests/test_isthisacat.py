'''
Created on Aug 16, 2015

@author: hashtonmartyn
'''
import unittest
from isthisacat import app, DATABASE_PATH_KEY, init_db, get_no_votes, get_yes_votes
import tempfile
import os
import re

csrf_token_input = re.compile(
    r'type="hidden" name="csrf_token" value="([0-9a-z#A-Z-\.]*)"'
)

class TestIsThisACat(unittest.TestCase):

    def setUp(self):
        self.db_fd, app.config[DATABASE_PATH_KEY] = tempfile.mkstemp()
        app.config["TESTING"] = True
        self.test_client = app.test_client()
        init_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(app.config[DATABASE_PATH_KEY])
        
    def get_csrf_token(self, data):
        match = csrf_token_input.search(u"%s" % data)
        assert match
        return match.groups()[0]
    
    def _vote(self, iscat, csrf_token):
        return self.test_client.post("/vote",
                                     data={"iscat": iscat,
                                           "csrf_token": csrf_token},
                                     follow_redirects=True)
        
    def vote_yes(self, csrf_token):
        return self._vote("TRUE", csrf_token)
        
    def vote_no(self, csrf_token):
        return self._vote("FALSE", csrf_token)
    
    def get_num_yes_votes(self):
        return int(self.test_client.get("/votes/yes").data)
    
    def get_num_no_votes(self):
        return int(self.test_client.get("/votes/no").data)

    def test_vote_cookie_not_set_shows_voting_options(self):
        rv = self.test_client.get("/")
        self.assertIn("Yes, this is a cat", rv.data)
        self.assertIn("No, this is not a cat", rv.data)
        
    def test_first_yes_vote(self):
        index_rv = self.test_client.get("/")
        csrf_token = self.get_csrf_token(index_rv.data)
        rv = self.vote_yes(csrf_token)
        self.assertIn("Results so far",
                      rv.data)
        self.assertEqual(1, self.get_num_yes_votes())
        self.assertEqual(0, self.get_num_no_votes())
        
    def test_first_no_vote(self):
        index_rv = self.test_client.get("/")
        csrf_token = self.get_csrf_token(index_rv.data)
        rv = self.vote_no(csrf_token)
        self.assertIn("Results so far",
                      rv.data)
        self.assertEqual(0, self.get_num_yes_votes())
        self.assertEqual(1, self.get_num_no_votes())
        
    def test_yes_vote_with_no_csrf_token(self):
        rv = self.test_client.post("/vote",
                                   data={"iscat": "TRUE"},
                                   follow_redirects=True)
        self.assertIn("CSRF token missing or incorrect.",
                      rv.data)
        self.assertEqual(400, rv.status_code)
        
    def test_no_vote_with_no_csrf_token(self):
        rv = self.test_client.post("/vote",
                                   data={"iscat": "FALSE"},
                                   follow_redirects=True)
        self.assertIn("CSRF token missing or incorrect.",
                      rv.data)
        self.assertEqual(400, rv.status_code)
        
    def test_test_interfaces_not_available_if_testing_not_in_config(self):
        del app.config["TESTING"]
        self.assertEqual(404, self.test_client.get("/votes/yes").status_code)
        self.assertEqual(404, self.test_client.get("/votes/no").status_code)
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    #Comment
    unittest.main()