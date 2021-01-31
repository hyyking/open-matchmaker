DATABASE = matchmaker.sqlite3
LOG_LEVEL=debug
CONFIG=mmconfig.json

SQL = matchmaker_db.sql
MOCK_DB = tests/empty_mockdb.sqlite3 tests/full_mockdb.sqlite3

MODULES = bot matchmaker tests
TEST = all


.PHONY: run tree test lint clean

run: $(DATABASE) $(CONFIG)
	@clear
	@python -m bot --loglevel $(LOG_LEVEL) \
		       --database $(DATABASE) \
		       --config   $(CONFIG)

tree:
	@tree --dirsfirst -I "__pycache__"

test: $(MOCK_DB)
	@python -m tests $(TEST)

%.sqlite3:
	@sqlite3 $@ < $(SQL)

$(CONFIG):
	@[[ ! -a $@ ]] && python -m bot --dump_config > $(CONFIG)

tests/full_mockdb.sqlite3:
	@sqlite3 $@ < $(SQL)
	@python -m tests --generate NO_RUN

tests/empty_mockdb.sqlite3:
	-@rm tests/empty_mockdb.sqlite3 2> /dev/null || true
	@sqlite3 $@ < $(SQL)

lint:
	@mypy --namespace-packages $(MODULES)

clean:
	-@rm -r **/__pycache__ 2> /dev/null || true
	-@rm $(MOCK_DB) 2> /dev/null || true
