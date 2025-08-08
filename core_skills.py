import random
rand_list = random.sample(range(1, 21), 10)

list_comprehension_below_10 = [num for num in rand_list if num < 10]
print("Result with List comprehension: ", list_comprehension_below_10)

list_comprehension_below_10 = list(filter(lambda x:  x < 10, rand_list))

print("Result with filter: ", list_comprehension_below_10)