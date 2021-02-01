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

-- Query Team with Player info
CREATE VIEW IF NOT EXISTS team_with_details AS
SELECT team.team_id,
       team.name as team_name,
       p1.discord_id as player_one_id,
       p1.name as player_one_name,
       p2.discord_id as player_two_id,
       p2.name as player_two_name
FROM team
INNER JOIN player as p1 on team.player_one = p1.discord_id
INNER JOIN player as p2 on team.player_two = p2.discord_id;

-- Query Team with Player and elo delta
CREATE VIEW IF NOT EXISTS team_details_with_delta AS
SELECT team.*, COALESCE(SUM(result.delta), 0) as delta_sum
FROM team_with_details as team
LEFT OUTER JOIN result ON team.team_id = result.team_id
GROUP BY team.team_id;

-- Query Result with Team details
CREATE VIEW IF NOT EXISTS result_with_team_details AS
SELECT result.result_id, team.*, result.points, result.delta
FROM result
INNER JOIN team_with_details as team ON result.team_id = team.team_id;
