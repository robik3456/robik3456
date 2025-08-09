import random

solution = random.randint(1, 10)
guess = None
number_of_tries = 5

while guess != solution and number_of_tries > 0:
    guess = input("Please guess a number between 1 and 10: ")
    guess = int(guess)
    number_of_tries -= 1

    if guess == solution:
        print("Congratulations! You won! The solution was indeed:", solution)
        exit()
    elif guess <= solution:
        print("Nope! It is higher :)", number_of_tries, "tries left")
    else:
        print("Nope! It is lower :)", number_of_tries, "tries left")