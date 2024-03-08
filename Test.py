import time

# Simple loading animation
for i in range(5):
    print(f"Loading{'.' * i}", end="")
    time.sleep(1)

# Add a newline after the loading animation
print("\nDone")
