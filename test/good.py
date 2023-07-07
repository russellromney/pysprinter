@requirements({"requests": "2.30.0", "logzero": ""})
def my_function(input_value: str):
    import requests

    x = f"input value is: {input_value}"
    print(x)
    return (f"{input_value} "*3)[-2]
