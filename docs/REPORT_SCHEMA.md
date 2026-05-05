# Report Schema

```json
{
  "run_id": "string",
  "generated_at": "string",
  "summary": {
    "total_strategies": 0,
    "valid_strategies": 0
  },
  "top_10": [
    {
      "rank": 1,
      "strategy_name": "string",
      "score": 0.0,
      "total_test_net_profit": 0.0,
      "pass_rate": 0.0,
      "max_test_mdd": 0.0,
      "average_test_pf": 0.0
    }
  ],
  "all_results": [
    {
      "rank": 1,
      "strategy_name": "string",
      "score": 0.0,
      "total_test_net_profit": 0.0,
      "pass_rate": 0.0,
      "max_test_mdd": 0.0,
      "average_test_pf": 0.0
    }
  ]
}
```

## Root Fields

- `run_id`: string
- `generated_at`: string
- `summary`: object
- `top_10`: array
- `all_results`: array

## Summary Fields

- `total_strategies`: int
- `valid_strategies`: int

## Ranking Item Fields

- `rank`: int
- `strategy_name`: string
- `score`: float
- `total_test_net_profit`: float
- `pass_rate`: float
- `max_test_mdd`: float
- `average_test_pf`: float
