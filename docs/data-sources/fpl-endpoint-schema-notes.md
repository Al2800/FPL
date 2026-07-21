# FPL endpoint schema notes

Observed at: `2026-07-21T16:05:26Z`
URL: `https://fantasy.premierleague.com/api/bootstrap-static/`
HTTP status: `200`

## Top-level keys
- `chips`: list[8]
- `element_stats`: list[26]
- `element_types`: list[4]
- `elements`: list[841]
- `events`: list[38]
- `game_config`: object keys=['rules', 'scoring', 'settings']
- `game_settings`: object keys=['cup_qualifying_method', 'cup_start_event_id', 'cup_stop_event_id', 'cup_type', 'element_sell_at_purchase_price', 'featured_entries', 'league_h2h_tiebreak_stats', 'league_join_private_max', 'league_join_public_max', 'league_ko_first_instead_of_random', 'league_max_ko_rounds_private_h2h', 'league_max_size_private_h2h', 'league_max_size_public_classic', 'league_max_size_public_h2h', 'league_points_h2h_draw', 'league_points_h2h_lose', 'league_points_h2h_win', 'league_prefix_public', 'max_extra_free_transfers', 'percentile_ranks']
- `phases`: list[11]
- `teams`: list[20]
- `total_players`: int

## Decision-relevant element fields present on sample player
- `chance_of_playing_next_round`
- `chance_of_playing_this_round`
- `clearances_blocks_interceptions`
- `cost_change_event`
- `cost_change_event_fall`
- `cost_change_start`
- `cost_change_start_fall`
- `defensive_contribution`
- `defensive_contribution_per_90`
- `ep_next`
- `ep_this`
- `news`
- `news_added`
- `now_cost_rank`
- `now_cost_rank_type`
- `recoveries`
- `scout_news_link`
- `selected_by_percent`
- `selected_rank`
- `selected_rank_type`
- `status`
- `tackles`
- `transfers_in`
- `transfers_in_event`
- `transfers_out`
- `transfers_out_event`
