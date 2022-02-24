import argparse


class Transaction:
    transaction_list = []

    def __init__(self, transaction_type, client_id, transaction_id, amount):
        self.transaction_type = transaction_type
        self.client_id = client_id
        self.transaction_id = transaction_id
        self.amount = amount

    @staticmethod
    def parse_transaction_csv(path_to_csv):
        with open(path_to_csv) as f:
            f.readline() # skip header line
            for line in f:
                line = line.rstrip()
                values = line.split(",")
                transaction_type = values[0]
                client_id = int(values[1])
                transaction_id = int(values[2])
                if transaction_type in ['dispute', 'resolve', 'chargeback']:
                    amount = None
                else:
                    amount = float(values[3])
                new_transaction = Transaction(transaction_type, client_id, transaction_id, amount)
                Transaction.transaction_list.append(new_transaction)

    @staticmethod
    def populate_client_list():
        for transaction in Transaction.transaction_list:
            client_id = transaction.client_id
            if client_id not in Client.client_list:
                Client.client_list[client_id] = Client(client_id)
            Client.client_list[client_id].transactions.append(transaction)


class Client:
    client_list = {}

    def __init__(self, client_id):
        self.client_id = client_id
        self.transactions = [] #Can probably make this a dictionary for quicker lookup
        self.available = 0
        self.held = 0
        self.total = 0
        self.locked = False

    def handle_deposit(self, amount):
        self.available += amount
        self.total += amount

    def handle_withdrawal(self, transaction_id, amount):
        if self.available < amount or self.total < amount:
            print("Error, Client has insufficient funds for withdrawal: " +
                  "ClientID: {}, TransactionID: {}, Available: {} Amount To Withdraw: {}".
                  format(self.client_id, transaction_id, self.available, amount))
        else:
            self.available -= amount
            self.total -= amount

    def handle_disputes_and_resolves_and_chargebacks(self, transaction_id, transaction_type):
        found = False
        for items in self.transactions:
            if items.transaction_id == transaction_id and items.transaction_type in ['withdraw', 'deposit']:
                if transaction_type == 'dispute':
                    self.held += items.amount
                    self.available -= items.amount
                    found = True
                elif transaction_type == 'resolve':
                    self.held -= items.amount
                    self.available += items.amount
                    found = True
                else:
                    self.held -= items.amount
                    self.total -= items.amount
                    self.locked = True
                    found = True
        if not found:
            print("Error, Client does not have matching transaction ID: " +
                  "ClientID: {}, TransactionID: {}".format(self.client_id, transaction_id))

    @staticmethod
    def resolve_transactions():
        for client_id, client in Client.client_list.items():
            for transaction in client.transactions:
                if transaction.transaction_type == 'deposit':
                    client.handle_deposit(transaction.amount)
                elif transaction.transaction_type == 'withdrawal':
                    client.handle_withdrawal(transaction.transaction_id, transaction.amount)
                elif transaction.transaction_type in ['dispute', 'resolve', 'chargeback']:
                    client.handle_disputes_and_resolves_and_chargebacks(transaction.transaction_id, transaction.transaction_type)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('csv_path', nargs='?', help='CSV file containing transactions')

    args = parser.parse_args()
    Transaction.parse_transaction_csv(args.csv_path)
    Transaction.populate_client_list()
    Client.resolve_transactions()

    print("Client, Available, Held, Total, Locked")
    for client_id, client in Client.client_list.items():
        print("{}, {}, {}, {}, {}".format(client.client_id, client.available, client.held, client.total, client.locked))
