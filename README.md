# _Open MatchMaker_

Open source elo-based matchmaking system for teams of two players. This project
comes with a discord bot implementation.

## MatchMaker

### Decision methods

The matchmaker comes with different decision methods:

- max_sum: Takes the set that has the maximal utility (think efficiency)
- min_variance: Takes the set that makes the most similar matches
- maxmin: Takes the set that makes the best worst match (improves matches for the worst team)
- minmax: Takes the set that makes the worst best match (best teams will have more variable opponents)

### Elo with seasonal factor

The seasonal parameter's purpose is to reduce the distance between higher and lower
ranked teams, thus adding distance to teams with similar ranks. This adds a bit of
variance between matches and allows lower teams to upset and gain more elo.

Example configuration:

```json
"period": {
    "active": 3,
    "duty_cycle": 1
},
```

The `active` parameter is the frequency at which the parameter will activate. The `duty_cycle`
parameter is the duration of this unbalanced state. You can disable this behavior by putting
the `duty_cycle` at 5.

## Discord Bot

1. Create a discord bot
2. Set token environment variable (`export DISCORD_TOKEN = ?`)
3. Run with `make run` (check the [`Makefile`](Makefile) for database/log/config specification)

### Configuration

Bot and matchmaker are configurable independently, however you can specify a single
config file (default is [`mmconfig.json`](mmconfig.json)):

```json
{
    "bot": {
        "command_prefix": "+",
        "channel": "haxball",
        "ok_prefix": ":smile:",
        "err_prefix": ":weary:"
    },
    "matchmaker": {
        "base_elo": 1000,
        "points_per_match": 1,
        "k_factor": 32,
        "period": {
            "active": 3,
            "duty_cycle": 1
        },
        "trigger_threshold": 10,
        "max_history": 3,
        "principal": "max_sum"
    }
}
```

## Licence

This project is licenced under the EUROPEAN UNION PUBLIC LICENCE v. 1.2
