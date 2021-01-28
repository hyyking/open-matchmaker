CREATE TABLE IF NOT EXISTS player (
    discord_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(16) NOT NULL
);

CREATE TABLE IF NOT EXISTS team (
    code INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(16) NOT NULL UNIQUE,
    player_one INTEGER NOT NULL,
    player_two INTEGER NOT NULL,

    FOREIGN KEY (player_one) REFERENCES team(code)
);

CREATE TABLE IF NOT EXISTS result (
    round INT NOT NULL,
    
    team_one INT NOT NULL,
    res_one INT NOT NULL,
    delta_one FLOAT NOT NULL,
    
    team_two INT NOT NULL,
    res_two INT NOT NULL,
    delta_two FLOAT NOT NULL,

    PRIMARY KEY(round, team_one, team_two),
    FOREIGN KEY (round) REFERENCES turn(code),
    FOREIGN KEY (team_one) REFERENCES team(code),
    FOREIGN KEY (team_two) REFERENCES team(code)
);

CREATE TABLE IF NOT EXISTS turn (
    code INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    participants INT NOT NULL
);
