# pysprinter

A prototype serverless Python runner using AWS Lambda.


Basic design: 
1. The user deploys the code runner to AWS as a Lambda. 
2. The user write a file with a function and passes dependencies & versions to a `requirements` decorator.
3. the user passes the filepath and any desired arguments to the CLI, which remotely validates and runs the input file and returns the output. 


## Use

**Basics**

Write a file with a function and decorator specifying dependencies. 
Dependencies that don't require a specific version can be left blank.

```python
# myfile.py
@requirements({'requests': '2.30.0','logzero':''})
def my_function(input_value: str):
    import requests
    return input_value
```

Then trigger the CLI, passing any positional arguments. 

```shell
python cli.py run myfile.py -a 5
>>> 5
```


**Example with `kwargs`**

If your function has optional or named arguments, you can pass arbitrary `kwargs` as required.

```python
# myfile.py
@requirements({'requests': ''})
def my_function(input_value: str, arg1: str=None, arg2: str):
    import requests
    return [input_value, arg1, arg2]
```

```shell
python cli.py run myfile.py -a 5 -arg1 this --arg2 that
>>> ["5", "this", "that"]
```

## Setup 

The code runner and CLI only require local `python3` and `boto3` installed.

Requirements: 

1. You are using a Unix-based system like Linux or Mac.
2. You have the AWS CLI configured with a valid account in ~/.aws/credentials.
2. You have Python 3.9+ installed on your system, accessible with the `python` command.
5. You have boto3 installed. 
3. You have the Serverless framework installed (`npm install -g serverless`). 

Deploy the code runner function by `cd`ing into the pysprinter directory and running:

```shell
sls deploy
```

This creates a new "dev" Cloudformation stack with an S3 bucket+policy, a function, a role, and a log group.


## Limitations and Improvements

**Lil bugs**

Arbitrary `kwargs` cannot be named "args" or "a". 

It is left as an exercise for the user to validate that package names and versions can be installed. A clear improvement would be validating package names and version.

**Real-world usefulness**

In practice, a code runner would likely be used to chain together a functional DAG of many operations on given data to produce outputs. Thus functionality to orchestrate that DAG with dependencies between functions and outputs would make this project more useful. 

Actual functions would likely need to access data of some kind - so adding an ability to name, access, and cache data sources between runs would add to the usefulness.

Finally, the ability to view logs is built in but not used - turning this on
would give the user a better view into the logs/printouts of their code as it runs.

**Storage**

AWS Lambda ephemeral storage limits the total size of all installed packages + code to 10GB. Running on proprietary hardware with (in practice) few size limits, or dynamically pulling packages at run-time into the workspace would solve this.

**Speed** 

First-time execution speed is limited to the install speed of the packages. After the first execution, packages are cached, but the code checks the installation status each time. This is much slower than having the packages installed from the start. This could be improved, by running proprietary hardware, using a package cache server, hooking the Lambda to block storage with many more packages, saving the packages to S3 to re-use them, etc. 

E.g. if the requirements list `torch`, then the lambda must download ~1GB of files and then install them - which runs against its memory limit. Larger memory would make this less slow.

**Security**

This design validates that the code is valid and the dependecies are valid and specified as expected. If the writer of the code and host of the code are different, then this design would be very easy to exploit for e.g. DDoS, exploring the host's code, or potentially finding vectors for exploration in the host's cloud environment. You can't totally lock down untrusted code, but isolated hardware/VMs and an enforced "allow-list" of packages and behaviors could make this more secure.

That being said, this project is fine for trusted code.


**Improvements**

Architecture:
* run code in isolated sandboxes on proprietary architecture using a much faster build/launch layer, e.g. Firecracker VMs or similar.
* run a `pip` cache to automatically download and re-load required dependency versions at run-time; this could be in a server or in S3/similar
* hook the Lambda up to block storage with packages cached for faster access
* run a packaging server which combines code and functions into a "deployment package"
* use larger RAM for the Lambda

Code design: 
* add CLI functionality to chain together multiple functions sequentially - accept outputs as inputs, etc. 
* add CLI functionality to build DAGs of multiple functions and run them concurrently according to the dependency graph
* add ability to pull in data used by multiple functions and cache it between runner executions
* validate that packages are valid
* let the user view the stdout of their code

Dev experience:
* the dev experience is simple but not fun...there's room for colors and descriptive printouts (timestamps, etc. e.g.) that could make this much nicer.