import random


def get_random_string(chars: str, n: int) -> str:
    res = ""
    list_chars = list(chars)
    for i in range(n):
        res += random.choice(list_chars)
    return res


def reapatable(func):
    def wrapper(*args, **kwargs) -> bool:

        if "repeat" in kwargs:
            n = kwargs["repeat"]
            del kwargs["repeat"]

            results = []
            for i in range(n):
                res = func(*args, **kwargs)
                if not res:
                    return False

                results.append(res)
            return True

        return func(*args, **kwargs)

    return wrapper


def round_float(f: float):
    return int(f * 100) / 100.0


def compare_strings(strA: str, strB: str) -> float:
    if len(strA) != len(strB):
        raise Exception(
            "The two strings do not have the same length. Unable to compare it"
        )
    n = len(strA)

    s = 1.0 * sum([strA[i] == strB[i] for i in range(n)])
    return round_float(s / n)
