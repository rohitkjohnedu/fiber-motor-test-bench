import time

# Measure performance
start_time = time.perf_counter()
# Code to be measured for performance
end_time = time.perf_counter()
execution_time = end_time - start_time
print("Execution time:", execution_time, "seconds")