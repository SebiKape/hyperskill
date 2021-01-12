import random
import sqlite3



class Card:
    IIN = "400000"

    def __init__(self):
        self.id = 0
        self.balance = 0
        self.card_PIN = "0000"
        self.card_number = "0000000000000000"

    def create_card(self, conn):
        randnumber = ""
        randpin = ""
        for _ in range(9):
            random.seed()
            randnumber += str(random.randint(0, 9))
        for _ in range(4):
            random.seed()
            randpin += str(random.randint(0, 9))
        self.card_PIN = randpin
        card_checksum = Card.get_sum_luhn(Card.IIN + randnumber)
        self.card_number = Card.IIN + randnumber + card_checksum
        self.insert_to_db(conn)

    def insert_to_db(self, conn):
        number = self.card_number
        pin = self.card_PIN
        balance = self.balance
        cur = conn.cursor()
        SQL_string = ''' INSERT INTO card(number, pin, balance)
        VALUES (?, ?, ?)
        ;
        '''
        cur.execute(SQL_string, [number, pin, balance])
        conn.commit()

    @staticmethod
    def get_sum_luhn(card_number):
        new_card_number = ""
        index = 1
        for dig in card_number:
            dig = int(dig)
            if (index % 2) != 0:
                dig *= 2
            new_card_number += str(dig)
            index += 1
        card_number = ""
        for dig in new_card_number:
            dig = int(dig)
            if dig > 9:
                dig -= 9
            card_number += str(dig)
        sum = 0
        for dig in card_number:
            dig = int(dig)
            sum += dig
        checksum = 10 - (sum % 10)
        if checksum == 10:
            checksum = 0
        return str(checksum)

    @staticmethod
    def check_luhn(card_number):
        checksum = card_number[15]
        exp_checksum = Card.get_sum_luhn(card_number[:15])
        if checksum == exp_checksum:
            return True
        else:
            return False

    def search_card(self, conn, card_number_inp):
        cur = conn.cursor()
        SQL_query = "SELECT * FROM card WHERE number = ?"
        cur.execute(SQL_query, (card_number_inp,))
        card_info = cur.fetchone()
        if card_info is None:
            return None
        self.id = card_info[0]
        self.card_number = card_info[1]
        self.card_PIN = card_info[2]
        self.balance = card_info[3]
        return self

    def check_PIN(self, conn, pin_inp):
        cur = conn.cursor()
        SQL_query = "SELECT pin FROM card WHERE id = ?"
        cur.execute(SQL_query, (str(self.id),))
        pin_db = cur.fetchone()
        if pin_db is None:
            return False
        if pin_inp == pin_db[0]:
            return True
        else:
            return False

    def log_in(self, conn):
        print("\nEnter your card number:")
        user_number_inp = input()
        print("\nEnter your PIN:")
        user_pin_inp = input()
        self = self.search_card(conn, user_number_inp)
        if self is None:
            return None, False
        else:
            if self.check_PIN(conn, user_pin_inp):
                return self, True
            else:
                return None, False

    def log_ui(self, conn):
        logged = True
        while logged:
            self = self.search_card(conn, self.card_number)
            print("\n1. Balance")
            print("2. Add income")
            print("3. Do transfer")
            print("4. Close account")
            print("5. Log out")
            print("0. Exit\n")
            user_inp = int(input())
            if not user_inp:
                print("\nBye!")
                return True
            elif user_inp == 1:
                print("\nBalance: {}".format(self.balance))
            elif user_inp == 2:
                print("Enter income:")
                income_inp = input()
                total_balance = self.balance + int(income_inp)
                SQL_query = '''UPDATE card
                SET balance = ?
                WHERE id = ?
                '''
                cur = conn.cursor()
                cur.execute(SQL_query, (str(total_balance), str(self.id)))
                conn.commit()
                print("Income was added!")
            elif user_inp == 3:
                print("Transfer\nEnter card number:")
                t_card_number = input()
                if t_card_number == self.card_number:
                    print("You can't transfer money to the same account!")
                elif Card.check_luhn(t_card_number):
                    t_card = Card()
                    t_card = t_card.search_card(conn, t_card_number)
                    if t_card is None:
                        print("Such a card does not exist")
                    else:
                        print("Enter how much money you want to transfer:")
                        transfer = int(input())
                        if transfer > self.balance:
                            print("Not enough money!")
                        else:
                            t_quantity = transfer + t_card.balance
                            SQL_query = "UPDATE card SET balance = ? WHERE id = ?"
                            cur.execute(SQL_query, (str(t_quantity), str(t_card.id)))
                            conn.commit()

                            total_balance = self.balance - transfer
                            SQL_query = '''UPDATE card
                            SET balance = ?
                            WHERE id = ?
                            '''
                            cur.execute(SQL_query, (str(total_balance), str(self.id)))
                            conn.commit()
                            print("Success!")
                else:
                    print("Probably you made a mistake in the card number. Please Try again!")
            elif user_inp == 4:
                SQL_query = "DELETE FROM card WHERE id = ?"
                cur = conn.cursor()
                cur.execute(SQL_query, (str(self.id),))
                conn.commit()
                print("The account has been closed!")
            elif user_inp == 5:
                print("\nYou have successfully logged out!")
                logged = False
        return False


conn = sqlite3.connect('card.s3db')
cur = conn.cursor()
SQL_string = '''CREATE TABLE IF NOT EXISTS card (
id INTEGER NOT NULL PRIMARY KEY,
number TEXT,
pin TEXT,
balance INTEGER DEFAULT 0
)
'''
cur.execute(SQL_string)
conn.commit()
Exited = False
while not Exited:
    print("\n1. Create an account")
    print("2. Log into account")
    print("0. Exit\n")
    user_inp = int(input())
    if not user_inp:
        print("\nBye!")
        Exited = True
    elif user_inp == 1:
        user_card = Card()
        user_card.create_card(conn)
        print("\nYour card has been created")
        print("Your card number: \n{}".format(user_card.card_number))
        print("Your card PIN: \n{}".format(user_card.card_PIN))
    elif user_inp == 2:
        card = Card()
        card, logged = card.log_in(conn)
        if logged:
            print("\nYou have successfully logged in")
            Exited = card.log_ui(conn)
        else:
            print("\nWrong card number or PIN!")
