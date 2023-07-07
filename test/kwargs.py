@requirements({"requests": "2.30.0", "logzero": ""})
def my_function(input_value: str, this: str=None):
    import requests

    x = f"input value is: {input_value}"
    print(x)
    return [input_value, this]
