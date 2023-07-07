from dataclasses import asdict
import json

from utils import Output, get_code, validate_code, setup_packages, run_code


def handler(event, context):
    """
    Orchestrates running user-input Python and installing dependencies.
    Validates the code is valid and has the correct input structure. 
    Runs the code and returns a summary to the user of logs, output, and errors.
    """
    out = Output([])

    # validate code
    code = get_code(event)
    try:
        parsed = validate_code(code)
    except SyntaxError:
        out.error = f"Code Error: invalid syntax"
    except ValueError as e:
        out.error = f"Code Error: {e.args[0]}"
    if out.error:
        out.statusCode = 400
        return asdict(out)

    # handle dependecies
    # note - for large packages (e.g. torch) this is the slowest step
    setup_packages(parsed)

    # run code
    out.eval_output, out.stdout, out.error = run_code(
        parsed, *event["args"], **event["kwargs"]
    )

    # return summary
    if out.eval_output:
        try:
            json.dumps(out.eval_output)
        except:
            out.eval_output = None
            out.error = "Function return value is not JSON-serializable."

    out.statusCode = 200
    if out.error:
        out.statusCode = 400
    return asdict(out)
