import transaction
d = {}
transaction.begin()
try:
    d[5] = 50
    raise ValueError()
    transaction.commit()
except Exception as e:
    print(d)
    print(e)
    transaction.abort()

print(d)
