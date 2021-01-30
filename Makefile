DATABASE = matchmaker.sqlite3
MOCK_DB = tests/empty_mockdb.sqlite3 tests/full_mockdb.sqlite3

SQL = matchmaker_db.sql

MODULES = bot matchmaker tests
TEST = all

.PHONY: run tree test lint clean

run: $(DATABASE)
	@clear
	@python -m bot --debug --database $(DATABASE)

tree:
	@tree --dirsfirst -I "__pycache__"

test: $(MOCK_DB)
	@python -m tests $(TEST)

%.sqlite3:
	@sqlite3 $@ < $(SQL)

tests/full_mockdb.sqlite3:
	@sqlite3 $@ < $(SQL)
	@python -m tests --generate NO_RUN

lint:
	@mypy --namespace-packages $(MODULES)

clean:
	-@rm -r **/__pycache__ 2> /dev/null || true
	-@rm tests/full_mockdb.sqlite3 2> /dev/null || true
	-@rm tests/empty_mockdb.sqlite3 2> /dev/null || true
