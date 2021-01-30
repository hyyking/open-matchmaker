# Baby'Haxball MatchMaker

![Affiche](project/static/affiche.png)

## Usage

1. Create a discord bot
2. Set token environment variable (`export DISCORD_TOKEN = ?`)
3. Run with `make run`


## Configuration

Bot and matchmaker are configurable independently, however you can specify a single
config file (default is [`mmconfig.json`](mmconfig.json)):

```json
{
    "bot": {
	"command_prefix": "+",
	"err_prefix": ":weary:",
	"ok_prefix": ":smile:"
    },

    "matchmaker": {
	"base_elo": 1000,
	"points_per_match": 7,
	"k_factor": 16,

	"trigger_threshold": 10,

	"period": {
	    "active": 3.0,
	    "duty_cycle": 0.2
	}
    }
}
```

## System

> description article in [french](project/PROJECT.md)

The system is based around an elo model with a seasonal parameter.
Summary:

```
ELO:
  BASE_ELO = 1000
  K = 16
  PPM = 7    // points per match

SEASONAL:
  PERIOD = 3 // every 3 period the seasonal parameter is on
  DUTY_CYCLE = 0.2 // length of the activity (corresponds to one period)
```

The seasonal parameter's purpose is to reduce the distance between higher and lower
ranked teams. And thus add distance to teams with similar ranks. This adds a bit of
variance between matches and allows lower teams to upset and gain more elo.
