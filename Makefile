DATABASE = matchmaker.sqlite3
SQL = matchmaker_db.sql
MODULES = bot matchmaker
TEST = all

run:
	@python -m bot --debug --database $(DATABASE)
tree:
	@tree --dirsfirst -I "__pycache__"
test:
	@python -m tests $(TEST)

lint:
	@mypy $(MODULES)

db:
	@sqlite3 $(DATABASE) < $(SQL)
	@sqlite3 tests/empty_mockdb.sqlite3 < $(SQL)
	
	@sqlite3 tests/full_mockdb.sqlite3 < $(SQL)
	@python -m tests --generate 

dbrm:
	@rm $(DATABASE)
	@rm tests/full_mockdb.sqlite3
	@rm tests/empty_mockdb.sqlite3
