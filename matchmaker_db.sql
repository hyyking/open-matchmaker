CREATE TABLE IF NOT EXISTS player (
    discord_id INTEGER PRIMARY KEY,
    name VARCHAR(16) NOT NULL
);

CREATE TABLE IF NOT EXISTS turn (
    round_id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    participants INT NOT NULL
);

CREATE TABLE IF NOT EXISTS team (
    team_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(16) NOT NULL UNIQUE,
    player_one INTEGER NOT NULL,
    player_two INTEGER NOT NULL,

    FOREIGN KEY (player_one) REFERENCES team(code),
    FOREIGN KEY (player_two) REFERENCES team(code)
);

CREATE TABLE IF NOT EXISTS match (
    match_id INTEGER PRIMARY KEY AUTOINCREMENT,
    round_id INTEGER NOT NULL,
    result_one INTEGER NOT NULL,
    result_two INTEGER NOT NULL,

    odds_ratio FLOAT,

    FOREIGN KEY (round_id) REFERENCES turn(round_id),
    FOREIGN KEY (result_one) REFERENCES result(result_id),
    FOREIGN KEY (result_two) REFERENCES turn(result_id)

);

CREATE TABLE IF NOT EXISTS result (
    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    team_id INT NOT NULL,
    points INT NOT NULL,
    delta FLOAT NOT NULL,
    
    FOREIGN KEY (team_id) REFERENCES team(team_id)
);
