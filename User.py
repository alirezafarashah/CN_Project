import hashlib


class User:
    def __init__(self, username, password, role):
        self.username = username
        self.password = password
        self.type = role
        self.is_logged_in = False

    def check_password(self, password):
        return password == self.password


class UserClient(User):
    def __init__(self, username, password, role):
        super().__init__(username, password, role)
        self.strike = 0
        self.sent_tickets = []


class Admin(User):
    def __init__(self, username, password, role):
        super().__init__(username, password, role)
        self.received_tickets = []
        self.sent_tickets = []

    pass


class Manager(User):
    def __init__(self, username, password, role):
        super().__init__(username, password, role)
        self.admin_requests = []
        self.received_tickets = []


class AuthException(Exception):
    def __init__(self, username, user=None):
        super().__init__(username)
        self.username = username
        self.user = user


class UsernameAlreadyExists(AuthException):
    pass


class PasswordTooShort(AuthException):
    pass


class InvalidUsername(AuthException):
    pass


class InvalidPassword(AuthException):
    pass


class PermissionError(Exception):
    pass


class NotLoggedInError(AuthException):
    pass


class NotPermittedError(AuthException):
    pass


class Authenticator:
    def __init__(self):
        self.users = {}

    def add_user(self, username, password, role):
        if username in self.users:
            raise UsernameAlreadyExists(username)
        if role == "user":
            self.users[username] = UserClient(username, password, role)
        elif role == "manager":
            self.users[username] = Manager(username, password, role)
        else:
            self.users[username] = Admin(username, password, role)

    def login(self, username, password):
        try:
            user = self.users[username]
        except KeyError:
            raise InvalidUsername(username)

        if not user.check_password(password):
            raise InvalidPassword(username, user)

        user.is_logged_in = True
        return user

    def send_admin_reg_req(self, user_name, password, role):
        if user_name in self.users:
            raise UsernameAlreadyExists(user_name)
        manager = self.users["manager"]
        manager.admin_requests.append(Admin(user_name, password, role))

    def is_logged_in(self, username):
        if username in self.users:
            return self.users[username].is_logged_in
        return False


class Authorizer:
    def __init__(self, authenticator):
        self.authenticator = authenticator
        self.permissions = {}

    def add_permission(self, perm_name):
        try:
            perm_set = self.permissions[perm_name]
        except KeyError:
            self.permissions[perm_name] = set()
        else:
            raise PermissionError("Permission Exists")

    def permit_user(self, perm_name, username):
        try:
            perm_set = self.permissions[perm_name]
        except KeyError:
            raise PermissionError("Permission does not exist")
        else:
            if username not in self.authenticator.users:
                raise InvalidUsername(username)
            perm_set.add(username)

    def check_permission(self, perm_name, username):
        if not self.authenticator.is_logged_in(username):
            raise NotLoggedInError(username)
        try:
            perm_set = self.permissions[perm_name]
        except KeyError:
            raise PermissionError("Permission does not exist")
        else:
            if username not in perm_set:
                raise NotPermittedError(username)
            else:
                return True
