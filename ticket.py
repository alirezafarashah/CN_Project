ID = 0


class Ticket:
    def __init__(self, message, sender_user_name, receiver):
        global ID
        self.message_sender = [message]
        self.message_receiver = []
        self.status = "new"
        self.sender = sender_user_name
        self.receiver = receiver
        self.id = ID
        ID += 1
