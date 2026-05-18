# Fiber motor test bench software
This software interfaces with the fiber motor test bench hardware. It controls the motor, the power sources and monitors the forces

# Credits
The original source code, the main bulk, was written by MYKHAILO ISYP

# Install
Install python
Install git

Download the repo using the following command in the terminal
```
git clone https://github.com/rohitkjohnedu/fiber-motor-test-bench
```

This repo uses uv for managing python packages. It is faster and manages the dependencies better than pip. It automatically creates when we install the dependencies. It activates the venv when we run our code.
install uv using the following command in the terminal
```
pip install uv
```

Then run the command in the terminal
```
uv sync
```

# Running
run the command in the terminal
```
uv run .\main.py
```