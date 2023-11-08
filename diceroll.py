import random

min_value = 1
max_value = 6
roll_again = "yes"

total = 0
total_total = 0
max_total = 0
rolls = 0

while roll_again == "yes" or roll_again == "y":
    print()
    print("Rolling the dices...")

    value1 = random.randint(min_value, max_value)
    value2 = random.randint(min_value, max_value)
    value3 = random.randint(min_value, max_value)

    rolls += 1
    total = value1 + value2 + value3
    total_total = total_total + total

    if total > max_total:
        max_total = total

    print(value1,value2,value3)
    print("The total value of this roll is", total)
    print("Your highest roll so far was", max_total)
    print("The total value of your rolls so far was", total_total, "by rolling", rolls, "times. This is an average of:", round(total_total / rolls,2))
    print()

    if total == 3:
        print("I am sorry, you are extra unlucky today")
        print()
        exit()
    elif total == 18:
        print("WOW, you are extra lucky today")
        print()
        exit()        

    roll_again = input("Press 'y' or 'yes' to roll the dices again: ")
print("Have a good day.")
print()