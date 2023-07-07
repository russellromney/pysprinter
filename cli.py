import sys
import argparse
import json
import boto3


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["run"])
    parser.add_argument("file")
    parser.add_argument("--args", "-a", nargs="*")

    # extract arbitrary arguments
    # https://stackoverflow.com/a/37367814
    args, unknown = parser.parse_known_args()
    for arg in unknown:
        if arg.startswith(("-", "--")):
            # you can pass any arguments to add_argument
            parser.add_argument(arg.split("=")[0])
    args = parser.parse_args()
    
    # turn those arbitrary arguments into kwargs
    kwargs = {}
    for k, v in args.__dict__.items():
        if not k in ("mode", "file", "args"):
            kwargs[k] = v
    for k in kwargs:
        del args.__dict__[k]

    # send the event to the lambda
    path = args.file
    try:
        code = open(path).read()
    except:
        print(f"Code not available at path: {path}")
        print("Exiting.")
        sys.exit()

    # send the event to lambda to validate and run code
    event = {
        "code": code,
        "args": args.args,
        "kwargs": kwargs,
    }
    client = boto3.client("lambda")
    response = client.invoke(
        FunctionName="pysprinter-dev-core",
        InvocationType="RequestResponse",
        Payload=json.dumps(event),
    )

    # response and error handling
    if "Payload" in response:
        out = json.loads(response["Payload"].read().decode())

        if not "error" in out:
            if "errorMessage" in out:
                print(
                    "There was an uncaught system error. Check function logs for details."
                )
                print(out["errorMessage"])
                sys.exit()

        if out["error"]:
            print("Runtime error:")
            print(out["error"])
        else:
            print("Output:")
            print(out["eval_output"])
    else:
        print("There was an uncaught error. Check function logs for details.")