from __future__ import annotations
import json
from copy import deepcopy
from pathlib import Path
import pytest, yaml
from src.ingestion.lineups_minutes import LineupsMinutesError, artifact_hash, reconcile_lineups_minutes, write_immutable_json

ROOT=Path(__file__).parents[2]
CONFIG=json.loads((ROOT/'config/data_sources/2026-27-lineups-minutes.json').read_text())
ALIASES={"aliases":[{"entity_type":"fixture","provider_id":"api-football","provider_entity_id":"fx1","fpl_entity_id":"fixture:1"},{"entity_type":"player","provider_id":"api-football","provider_entity_id":"p1","fpl_entity_id":"101"}]}
SNAPSHOT={"provider_id":"api-football","provider_fixture_id":"fx1","observed_at":"2026-08-20T10:00:00Z","players":[{"provider_player_id":"p1","started":True,"minutes":90}]}

def test_reconciles_explicit_aliases_and_seals_artifact():
    result=reconcile_lineups_minutes(SNAPSHOT,fpl_minutes={"fixture:1":{"101":90}},aliases=ALIASES,config=CONFIG,cutoff="2026-08-20T12:00:00Z")
    assert result["status"]=="complete" and result["players"][0]["status"]=="admitted"
    assert result["content_sha256"]==artifact_hash(result)

def test_disagreement_unmapped_and_after_cutoff_do_not_admit():
    changed=deepcopy(SNAPSHOT); changed["players"][0]["minutes"]=89
    result=reconcile_lineups_minutes(changed,fpl_minutes={"fixture:1":{"101":90}},aliases=ALIASES,config=CONFIG,cutoff="2026-08-20T12:00:00Z")
    assert result["players"][0]["status"]=="quarantined"
    changed["observed_at"]="2026-08-20T13:00:00Z"
    with pytest.raises(LineupsMinutesError,match="after cutoff"): reconcile_lineups_minutes(changed,fpl_minutes={"fixture:1":{"101":90}},aliases=ALIASES,config=CONFIG,cutoff="2026-08-20T12:00:00Z")
    changed=deepcopy(SNAPSHOT); changed["players"][0]["provider_player_id"]="unknown"
    assert "unmapped_provider_player:unknown" in reconcile_lineups_minutes(changed,fpl_minutes={"fixture:1":{}},aliases=ALIASES,config=CONFIG,cutoff="2026-08-20T12:00:00Z")["quality"]["gaps"]

def test_immutable_write(tmp_path):
    value=reconcile_lineups_minutes(SNAPSHOT,fpl_minutes={"fixture:1":{"101":90}},aliases=ALIASES,config=CONFIG,cutoff="2026-08-20T12:00:00Z")
    target=tmp_path/'a.json'; assert write_immutable_json(target,value)=="created"; assert write_immutable_json(target,value)=="identical"
    value["status"]="x"
    with pytest.raises(FileExistsError): write_immutable_json(target,value)
