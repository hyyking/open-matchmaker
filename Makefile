DATABASE = matchmaker.sqlite3
LOG_LEVEL=debug
CONFIG=mmconfig.json
TEST = all

SQL = matchmaker_db.sql
MOCK_DB = tests/empty_mockdb.sqlite3 tests/full_mockdb.sqlite3

MODULES = bot matchmaker tests


.PHONY: run test tree lint clean

# -- Run
run: $(DATABASE) $(CONFIG) $(SQL)
	@clear
	@python -m bot --loglevel $(LOG_LEVEL) \
		       --database $(DATABASE) \
		       --config   $(CONFIG)

$(CONFIG):
	@[[ ! -a $@ ]] && python -m bot --dump_config > $(CONFIG)

$(DATABASE): $(SQL)
	sqlite3 $@ < $(SQL)


# -- Test
test: $(MOCK_DB)
	@python -m tests $(TEST)

tests/%.sqlite3: $(SQL) tests/generate.py
	-@rm $@ 2> /dev/null || true
	sqlite3 $@ < $(SQL)
	@if [ $@ = "tests/full_mockdb.sqlite3" ]; then \
	    python -m tests --generate; \
	fi


# -- Util
tree:
	@tree --dirsfirst -I "__pycache__"

lint:
	@mypy --namespace-packages $(MODULES)

clean:
	-@rm -r **/__pycache__ 2> /dev/null || true
	-@rm $(MOCK_DB) 2> /dev/null || true
