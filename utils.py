import ast
from dataclasses import dataclass
import os
import io
import sys
import contextlib
import traceback
import subprocess
from typing import Union, Dict, List, Optional


installdir = "/tmp/newpackages"
cachedir = "/tmp/temppipcachedir"


@dataclass
class Output:
    stdout: Optional[List[str]]
    statusCode: int = None
    eval_output: Union[Dict, List, str, int, float, None] = None
    error: Union[str, None] = None


def get_code(event: Dict) -> str:
    """
    Extract the code from the event.
    """
    if "code" in event:
        return event["code"]

    code = """
def func():
    import requests
    import logzero
    print('this is my print statement')
    x = 1
    y = 2
    print(x+y)
    return x+y*50
func()
"""
    return code


def validate_code(code: str) -> Union[None, ast.Module]:
    """
    Determine whether a given code is valid or not.
    If not, raise a SyntaxError.

    If valid code, validate that the function has the right format:
        * name is my_function
        * if there is a requirements decorator, its only argument is a dict of string: string
    If not valid, raise a ValueError.

    If valid, return the parsed code as a parsed ast.Module.
    Otherwise return None.
    """
    # valid code validation
    try:
        parsed = ast.parse(code)
    except:
        raise SyntaxError

    # function validation
    # empty body
    if not parsed.body:
        raise ValueError("Empty code.")
    func_err = ValueError(f"Only allowed code is a non-async function")
    # there's only one function
    if len(parsed.body) > 1:
        raise func_err
    # not a function definition
    if not isinstance(parsed.body[0], ast.FunctionDef):
        raise func_err
    # wrong function name
    if not parsed.body[0].name == "my_function":
        raise func_err

    # decorator validation
    # if no decorator, we assume no requirements are needed
    if parsed.body[0].decorator_list:
        decorator_err = ValueError("Incorrect decorator; @requirements(Dict[str, str])")
        # wrong decorator name
        if not parsed.body[0].decorator_list[0].func.id == "requirements":
            raise decorator_err
        # empty requirements args
        if not parsed.body[0].decorator_list[0].args:
            raise decorator_err
        # empty Dict arg
        if not parsed.body[0].decorator_list[0].args[0].keys:
            raise decorator_err
        # wrong args type
        if not isinstance(parsed.body[0].decorator_list[0].args[0], ast.Dict):
            raise decorator_err

        # correct requirements types
        if not all(
            [
                isinstance(x.value, str)
                for x in parsed.body[0].decorator_list[0].args[0].keys
            ]
        ) or not all(
            [
                isinstance(x.value, str)
                for x in parsed.body[0].decorator_list[0].args[0].values
            ]
        ):
            raise decorator_err

    return parsed


def install_and_import(packages):
    """
    Use pip to install packages to a local folder, using a local cache.
    """
    args = [
        "python3",
        "-m",
        "pip",
        "--disable-pip-version-check",
        "install",
        "--upgrade",
        *packages,
        # "--quiet",
        "--no-compile",
        "-t",
        installdir,
        "--cache-dir",
        cachedir,
    ]
    print('installing packages with command:',args)
    done = subprocess.run(args)
    # future: process stderr

def setup_packages(parsed: ast.Module) -> ast.Module:
    """
    If there is a packages decorator, install the packages it lists.
    Remove the decorator call and return the plain function definition.
    """
    dirr = os.listdir("/tmp")
    if not "newpackages" in dirr:
        os.mkdir(installdir)
    if not installdir in sys.path:
        sys.path.insert(0, installdir)

    if parsed.body[0].decorator_list:
        packages = dict(
            zip(
                parsed.body[0].decorator_list[0].args[0].keys,
                parsed.body[0].decorator_list[0].args[0].values,
            )
        )
        install_and_import(
            [
                f"{k.value}" + (f"=={v.value}" if v.value else "")
                for k, v in packages.items()
            ]
        )
        parsed.body[0].decorator_list.pop()
    return parsed


def run_code(parsed: ast.Module, *args, **kwargs) -> Output:
    """
    Given a valid code module containing some function:
        * compile the module and run it with a protected scope
        * return stdout, function output, and any errors to the user
    """
    name = parsed.body[0].name
    _globals, _locals = {}, {}
    # save the function definition to the local scope.
    exec(compile(parsed, "ast", "exec"), _globals, _locals)

    tb = None
    err = None
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        eval_output = None
        try:
            eval_output = _locals[name](*args, **kwargs)
        except Exception as e:
            tb = traceback.format_exc()
            err = e.args[0]
    stdout = f.getvalue().splitlines()

    if stdout:
        for x in stdout:
            print(x)
    if tb:
        stdout.append(err)
        # stdout.append(tb)
        # print(tb)

    return eval_output, stdout, err
