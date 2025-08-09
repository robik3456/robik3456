from random import randint

#create a list of play options
t = ["Rock", "Paper", "Scissors"]

#assign a random play to the computer
computer = t[randint(0,2)]
num_of_win = 0
num_of_lose = 0

#set player to False
player = False

def lose():
    print()
    print("You lost! Computer chose:", computer)
    print("Standings: Player", num_of_win, "- Computer", num_of_lose)

def win():
    print()
    print("You won! Computer chose:", computer)
    print("Standings: Player", num_of_win, "- Computer", num_of_lose)

def tie():
    print()
    print("It is a tie! Computer also chose:", computer)
    print("Standings: Player", num_of_win, "- Computer", num_of_lose)

while player == False:
#set player to True
    player = input("Rock, Paper, Scissors? ")
    if player != "Rock" and player != "Paper" and player != "Scissors":
        print("That's not a valid play. Check your spelling!")
    elif player == computer:
        tie()
    elif (player == "Rock" and computer == "Scissors") or (player == "Paper" and computer == "Rock") or (player == "Scissors" and computer == "Paper"):
        num_of_win += 1
        win()
    else:
        num_of_lose += 1
        lose()

    if num_of_win == 5:
        print("Congratulations! You won the game")
        print()
        exit()

    if num_of_lose == 5:
        print("I am sorry, you lost the game :(")
        print()
        exit()

    if num_of_win > num_of_lose:
        print("Come on! You are leading by ", num_of_win - num_of_lose, " points!")
    elif num_of_win < num_of_lose:
        print("Noooo! You are losing by ", num_of_lose - num_of_win, " points!")
    else:
        print("Hehe, it is a tie")
    print()
    
    #player was set to True, but we want it to be False so the loop continues
    player = False
    computer = t[randint(0,2)]