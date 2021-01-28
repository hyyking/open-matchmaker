DATABASE = matchmaker.sqlite3
SQL = matchmaker_db.sql

run:
	@python -m bot --debug
db:
	@sqlite3 $(DATABASE) < $(SQL)
tree:
	@tree --dirsfirst -I "__pycache__"

dbrm:
	@rm $(DATABASE)
