"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from http import HTTPStatus
from flask import json

from tests.factories import AccountFactory
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service.routes import app

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"


######################################################################
#  T E S T   C A S E S
######################################################################
class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  A C C O U N T   T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_account = response.get_json()
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="test/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

######################################################################
# TEST - LIST ALL ACCOUNTS
######################################################################

    def test_list_accounts(self):
        """It should Create a list of Accounts when requested."""
        # Create test accounts using _create_accounts
        test_accounts = self._create_accounts(2)  # Create 2 test accounts

        response = self.client.get('/accounts')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)

        # Check if the number of returned accounts matches the created test accounts
        self.assertEqual(len(data), len(test_accounts))

        # Check if the serialized data matches the expected data for each account
        for i, account in enumerate(test_accounts):
            self.assertEqual(data[i]["name"], account.name)
            self.assertEqual(data[i]["email"], account.email)
            self.assertEqual(data[i]["address"], account.address)
            self.assertEqual(data[i]["phone_number"], account.phone_number)
            self.assertEqual(data[i]["date_joined"], str(account.date_joined))

    
######################################################################
# TEST - READ AN ACCOUNT
######################################################################
    def test_read_account(self):
        """It should Read a single Account"""
        # Create a test account using _create_accounts
        test_account = self._create_accounts(1)[0]

        response = self.client.get(
            f"{BASE_URL}/{test_account.id}", content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()

        # Check if the retrieved data matches the expected data of the test account
        self.assertEqual(data["name"], test_account.name)
        self.assertEqual(data["email"], test_account.email)
        self.assertEqual(data["address"], test_account.address)
        self.assertEqual(data["phone_number"], test_account.phone_number)
        self.assertEqual(data["date_joined"], str(test_account.date_joined))



    #test_account_not_found
    def test_read_account_not_found(self):
        """It should not Read an Account that is not found"""
        response = self.client.get(f"{BASE_URL}/0")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)



######################################################################
# TEST - UPDATE AN EXISTING ACCOUNT
######################################################################

    def test_update_nonexistent_account(self):
        account_id = 999  # Assuming this account ID does not exist
        new_data = {'name': 'Updated Name'}

        # Send a PUT request to update the nonexistent account
        response = self.client.put(f'{BASE_URL}/accounts/{account_id}', json=new_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)


######################################################################
# TEST - DELETE AN ACCOUNT
######################################################################

    def test_delete_existing_account(self):
        account_id = 1
        resp = self.client.delete(f'/accounts/{account_id}')
        self.assertEqual(resp.status_code, HTTPStatus.NO_CONTENT)
        #self.assert_called_once()

    def test_delete_nonexistent_account(self):
        resp = self.client.delete(f'/accounts/999')
        self.assertEqual(resp.status_code, HTTPStatus.NO_CONTENT)
